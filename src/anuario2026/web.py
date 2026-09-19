from __future__ import annotations

import asyncio
import json
import threading
import time
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from .exports import ExportUnavailable, create_figure_compendium, ensure_pdf, ensure_pptx
from .pipeline import make_run_id, preflight_status, run_pipeline
from .registry import load_figures, load_project_config


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class RunJob:
    run_id: str
    figure_ids: list[str]
    status: str = "queued"
    started_at: str = field(default_factory=_utc_now)
    finished_at: str | None = None
    total: int = 0
    completed: int = 0
    current_figure: str | None = None
    current_title: str | None = None
    counts: dict[str, int] = field(default_factory=dict)
    figure_statuses: dict[str, dict[str, Any]] = field(default_factory=dict)
    error: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    next_event_id: int = 1

    def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        payload = dict(event)
        payload["event_id"] = self.next_event_id
        payload["timestamp"] = _utc_now()
        self.next_event_id += 1
        self.events.append(payload)
        return payload

    def snapshot(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "total": self.total,
            "completed": self.completed,
            "progress": round(self.completed / self.total * 100, 1) if self.total else 0,
            "current_figure": self.current_figure,
            "current_title": self.current_title,
            "counts": self.counts,
            "figure_statuses": self.figure_statuses,
            "error": self.error,
        }


class RunRequest(BaseModel):
    mode: str = Field(default="all", pattern="^(all|selection|single)$")
    figure_ids: list[str] = Field(default_factory=list)
    stop_on_error: bool = False


class RunManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.lock = threading.RLock()
        self.jobs: dict[str, RunJob] = {}
        self.active_run_id: str | None = None

    def _catalog(self):
        config = load_project_config(self.project_root)
        return load_figures(self.project_root, config)

    def available_ids(self) -> list[str]:
        return [
            figure.figure_id
            for figure in self._catalog()
            if preflight_status(self.project_root, figure)[0] == "LISTA"
        ]

    def start(self, request: RunRequest) -> RunJob:
        catalog = self._catalog()
        known = {figure.figure_id for figure in catalog}
        if request.mode == "all":
            selected = self.available_ids()
        else:
            selected = list(dict.fromkeys(request.figure_ids))
            unknown = [figure_id for figure_id in selected if figure_id not in known]
            if unknown:
                raise ValueError(f"Figuras desconocidas: {', '.join(unknown)}")
            if request.mode == "single" and len(selected) != 1:
                raise ValueError("El modo single requiere exactamente una figura.")
        if not selected:
            raise ValueError("No hay figuras seleccionadas para ejecutar.")

        with self.lock:
            if self.active_run_id:
                active = self.jobs.get(self.active_run_id)
                if active and active.status in {"queued", "running"}:
                    raise RuntimeError(f"Ya existe una corrida activa: {self.active_run_id}")
            run_id = make_run_id(False)
            job = RunJob(run_id=run_id, figure_ids=selected, total=len(selected))
            job.append_event({"type": "queued", "run_id": run_id, "total": len(selected)})
            self.jobs[run_id] = job
            self.active_run_id = run_id

        thread = threading.Thread(
            target=self._worker,
            args=(job, request.stop_on_error),
            name=f"anuario-{run_id}",
            daemon=True,
        )
        thread.start()
        return job

    def _handle_pipeline_event(self, job: RunJob, event: dict[str, Any]) -> None:
        with self.lock:
            event_type = event.get("type")
            if event_type == "run_started":
                job.status = "running"
                job.total = int(event.get("total") or job.total)
            elif event_type == "figure_started":
                job.status = "running"
                job.current_figure = str(event.get("figure_id") or "") or None
                job.current_title = str(event.get("title") or "") or None
            elif event_type == "figure_finished":
                figure_id = str(event.get("figure_id") or "")
                if figure_id:
                    job.figure_statuses[figure_id] = {
                        "status": event.get("status"),
                        "message": event.get("message"),
                        "duration_seconds": event.get("duration_seconds"),
                        "output_path": event.get("output_path"),
                        "position": event.get("position"),
                    }
                job.completed = len(job.figure_statuses)
            elif event_type == "run_finished":
                job.counts = dict(event.get("counts") or {})
                job.current_figure = None
                job.current_title = None
            job.append_event(event)

    def _worker(self, job: RunJob, stop_on_error: bool) -> None:
        try:
            run_pipeline(
                self.project_root,
                figure_ids=job.figure_ids,
                stop_on_error=stop_on_error,
                assemble=False,
                run_id=job.run_id,
                progress_callback=lambda event: self._handle_pipeline_event(job, event),
            )
            with self.lock:
                job.status = "finished"
                job.finished_at = _utc_now()
                job.current_figure = None
                job.current_title = None
                job.append_event(
                    {
                        "type": "ui_complete",
                        "run_id": job.run_id,
                        "counts": job.counts,
                        "completed": job.completed,
                        "total": job.total,
                    }
                )
        except Exception as exc:  # noqa: BLE001 - el error debe verse en la UI
            with self.lock:
                job.status = "error"
                job.error = f"{type(exc).__name__}: {exc}"
                job.finished_at = _utc_now()
                job.append_event({"type": "ui_error", "run_id": job.run_id, "error": job.error})
        finally:
            with self.lock:
                if self.active_run_id == job.run_id:
                    self.active_run_id = None

    def get(self, run_id: str) -> RunJob:
        with self.lock:
            job = self.jobs.get(run_id)
            if job:
                return job
        # Permite reabrir una corrida terminada de una sesión anterior del servidor.
        run_dir = self.project_root / "reportes" / run_id
        summary_path = run_dir / "resumen_ejecucion.json"
        if not summary_path.is_file():
            raise KeyError(run_id)
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        statuses = payload.get("statuses") or []
        job = RunJob(
            run_id=run_id,
            figure_ids=[item.get("figure_id") for item in statuses if item.get("figure_id")],
            status="finished",
            started_at=payload.get("started_at") or _utc_now(),
            finished_at=payload.get("finished_at"),
            total=len(statuses),
            completed=len(statuses),
        )
        for item in statuses:
            figure_id = item.get("figure_id")
            if not figure_id:
                continue
            job.figure_statuses[figure_id] = {
                "status": item.get("status"),
                "message": item.get("message"),
                "duration_seconds": item.get("duration_seconds"),
                "output_path": item.get("output_path"),
                "position": item.get("order"),
            }
            state = str(item.get("status") or "")
            job.counts[state] = job.counts.get(state, 0) + 1
        with self.lock:
            self.jobs[run_id] = job
        return job


def create_app(project_root: Path) -> FastAPI:
    project_root = project_root.resolve()
    manager = RunManager(project_root)
    app = FastAPI(title="Anuario Estadístico 2026", version="0.27.0")
    app.state.project_root = project_root
    app.state.run_manager = manager

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "project_root": str(project_root), "version": "0.27.0"}

    @app.get("/api/figures")
    def figures() -> dict[str, Any]:
        config = load_project_config(project_root)
        catalog = load_figures(project_root, config)
        payload = []
        for figure in catalog:
            state, message, _ = preflight_status(project_root, figure)
            payload.append(
                {
                    "id": figure.figure_id,
                    "section": figure.section,
                    "title": figure.title,
                    "order": figure.order,
                    "reference_page": figure.reference_page,
                    "status": state,
                    "status_message": message,
                    "available": state == "LISTA",
                    "has_preview": figure.output_path.is_file(),
                    "preview_url": f"/api/figures/{figure.figure_id}/preview",
                }
            )
        return {
            "project": config.get("project_name", "Anuario Estadístico 2026"),
            "version": config.get("version"),
            "figures": payload,
            "available_count": sum(1 for item in payload if item["available"]),
            "total_count": len(payload),
        }

    @app.get("/api/figures/{figure_id}/preview")
    def preview(figure_id: str) -> FileResponse:
        config = load_project_config(project_root)
        catalog = load_figures(project_root, config)
        match = next((figure for figure in catalog if figure.figure_id == figure_id), None)
        if match is None:
            raise HTTPException(status_code=404, detail="Figura desconocida")
        if not match.output_path.is_file():
            raise HTTPException(status_code=404, detail="La figura todavía no tiene una imagen generada")
        return FileResponse(
            match.output_path,
            media_type="image/png",
            headers={"Cache-Control": "no-store, max-age=0"},
        )

    @app.post("/api/runs")
    def start_run(payload: RunRequest) -> JSONResponse:
        try:
            job = manager.start(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return JSONResponse(job.snapshot(), status_code=202)

    @app.get("/api/runs/{run_id}")
    def run_status(run_id: str) -> dict[str, Any]:
        try:
            job = manager.get(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Corrida desconocida") from exc
        with manager.lock:
            return job.snapshot()

    @app.get("/api/runs/{run_id}/events")
    async def run_events(run_id: str, request: Request) -> StreamingResponse:
        try:
            job = manager.get(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Corrida desconocida") from exc

        last_event_header = request.headers.get("last-event-id", "0")
        try:
            cursor = int(last_event_header)
        except ValueError:
            cursor = 0

        async def stream():
            nonlocal cursor
            last_heartbeat = time.monotonic()
            while True:
                if await request.is_disconnected():
                    break
                pending: list[dict[str, Any]] = []
                terminal = False
                with manager.lock:
                    pending = [event for event in job.events if int(event["event_id"]) > cursor]
                    terminal = job.status in {"finished", "error"}
                for event in pending:
                    cursor = int(event["event_id"])
                    data = json.dumps(event, ensure_ascii=False, default=str)
                    yield f"id: {cursor}\ndata: {data}\n\n"
                if terminal and not pending:
                    break
                if time.monotonic() - last_heartbeat > 10:
                    yield ": keep-alive\n\n"
                    last_heartbeat = time.monotonic()
                await asyncio.sleep(0.25)

        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.get("/api/exports/{run_id}/{kind}")
    async def export(run_id: str, kind: str):
        kind = kind.lower()
        try:
            manager.get(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Corrida desconocida") from exc

        try:
            if kind == "pptx":
                path = await run_in_threadpool(ensure_pptx, project_root, run_id)
                media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            elif kind == "pdf":
                path = await run_in_threadpool(ensure_pdf, project_root, run_id)
                media_type = "application/pdf"
            elif kind in {"png", "jpg", "svg"}:
                path = await run_in_threadpool(create_figure_compendium, project_root, run_id, kind)
                media_type = "application/zip"
            else:
                raise HTTPException(status_code=404, detail="Formato de exportación desconocido")
        except ExportUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001 - mostrar error de exportación sin tumbar el servidor
            raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}") from exc

        return FileResponse(path, media_type=media_type, filename=path.name)

    frontend_dist = project_root / "web" / "dist"
    if frontend_dist.is_dir():
        assets_dir = frontend_dist / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/")
        def index() -> FileResponse:
            return FileResponse(frontend_dist / "index.html")

        @app.get("/{path:path}")
        def spa(path: str):
            # Las rutas /api ya fueron resueltas arriba. El resto pertenece a React.
            candidate = frontend_dist / path
            if candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(frontend_dist / "index.html")
    else:
        @app.get("/")
        def missing_frontend() -> JSONResponse:
            return JSONResponse(
                {
                    "message": "El frontend React no está compilado.",
                    "build": "cd web && npm install && npm run build",
                },
                status_code=503,
            )

    return app


def serve(project_root: Path, host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    import uvicorn

    app = create_app(project_root)
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    uvicorn.run(app, host=host, port=port, log_level="info")
