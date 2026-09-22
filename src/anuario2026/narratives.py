from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY = Path("assets/presentation/narrativas_figuras_2026.json")


@dataclass(frozen=True)
class NarrativeRecord:
    figure_id: str
    source_pdf_page: int
    baseline_text_2024: str
    updated_text: str
    update_mode: str
    notes: tuple[str, ...]
    data_file: str | None
    expected_data_sha256: str | None
    current_data_sha256: str | None
    verification_status: str


@dataclass(frozen=True)
class NarrativeAudit:
    records: dict[str, NarrativeRecord]
    registry_path: Path
    reference_run: str | None
    source_document: str | None

    @property
    def verified_count(self) -> int:
        return sum(r.verification_status == "verified" for r in self.records.values())

    @property
    def changed_data_count(self) -> int:
        return sum(r.verification_status == "data_changed" for r in self.records.values())

    @property
    def mode_counts(self) -> dict[str, int]:
        return dict(Counter(r.update_mode for r in self.records.values()))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def load_narrative_audit(
    project_root: Path,
    *,
    run_dir: Path | None,
    registry_path: Path | None = None,
) -> NarrativeAudit:
    """Load the reviewed 2024 prose and its record-only 2026 updates.

    The registry stores a SHA-256 of the exact ``datos_usados`` file used while
    reviewing each narrative.  This prevents a later data refresh from silently
    reusing stale prose.  Assembly can still proceed in non-strict mode, but the
    mismatch is explicit in the audit report.
    """

    registry = registry_path or (project_root / DEFAULT_REGISTRY)
    if not registry.is_file():
        raise FileNotFoundError(f"Falta el registro de narrativas: {registry}")
    payload = _load_json(registry)
    records: dict[str, NarrativeRecord] = {}

    for item in payload.get("entries", []):
        figure_id = str(item["figure_id"])
        data_file = item.get("data_file")
        expected = item.get("data_sha256")
        current: str | None = None
        status = "not_verified"

        if run_dir is not None and data_file:
            candidate = run_dir / "datos_usados" / Path(str(data_file)).name
            if candidate.is_file():
                current = _sha256(candidate)
                status = "verified" if not expected or current == expected else "data_changed"
            else:
                status = "data_missing"

        records[figure_id] = NarrativeRecord(
            figure_id=figure_id,
            source_pdf_page=int(item["source_pdf_page"]),
            baseline_text_2024=str(item["baseline_text_2024"]).strip(),
            updated_text=str(item["updated_text"]).strip(),
            update_mode=str(item.get("update_mode") or "records_only"),
            notes=tuple(str(x) for x in item.get("notes", [])),
            data_file=str(data_file) if data_file else None,
            expected_data_sha256=str(expected) if expected else None,
            current_data_sha256=current,
            verification_status=status,
        )

    return NarrativeAudit(
        records=records,
        registry_path=registry,
        reference_run=payload.get("reference_run"),
        source_document=payload.get("source_document"),
    )


def write_narrative_reports(
    audit: NarrativeAudit,
    *,
    json_path: Path,
    csv_path: Path,
    inserted_figure_ids: set[str],
) -> None:
    rows: list[dict[str, Any]] = []
    for figure_id, record in audit.records.items():
        rows.append(
            {
                "figure_id": figure_id,
                "inserted_in_pptx": figure_id in inserted_figure_ids,
                "source_pdf_page": record.source_pdf_page,
                "update_mode": record.update_mode,
                "verification_status": record.verification_status,
                "data_file": record.data_file,
                "expected_data_sha256": record.expected_data_sha256,
                "current_data_sha256": record.current_data_sha256,
                "baseline_text_2024": record.baseline_text_2024,
                "updated_text": record.updated_text,
                "notes": " | ".join(record.notes),
            }
        )

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_payload = {
        "source_document": audit.source_document,
        "registry": str(audit.registry_path),
        "reference_run": audit.reference_run,
        "registered_count": len(audit.records),
        "inserted_count": sum(bool(row["inserted_in_pptx"]) for row in rows),
        "verified_count": audit.verified_count,
        "data_changed_count": audit.changed_data_count,
        "update_mode_counts": audit.mode_counts,
        "rows": rows,
    }
    json_path.write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        fieldnames = [
            "figure_id",
            "inserted_in_pptx",
            "source_pdf_page",
            "update_mode",
            "verification_status",
            "data_file",
            "expected_data_sha256",
            "current_data_sha256",
            "baseline_text_2024",
            "updated_text",
            "notes",
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
