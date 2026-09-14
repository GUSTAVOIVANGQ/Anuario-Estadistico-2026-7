from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "figures" / "figura_b_21.py"
SPEC = importlib.util.spec_from_file_location("figura_b_21_test", SCRIPT)
assert SPEC and SPEC.loader
B21 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B21)


def test_b21_selects_latest_complete_period_and_aggregates_operators():
    bit_rows = []
    household_rows = []
    for entity in range(1, 33):
        bit_rows.extend([
            {"K_ENTIDAD": entity, "ANIO": 2023, "MES": 12, "A_RESIDENCIAL_E": 58},
            {"K_ENTIDAD": entity, "ANIO": 2024, "MES": 11, "A_RESIDENCIAL_E": 45},
            {"K_ENTIDAD": entity, "ANIO": 2024, "MES": 12, "A_RESIDENCIAL_E": 20},
            {"K_ENTIDAD": entity, "ANIO": 2024, "MES": 12, "A_RESIDENCIAL_E": 30},
        ])
        household_rows.append({"K_ENTIDAD": entity, "FAC_HOG": 100})

    data, metadata = B21.build_metrics(
        pd.DataFrame(bit_rows), pd.DataFrame(household_rows)
    )

    assert (metadata["anio_bit"], metadata["mes_bit"]) == (2024, 12)
    assert metadata["penetracion_nacional"] == 50.0
    assert metadata["penetracion_nacional_grafica"] == 50
    assert data["accesos_residenciales"].tolist() == [50] * 32
    assert data["penetracion_grafica"].tolist() == [50] * 32


def test_b21_color_classes_follow_the_reference_breaks():
    assert B21._class_color(54) == B21.COLORS[0]
    assert B21._class_color(55) == B21.COLORS[1]
    assert B21._class_color(65) == B21.COLORS[1]
    assert B21._class_color(66) == B21.COLORS[2]
    assert B21._class_color(76) == B21.COLORS[3]
    assert B21._class_color(86) == B21.COLORS[4]
