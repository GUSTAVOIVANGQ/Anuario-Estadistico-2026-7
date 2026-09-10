from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import FigureDefinition


def load_project_config(project_root: Path) -> dict[str, Any]:
    path = project_root / "config" / "proyecto.json"
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def figure_slug(figure_id: str) -> str:
    return figure_id.lower().replace(".", "_")


def reference_page(figure_id: str) -> int:
    section, *parts = figure_id.split(".")
    number = int(parts[0])
    if section == "A":
        return 10 + number
    if section == "B":
        return 20 + number
    if section == "C":
        if number in (3, 4):
            return 48
        return 45 + number
    if section == "D":
        return 60 + number
    if section == "E":
        return 71 + number
    if section == "F":
        if number == 1:
            return 81 + int(parts[1])
        return 84 + number
    if section == "G":
        return 100 + number
    if section == "H":
        return 101 + number
    raise ValueError(f"Sección desconocida: {figure_id}")


def _indicator_rows(project_root: Path) -> dict[str, dict[str, str]]:
    path = project_root / "inventario_indicadores.csv"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return {row["id_indicador"].strip(): row for row in csv.DictReader(stream)}


def _split_sources(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(";") if item.strip())


def load_figures(project_root: Path, config: dict[str, Any]) -> list[FigureDefinition]:
    known = _indicator_rows(project_root)
    paths = config["paths"]
    figures: list[FigureDefinition] = []
    order = 0

    for section, ids in config["figure_sections"].items():
        for figure_id in ids:
            order += 1
            row = known.get(figure_id, {})
            slug = figure_slug(figure_id)
            # La lógica nueva exige un archivo independiente por figura. El campo
            # script del inventario heredado se conserva como referencia, pero no
            # controla la ejecución.
            script_rel = f"scripts/figures/figura_{slug}.py"
            output_rel = row.get("salida_esperada") or (
                f"{paths['figures']}/{section}/figura_{slug}.png"
            )
            figures.append(
                FigureDefinition(
                    order=order,
                    figure_id=figure_id,
                    section=section,
                    title=row.get("nombre") or f"Figura {figure_id}",
                    reference_page=reference_page(figure_id),
                    script_path=project_root / Path(script_rel),
                    output_path=project_root / Path(output_rel),
                    source_ids=_split_sources(row.get("fuentes_requeridas", "")),
                    manual_input=config.get("manual_inputs", {}).get(figure_id),
                    downloader=config.get("downloaders", {}).get(figure_id),
                )
            )
    return figures
