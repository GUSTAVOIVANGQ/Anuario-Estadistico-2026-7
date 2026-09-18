from __future__ import annotations

import importlib.util
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

from .context import FigureContext
from .models import FigureDefinition, FigureStatus
from .presentation import assemble_from_template
from .registry import load_figures, load_project_config
from .reports import RunReports, utc_now
from .sources import SourceCatalog
from .ui_2024 import install_source_credit_normalizer


LOGGER = logging.getLogger("anuario2026")


def make_run_id(dry_run: bool) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{stamp}_{'simulacion' if dry_run else 'corrida'}"


def configure_logging(log_path: Path) -> None:
    LOGGER.setLevel(logging.INFO)
    LOGGER.handlers.clear()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(file_handler)
    LOGGER.addHandler(stream_handler)


def select_figures(
    figures: list[FigureDefinition],
    only: str | None,
    start_from: str | None,
    until: str | None,
) -> list[FigureDefinition]:
    if only:
        selected = [item for item in figures if item.figure_id == only]
        if not selected:
            raise ValueError(f"Figura desconocida: {only}")
        return selected
    start_index = 0
    end_index = len(figures)
    ids = [item.figure_id for item in figures]
    if start_from:
        if start_from not in ids:
            raise ValueError(f"Figura desconocida: {start_from}")
        start_index = ids.index(start_from)
    if until:
        if until not in ids:
            raise ValueError(f"Figura desconocida: {until}")
        end_index = ids.index(until) + 1
    return figures[start_index:end_index]


def manual_files(project_root: Path, figure: FigureDefinition) -> list[Path]:
    if not figure.manual_input:
        return []
    directory = project_root / figure.manual_input["directory"]
    files: list[Path] = []
    for pattern in figure.manual_input.get("patterns", ["*"]):
        files.extend(path for path in directory.glob(pattern) if path.is_file())
    return sorted(set(files))


def validate_png(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"La figura no generó el archivo esperado: {path}")
    with Image.open(path) as image:
        image.verify()


def load_generator(figure: FigureDefinition):
    module_name = "anuario_figure_" + figure.figure_id.lower().replace(".", "_")
    spec = importlib.util.spec_from_file_location(module_name, figure.script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar {figure.script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    declared = getattr(module, "FIGURE_ID", figure.figure_id)
    if declared != figure.figure_id:
        raise ValueError(
            f"El script declara FIGURE_ID={declared!r}; se esperaba {figure.figure_id!r}"
        )
    generate = getattr(module, "generate", None)
    if not callable(generate):
        raise TypeError("El script debe exponer generate(context)")
    return generate


def preflight_status(
    project_root: Path,
    figure: FigureDefinition,
) -> tuple[str, str, list[Path]]:
    files = manual_files(project_root, figure)
    if not figure.script_path.is_file():
        return "PENDIENTE_CODIGO", "Falta actualizar el script de la figura.", files
    if figure.manual_input and not files:
        directory = project_root / figure.manual_input["directory"]
        return (
            "BLOQUEADA_INSUMO_MANUAL",
            f"Coloca los archivos crudos en {directory}",
            files,
        )
    if figure.downloader and figure.downloader.get("status") != "ready":
        return (
            "BLOQUEADA_DESCARGADOR",
            figure.downloader.get("instruction", "Falta integrar el descargador."),
            files,
        )
    return "LISTA", "Código e insumos disponibles.", files


def show_manual_instructions(project_root: Path, figures: list[FigureDefinition]) -> None:
    manual = [item for item in figures if item.manual_input]
    if not manual:
        return
    LOGGER.info("INSUMOS DE DESCARGA MANUAL")
    for figure in manual:
        directory = project_root / figure.manual_input["directory"]
        found = manual_files(project_root, figure)
        state = f"{len(found)} archivo(s)" if found else "FALTA"
        LOGGER.info("  %s | %s | %s", figure.figure_id, state, directory)
        LOGGER.info("      %s", figure.manual_input["instruction"])
    LOGGER.info("")


def run_pipeline(
    project_root: Path,
    *,
    dry_run: bool = False,
    only: str | None = None,
    start_from: str | None = None,
    until: str | None = None,
    stop_on_error: bool = False,
    assemble: bool = False,
) -> Path:
    install_source_credit_normalizer()
    config = load_project_config(project_root)
    all_figures = load_figures(project_root, config)
    figures = select_figures(all_figures, only, start_from, until)
    run_id = make_run_id(dry_run)
    reports = RunReports(project_root, run_id, dry_run)
    configure_logging(reports.run_dir / "pipeline.log")
    sources = SourceCatalog(project_root)
    reports.write_source_matrix(all_figures, sources.sources)
    show_manual_instructions(project_root, all_figures)

    LOGGER.info("Anuario Estadístico 2026 | corrida %s", run_id)
    LOGGER.info("Figuras seleccionadas: %d de %d", len(figures), len(all_figures))
    LOGGER.info("")

    for position, figure in enumerate(figures, start=1):
        started = time.perf_counter()
        started_at = utc_now()
        status, message, files = preflight_status(project_root, figure)
        LOGGER.info("[%03d/%03d] %s | %s", position, len(figures), figure.figure_id, status)
        if dry_run or status != "LISTA":
            result = FigureStatus(
                order=figure.order,
                figure_id=figure.figure_id,
                status=status,
                message=message,
                script_path=str(figure.script_path.relative_to(project_root)),
                output_path=str(figure.output_path.relative_to(project_root)),
                started_at=started_at,
                finished_at=utc_now(),
                duration_seconds=round(time.perf_counter() - started, 3),
            )
            reports.add_status(result)
            if status.startswith("BLOQUEADA"):
                LOGGER.info("  %s", message)
            if stop_on_error and status not in {"PENDIENTE_CODIGO", "LISTA"}:
                break
            continue

        try:
            context = FigureContext(project_root, figure, reports, sources, files)
            if files:
                context.verified_manual_files()
            generate = load_generator(figure)
            payload: dict[str, Any] = generate(context) or {}
            output = Path(payload.get("figure_path", figure.output_path))
            if not output.is_absolute():
                output = project_root / output
            validate_png(output)
            reports.add_artifact(figure.figure_id, "grafica", output)
            slide_value = payload.get("slide_path")
            if slide_value:
                slide_path = Path(slide_value)
                if not slide_path.is_absolute():
                    slide_path = project_root / slide_path
                validate_png(slide_path)
                reports.add_artifact(figure.figure_id, "pagina_completa", slide_path)
            metadata_path = (
                project_root
                / config["paths"]["metadata"]
                / f"{figure.figure_id.lower().replace('.', '_')}.json"
            )
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(
                json.dumps(
                    {
                        "figure_id": figure.figure_id,
                        "title": figure.title,
                        "reference_page_2024": figure.reference_page,
                        "figure_path": str(output.relative_to(project_root)),
                        "run_id": run_id,
                        "result": payload,
                    },
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
                + "\n",
                encoding="utf-8",
            )
            reports.add_artifact(figure.figure_id, "metadatos", metadata_path)
            status = "OK"
            message = "Gráfica generada y verificada."
        except Exception as exc:  # noqa: BLE001 - cada figura debe quedar aislada
            LOGGER.exception("  Falló %s", figure.figure_id)
            status = "ERROR"
            message = f"{type(exc).__name__}: {exc}"

        reports.add_status(
            FigureStatus(
                order=figure.order,
                figure_id=figure.figure_id,
                status=status,
                message=message,
                script_path=str(figure.script_path.relative_to(project_root)),
                output_path=str(figure.output_path.relative_to(project_root)),
                started_at=started_at,
                finished_at=utc_now(),
                duration_seconds=round(time.perf_counter() - started, 3),
            )
        )
        if status == "ERROR" and stop_on_error:
            break

    reports.finalize()
    LOGGER.info("")
    LOGGER.info("Reporte de corrida: %s", reports.run_dir)
    if assemble and not dry_run:
        assemble_pptx(project_root, reports.run_dir)
    return reports.run_dir


def assemble_pptx(
    project_root: Path,
    run_dir: Path | None = None,
    *,
    output: Path | None = None,
    strict: bool = False,
) -> Path:
    suffix = run_dir.name if run_dir else "base"
    output_path = output or (
        project_root / "entrega" / f"anuario_estadistico_2026_{suffix}.pptx"
    )
    result = assemble_from_template(
        project_root,
        output_path,
        strict=strict,
        run_dir=run_dir,
    )
    LOGGER.info("PPTX ensamblado: %s", result.output_path)
    LOGGER.info(
        "Figuras insertadas: %d | faltantes: %d | errores: %d",
        result.inserted,
        len(result.missing),
        len(result.errors),
    )
    if result.missing:
        LOGGER.info("Marcadores conservados para figuras faltantes: %s", ", ".join(result.missing))
    if result.errors:
        for error in result.errors:
            LOGGER.warning("Ensamblaje: %s", error)
    LOGGER.info("Reporte de ensamblaje: %s", result.report_path)
    return result.output_path
