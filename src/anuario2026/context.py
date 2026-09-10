from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import FigureDefinition
from .reports import RunReports
from .sources import SourceCatalog, verify_raw_file
from .text_engine import TextEngine


class FigureContext:
    def __init__(
        self,
        project_root: Path,
        figure: FigureDefinition,
        reports: RunReports,
        sources: SourceCatalog,
        manual_files: list[Path],
    ):
        self.project_root = project_root
        self.figure = figure
        self.reports = reports
        self.sources = sources
        self.manual_files = tuple(manual_files)
        self.expected_figure_path = figure.output_path
        self.expected_slide_path = (
            project_root / "build" / "slides" / f"{figure.figure_id.lower().replace('.', '_')}.png"
        )
        self.text_engine = TextEngine(project_root / "templates" / "text")

    def acquire_source(self, source_id: str) -> Path:
        path, metadata = self.sources.acquire(source_id)
        self.reports.add_reference(
            {
                "figure_id": self.figure.figure_id,
                "source_id": source_id,
                "owner": metadata.get("owner", ""),
                "title": metadata.get("title", ""),
                "expected_period": metadata.get("expected_period", ""),
                "detected_period": metadata.get("detected_period", ""),
                "period_assessment": metadata.get("period_assessment", ""),
                "landing_page": metadata.get("landing_page", ""),
                "exact_url": metadata.get("exact_url", ""),
                "local_path": str(path.relative_to(self.project_root)),
                "sha256": metadata.get("sha256", ""),
                "bytes": metadata.get("bytes", ""),
                "downloaded_at": metadata.get("downloaded_at", ""),
                "source_last_modified": metadata.get("source_last_modified", ""),
                "content_type": metadata.get("content_type", ""),
                "cache_status": metadata.get("cache_status", ""),
                "verification_status": metadata.get("status", ""),
            }
        )
        self.reports.add_artifact(self.figure.figure_id, "dato_crudo", path)
        return path

    def record_source_period(
        self,
        source_id: str,
        detected_period: str,
        period_assessment: str = "AL_DIA",
    ) -> None:
        self.reports.update_reference(
            self.figure.figure_id,
            source_id,
            detected_period=detected_period,
            period_assessment=period_assessment,
        )

    def register_raw_source(
        self,
        source_id: str,
        path: Path,
        *,
        owner: str,
        title: str,
        expected_period: str,
        detected_period: str,
        landing_page: str,
        exact_url: str,
        cache_status: str,
        downloaded_at: str = "",
        source_last_modified: str = "",
        content_type: str = "",
    ) -> None:
        """Registra un crudo adquirido por un descargador especializado."""
        verification = verify_raw_file(path)
        try:
            local_path = str(path.relative_to(self.project_root))
        except ValueError:
            local_path = str(path)
        self.reports.add_reference(
            {
                "figure_id": self.figure.figure_id,
                "source_id": source_id,
                "owner": owner,
                "title": title,
                "expected_period": expected_period,
                "detected_period": detected_period,
                "period_assessment": "AL_DIA",
                "landing_page": landing_page,
                "exact_url": exact_url,
                "local_path": local_path,
                "sha256": verification["sha256"],
                "bytes": verification["bytes"],
                "downloaded_at": downloaded_at,
                "source_last_modified": source_last_modified,
                "content_type": content_type,
                "cache_status": cache_status,
                "verification_status": verification["status"],
            }
        )
        self.reports.add_artifact(self.figure.figure_id, "dato_crudo", path)

    def verified_manual_files(self) -> tuple[Path, ...]:
        configured_sources = {
            self.sources.sources[source_id].get("filename", ""): (
                source_id,
                self.sources.sources[source_id],
            )
            for source_id in self.figure.source_ids
            if source_id in self.sources.sources
        }
        for path in self.manual_files:
            verification = verify_raw_file(path)
            source_id, source = configured_sources.get(path.name, ("manual", {}))
            self.reports.add_reference(
                {
                    "figure_id": self.figure.figure_id,
                    "source_id": source_id,
                    "owner": source.get("owner", ""),
                    "title": source.get("title", path.name),
                    "expected_period": source.get("expected_period", ""),
                    "detected_period": source.get("detected_period", ""),
                    "period_assessment": "POR_VALIDAR_EN_SCRIPT",
                    "landing_page": source.get("landing_page", ""),
                    "exact_url": source.get("exact_url", ""),
                    "local_path": str(path.relative_to(self.project_root)),
                    "sha256": verification["sha256"],
                    "bytes": verification["bytes"],
                    "downloaded_at": datetime.fromtimestamp(
                        path.stat().st_mtime, tz=timezone.utc
                    ).isoformat(timespec="seconds"),
                    "cache_status": "INSUMO_MANUAL_VERIFICADO",
                    "verification_status": verification["status"],
                }
            )
            self.reports.add_artifact(self.figure.figure_id, "dato_crudo_manual", path)
        return self.manual_files

    def record_calculation(
        self,
        calculation_id: str,
        formula: str,
        inputs: Any,
        result: Any,
        unit: str = "",
        decimals: int | None = None,
    ) -> None:
        self.reports.add_calculation(
            {
                "figure_id": self.figure.figure_id,
                "calculation_id": calculation_id,
                "formula": formula,
                "inputs_json": json.dumps(inputs, ensure_ascii=False, default=str),
                "result": result,
                "unit": unit,
                "decimals": "" if decimals is None else decimals,
            }
        )

    def write_data_used(self, rows: Any, name: str = "datos_usados") -> Path:
        slug = self.figure.figure_id.lower().replace(".", "_")
        path = self.reports.run_dir / "datos_usados" / f"{slug}_{name}.csv"
        if hasattr(rows, "to_csv"):
            rows.to_csv(path, index=False, encoding="utf-8-sig")
        else:
            records = list(rows)
            if records and isinstance(records[0], dict):
                with path.open("w", encoding="utf-8-sig", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(records[0].keys()))
                    writer.writeheader()
                    writer.writerows(records)
            else:
                with path.open("w", encoding="utf-8-sig", newline="") as stream:
                    writer = csv.writer(stream)
                    writer.writerows(records)
        print(f"\nDatos usados en {self.figure.figure_id}:")
        print(path.read_text(encoding="utf-8-sig").rstrip())
        self.reports.add_artifact(self.figure.figure_id, "datos_usados", path)
        return path

    def render_text(
        self,
        template_name: str,
        variables: dict[str, Any],
        output_name: str = "parrafo.md",
    ) -> Path:
        slug = self.figure.figure_id.lower().replace(".", "_")
        content = self.text_engine.render(template_name, variables)
        build_path = self.project_root / "build" / "text" / f"{slug}.md"
        audit_path = self.reports.run_dir / "textos" / f"{slug}_{output_name}"
        build_path.parent.mkdir(parents=True, exist_ok=True)
        build_path.write_text(content, encoding="utf-8")
        audit_path.write_text(content, encoding="utf-8")
        self.reports.add_artifact(self.figure.figure_id, "texto_generado", build_path)
        self.reports.add_artifact(self.figure.figure_id, "texto_copia_corrida", audit_path)
        return build_path
