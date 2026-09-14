from __future__ import annotations

import ast
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def script(suffix: int) -> Path:
    return ROOT / "scripts" / "figures" / f"figura_f_1_{suffix}.py"


def test_cada_lamina_f1_es_un_script_autonomo_y_auditable():
    for suffix in range(1, 5):
        source = script(suffix).read_text(encoding="utf-8")
        tree = ast.parse(source)
        assert f'FIGURE_ID = "F.1.{suffix}"' in source
        assert "context.acquire_source" in source
        assert "context.write_data_used" in source
        assert "context.record_calculation" in source
        assert "context.render_text" in source
        assert "load_endutih" in source and "calculate" in source and "_plot" in source
        assert "_endutih_f1_common" not in source
        assert any(isinstance(node, ast.FunctionDef) and node.name == "generate" for node in tree.body)


def test_inventario_separa_las_cuatro_laminas_y_sus_salidas():
    with (ROOT / "inventario_indicadores.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = {row["id_indicador"]: row for row in csv.DictReader(stream)}
    for suffix in range(1, 5):
        row = rows[f"F.1.{suffix}"]
        assert row["implementacion"] == "actualizado"
        assert row["script"] == f"scripts/figures/figura_f_1_{suffix}.py"
        assert row["salida_esperada"] == f"build/figures/F/figura_f_1_{suffix}.png"


def test_periodos_y_tablas_endutih_son_explicitos():
    f11 = script(1).read_text(encoding="utf-8")
    f13 = script(3).read_text(encoding="utf-8")
    assert 'TABLE_TOKEN = "usuarios2_anual"' in f11
    assert 'PERIOD_CURRENT = "2025"' in f11
    assert 'CURRENT_SOURCE_ID = "inegi_endutih_2024_reference"' in f13
    assert 'LATEST_SOURCE_ID = "inegi_endutih_2025"' in f13


def test_pies_conservan_fuente_y_nota_sin_etiquetas_editoriales():
    for suffix in range(1, 5):
        source = script(suffix).read_text(encoding="utf-8")
        assert '"Fuente:"' in source
        assert '"Nota:"' in source
        assert "control editorial" not in source.lower()
        assert "revisión" not in source.lower()
