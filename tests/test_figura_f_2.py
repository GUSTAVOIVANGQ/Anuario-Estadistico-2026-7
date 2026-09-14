from __future__ import annotations

import ast
import csv
import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "figures" / "figura_f_2.py"


def _module():
    spec = importlib.util.spec_from_file_location("figura_f_2", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_f2_es_script_autonomo_auditable():
    source = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert 'FIGURE_ID = "F.2"' in source
    assert "context.acquire_source" in source
    assert "context.write_data_used" in source
    assert "context.record_calculation" in source
    assert "context.render_text" in source
    assert any(isinstance(node, ast.FunctionDef) and node.name == "generate" for node in tree.body)


def test_f2_reconoce_resultado_publicado_2024():
    module = _module()
    frame = pd.DataFrame(
        [
            {"sector": "Radiodifusión", "total": 54_694, "mujeres_pct": 45.0, "hombres_pct": 55.0},
            {"sector": "Telecomunicaciones", "total": 247_172, "mujeres_pct": 32.0, "hombres_pct": 68.0},
        ]
    )
    assert module.reference_matches(frame)
    frame.loc[1, "total"] += 1
    assert not module.reference_matches(frame)


def test_f2_calcula_ponderaciones_por_scian_y_sexo():
    module = _module()
    frame = pd.DataFrame(
        {
            "clase1": [1, 1, 1, 1, 2],
            "clase2": [1, 1, 1, 1, 2],
            "fac_tri": [20, 30, 40, 10, 999],
            "sex": [2, 1, 2, 1, 2],
            "p4a": pd.Series(["5150", "5150", "5170", "5170", "5170"], dtype="string"),
        }
    )
    data, sample = module.calculate(frame, module._universe_legacy)
    rows = data.set_index("sector")
    assert sample == 4
    assert rows.loc["Radiodifusión", "total"] == 50
    assert rows.loc["Radiodifusión", "mujeres_pct"] == 40
    assert rows.loc["Telecomunicaciones", "total"] == 50
    assert rows.loc["Telecomunicaciones", "mujeres_pct"] == 80


def test_inventario_declara_f2_actualizada():
    with (ROOT / "inventario_indicadores.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = {row["id_indicador"]: row for row in csv.DictReader(stream)}
    row = rows["F.2"]
    assert row["implementacion"] == "actualizado"
    assert row["script"] == "scripts/figures/figura_f_2.py"
    assert row["fuentes_requeridas"] == "inegi_enoe_2026_q2"
    assert row["fuentes_referencia"] == "inegi_enoe_2024_q2_reference"
    assert row["salida_esperada"] == "build/figures/F/figura_f_2.png"


def test_f2_conserva_pie_editorial():
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"Fuente:"' in source
    assert "control editorial" not in source.lower()
    assert "revisión" not in source.lower()
