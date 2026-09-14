from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest


FIGURE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "figures"
if str(FIGURE_DIR) not in sys.path:
    sys.path.insert(0, str(FIGURE_DIR))

# B.4 contiene su propia copia de las rutinas verificables. La prueba importa
# el script real para asegurar que no exista una dependencia de ejecución en
# un motor compartido.
from figura_b_4 import _ihh, _market_share, _series_field, _series_sum, _speed


def test_series_sum_uses_latest_complete_december() -> None:
    raw = pd.DataFrame({
        "ANIO": [2023, 2023, 2024, 2024, 2025],
        "MES": [12, 12, 12, 12, 6],
        "TOTAL": [10, 5, 20, 4, 99],
    })
    data, meta = _series_sum(raw, "TOTAL", 2023)
    assert meta["year"] == 2024
    assert data.to_dict("records") == [
        {"ANIO": 2023, "TOTAL": 15},
        {"ANIO": 2024, "TOTAL": 24},
    ]


def test_series_field_does_not_use_partial_latest_year() -> None:
    raw = pd.DataFrame({
        "ANIO": [2023, 2024, 2025],
        "MES": [12, 12, 3],
        "P": [60, 64, 70],
    })
    data, meta = _series_field(raw, "P", 2023)
    assert meta["year"] == 2024
    assert data.iloc[-1].to_dict() == {"ANIO": 2024, "P": 64}


def test_market_share_groups_and_preserves_percent_scale() -> None:
    raw = pd.DataFrame({
        "ANIO": [2024, 2024, 2024],
        "MES": [12, 12, 12],
        "GRUPO": ["AMÉRICA MÓVIL", "TELMEX", "MEGACABLE-MCM"],
        "MARKET_SHARE": ["35.0%", "5.0%", "60.0%"],
    })
    data, meta = _market_share(raw, "B.9")
    assert data.loc[0, "América Móvil"] == pytest.approx(40.0)
    assert data.loc[0, "Megacable-MCM"] == pytest.approx(60.0)
    assert meta["leader"] == "Megacable-MCM"


def test_ihh_strips_thousands_separator() -> None:
    raw = pd.DataFrame({"ANIO": [2023, 2024], "MES": [12, 12], "IHH": ["2,700", "2,519"]})
    data, meta = _ihh(raw, "IHH")
    assert data["IHH"].tolist() == [2700, 2519]
    assert meta["value"] == 2519


def test_speed_percentages_sum_to_one_hundred() -> None:
    raw = pd.DataFrame({
        "ANIO": [2024, 2024], "MES": [12, 12],
        "A_V1_E": [10, 10], "A_V2_E": [20, 20], "A_V3_E": [30, 30],
        "A_V4_E": [35, 35], "A_NO_ESPECIFICADO_E": [5, 5],
        "A_TOTAL_E": [100, 100],
    })
    data, meta = _speed(raw)
    assert data.drop(columns="ANIO").sum(axis=1).iloc[0] == pytest.approx(100.0)
    assert meta["value"] == 200
