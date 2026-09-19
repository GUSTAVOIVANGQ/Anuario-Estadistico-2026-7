from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import FigureDefinition, FigureStatus, RunSummary


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class RunReports:
    status_fields = [
        "order",
        "figure_id",
        "status",
        "message",
        "script_path",
        "output_path",
        "started_at",
        "finished_at",
        "duration_seconds",
    ]
    reference_fields = [
        "figure_id",
        "source_id",
        "owner",
        "title",
        "expected_period",
        "detected_period",
        "period_assessment",
        "landing_page",
        "exact_url",
        "local_path",
        "sha256",
        "bytes",
        "downloaded_at",
        "source_last_modified",
        "content_type",
        "cache_status",
        "verification_status",
    ]
    calculation_fields = [
        "figure_id",
        "calculation_id",
        "formula",
        "inputs_json",
        "result",
        "unit",
        "decimals",
    ]
    artifact_fields = [
        "figure_id",
        "role",
        "path",
        "sha256",
        "bytes",
        "modified_at",
    ]
    figure_source_reference_fields = [
        "figura",
        "fuente_source_id",
        "fuente_propietario",
        "archivo_descarga_zip",
        "archivo_real_tabla",
        "portal_origen",
    ]

    def __init__(self, project_root: Path, run_id: str, dry_run: bool):
        self.project_root = project_root
        self.run_id = run_id
        self.run_dir = project_root / "reportes" / run_id
        self.run_dir.mkdir(parents=True, exist_ok=False)
        (self.run_dir / "datos_usados").mkdir()
        (self.run_dir / "textos").mkdir()
        self.summary = RunSummary(run_id=run_id, dry_run=dry_run, started_at=utc_now())
        self.references: list[dict[str, Any]] = []
        self.calculations: list[dict[str, Any]] = []
        self.artifacts: list[dict[str, Any]] = []
        self._write_csv("estado_figuras.csv", self.status_fields, [])
        self._write_csv("referencias_por_figura.csv", self.reference_fields, [])
        self._write_csv("calculos_por_figura.csv", self.calculation_fields, [])
        self._write_csv("manifiesto_archivos.csv", self.artifact_fields, [])

    def _write_csv(self, name: str, fields: list[str], rows: list[dict[str, Any]]) -> None:
        path = self.run_dir / name
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    def add_status(self, status: FigureStatus) -> None:
        self.summary.statuses.append(status)
        self._write_csv(
            "estado_figuras.csv",
            self.status_fields,
            [asdict(item) for item in self.summary.statuses],
        )

    def add_reference(self, row: dict[str, Any]) -> None:
        self.references.append(row)
        self._write_csv("referencias_por_figura.csv", self.reference_fields, self.references)

    def update_reference(
        self, figure_id: str, source_id: str, **updates: Any
    ) -> None:
        for row in reversed(self.references):
            if row.get("figure_id") == figure_id and row.get("source_id") == source_id:
                row.update(updates)
                self._write_csv(
                    "referencias_por_figura.csv", self.reference_fields, self.references
                )
                return
        raise KeyError(f"Referencia no registrada para {figure_id}: {source_id}")

    def add_calculation(self, row: dict[str, Any]) -> None:
        self.calculations.append(row)
        self._write_csv("calculos_por_figura.csv", self.calculation_fields, self.calculations)

    def add_artifact(self, figure_id: str, role: str, path: Path) -> None:
        relative = path.resolve().relative_to(self.project_root.resolve())
        stat = path.stat()
        self.artifacts.append(
            {
                "figure_id": figure_id,
                "role": role,
                "path": relative.as_posix(),
                "sha256": sha256_file(path),
                "bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(timespec="seconds"),
            }
        )
        self._write_csv("manifiesto_archivos.csv", self.artifact_fields, self.artifacts)

    def write_source_matrix(
        self,
        figures: list[FigureDefinition],
        sources: dict[str, dict[str, str]],
    ) -> None:
        fields = [
            "figure_id",
            "source_id",
            "owner",
            "title",
            "expected_period",
            "acquisition_mode",
            "landing_page",
            "exact_url",
            "configuration_status",
        ]
        rows: list[dict[str, str]] = []
        pending: list[dict[str, str]] = []
        for figure in figures:
            if not figure.source_ids:
                pending.append(
                    {
                        "figure_id": figure.figure_id,
                        "reason": "SIN_FUENTE_CONFIGURADA",
                        "detail": "Se definirá al actualizar la figura.",
                    }
                )
                continue
            for source_id in figure.source_ids:
                source = sources.get(source_id, {})
                status = "CONFIGURADA" if source else "SOURCE_ID_NO_REGISTRADO"
                row = {
                    "figure_id": figure.figure_id,
                    "source_id": source_id,
                    "owner": source.get("owner", ""),
                    "title": source.get("title", ""),
                    "expected_period": source.get("expected_period", ""),
                    "acquisition_mode": source.get("acquisition_mode", ""),
                    "landing_page": source.get("landing_page", ""),
                    "exact_url": source.get("exact_url", ""),
                    "configuration_status": status,
                }
                rows.append(row)
                if status != "CONFIGURADA":
                    pending.append(
                        {
                            "figure_id": figure.figure_id,
                            "reason": status,
                            "detail": source_id,
                        }
                    )
        self._write_csv("fuentes_configuradas.csv", fields, rows)
        self._write_csv(
            "fuentes_pendientes.csv",
            ["figure_id", "reason", "detail"],
            pending,
        )

    def write_figure_source_reference_report(self) -> Path:
        """Genera en cada corrida el catálogo figura-fuente solicitado para defensa."""
        source_path = self.project_root / "referencias_fuentes_figuras.csv"
        rows: list[dict[str, str]] = []
        if source_path.is_file():
            with source_path.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                missing = [
                    field
                    for field in self.figure_source_reference_fields
                    if field not in (reader.fieldnames or [])
                ]
                if missing:
                    raise ValueError(
                        "referencias_fuentes_figuras.csv no contiene las columnas requeridas: "
                        + ", ".join(missing)
                    )
                rows = [dict(row) for row in reader]
        self._write_csv(
            "referencias_fuentes_figuras.csv",
            self.figure_source_reference_fields,
            rows,
        )
        return self.run_dir / "referencias_fuentes_figuras.csv"

    def finalize(self) -> None:
        self.summary.finished_at = utc_now()
        payload = asdict(self.summary)
        with (self.run_dir / "resumen_ejecucion.json").open(
            "w", encoding="utf-8"
        ) as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")

        counts = Counter(status.status for status in self.summary.statuses)
        lines = [
            f"# Resumen de ejecución {self.run_id}",
            "",
            f"- Inicio UTC: {self.summary.started_at}",
            f"- Fin UTC: {self.summary.finished_at}",
            f"- Simulación: {'sí' if self.summary.dry_run else 'no'}",
            f"- Figuras inventariadas: {len(self.summary.statuses)}",
            "",
            "## Estados",
            "",
        ]
        lines.extend(f"- {key}: {value}" for key, value in sorted(counts.items()))
        lines.extend(
            [
                "",
                "## Archivos de defensa",
                "",
                "- `estado_figuras.csv`: resultado secuencial de cada figura.",
                "- `fuentes_configuradas.csv`: fuente prevista para cada figura.",
                "- `fuentes_pendientes.csv`: enlaces o fuentes aún por definir.",
                "- `referencias_por_figura.csv`: fuentes realmente usadas.",
                "- `referencias_fuentes_figuras.csv`: catálogo figura-fuente, archivo real y portal de origen.",
                "- `calculos_por_figura.csv`: fórmulas y resultados registrados.",
                "- `manifiesto_archivos.csv`: huellas SHA-256 de insumos y salidas.",
            ]
        )
        (self.run_dir / "resumen_ejecucion.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
