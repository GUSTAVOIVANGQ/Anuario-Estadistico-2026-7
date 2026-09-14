from __future__ import annotations

import ast
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _script(number: int) -> Path:
    return ROOT / "scripts" / "figures" / f"figura_f_{number}.py"


def test_cada_figura_tiene_script_autonomo_y_salida_propia():
    for number in range(10, 17):
        path = _script(number)
        assert path.is_file()
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        assert f'FIGURE_ID="F.{number}"' in source or f'FIGURE_ID = "F.{number}"' in source
        assert "context.acquire_source" in source
        assert "context.write_data_used" in source
        assert "context.record_calculation" in source
        assert "context.render_text" in source
        assert any(isinstance(node, ast.FunctionDef) and node.name == "generate" for node in tree.body)


def test_inventario_declara_fuente_compatible_y_salidas():
    with (ROOT / "inventario_indicadores.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = {row["id_indicador"]: row for row in csv.DictReader(stream)}
    for number in range(10, 17):
        row = rows[f"F.{number}"]
        assert row["implementacion"] == "actualizado"
        assert row["salida_esperada"] == f"build/figures/F/figura_f_{number}.png"
    assert rows["F.14"]["fuentes_requeridas"] == "ift_tercera_encuesta_usuarios_2023_pdf"
    for number in (10, 11, 12, 13, 15, 16):
        assert rows[f"F.{number}"]["fuentes_requeridas"] == "ift_tercera_encuesta_usuarios_2023_base"


def test_no_se_presentan_las_encuestas_2025_como_comparables():
    with (ROOT / "inventario_fuentes.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = {row["source_id"]: row for row in csv.DictReader(stream)}
    for source_id in ("ift_primera_encuesta_usuarios_2025", "ift_segunda_encuesta_usuarios_2025"):
        assert rows[source_id]["role"] == "reference"
        assert rows[source_id]["period_assessment"] == "NO_COMPARABLE"


def test_pies_editoriales_conservan_etiquetas_sin_control_extra():
    for number in range(10, 17):
        source = _script(number).read_text(encoding="utf-8")
        assert '"Fuente:"' in source
        assert '"Nota:"' in source
        assert "control editorial" not in source.lower()
        assert "revisión" not in source.lower()
