from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


def percent_variation(previous: float, current: float) -> float | None:
    previous = float(previous)
    current = float(current)
    if previous == 0:
        return None
    return (current / previous - 1.0) * 100.0


def extreme_record(
    records: Iterable[Mapping[str, Any]],
    value_key: str,
    label_key: str,
    mode: str,
) -> dict[str, Any] | None:
    valid = [row for row in records if row.get(value_key) is not None]
    if not valid:
        return None
    chooser = max if mode == "max" else min
    row = chooser(valid, key=lambda item: float(item[value_key]))
    return {"etiqueta": row[label_key], "valor": float(row[value_key])}


def format_number(value: Any, decimals: int = 1) -> str:
    if value is None:
        return ""
    return f"{float(value):,.{int(decimals)}f}"


def format_percentage(value: Any, decimals: int = 1) -> str:
    if value is None:
        return ""
    return f"{float(value):,.{int(decimals)}f}%"


class TextEngine:
    def __init__(self, templates_dir: Path):
        self.environment = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=False,
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.environment.filters["numero"] = format_number
        self.environment.filters["porcentaje"] = format_percentage
        self.environment.globals.update(
            variacion_pct=percent_variation,
            mayor=lambda rows, value="valor", label="entidad": extreme_record(
                rows, value, label, "max"
            ),
            menor=lambda rows, value="valor", label="entidad": extreme_record(
                rows, value, label, "min"
            ),
        )

    def render(self, template_name: str, variables: Mapping[str, Any]) -> str:
        return self.environment.get_template(template_name).render(**variables).strip() + "\n"

