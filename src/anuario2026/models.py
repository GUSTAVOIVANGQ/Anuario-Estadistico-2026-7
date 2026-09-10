from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FigureDefinition:
    order: int
    figure_id: str
    section: str
    title: str
    reference_page: int
    script_path: Path
    output_path: Path
    source_ids: tuple[str, ...] = ()
    manual_input: dict[str, Any] | None = None
    downloader: dict[str, Any] | None = None


@dataclass
class FigureStatus:
    order: int
    figure_id: str
    status: str
    message: str
    script_path: str
    output_path: str
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: float = 0.0


@dataclass
class RunSummary:
    run_id: str
    dry_run: bool
    started_at: str
    finished_at: str = ""
    statuses: list[FigureStatus] = field(default_factory=list)

