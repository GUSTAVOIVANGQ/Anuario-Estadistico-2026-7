from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    path = ROOT / "scripts" / "figures" / f"figura_{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


C5 = load("c_5")
C6 = load("c_6")
C8 = load("c_8")
C9 = load("c_9")
C10 = load("c_10")
C12 = load("c_12")
C14 = load("c_14")
C15 = load("c_15")
C16 = load("c_16")


def test_c5_uses_latest_complete_december_and_millions() -> None:
    raw = pd.DataFrame({
        "ANIO": [2023, 2024, 2025], "MES": [12, 12, 6],
        "L_PREPAGO_E": [1_000_000, 2_000_000, 9_000_000],
        "L_POSPAGO_E": [0, 0, 0], "L_POSPAGOC_E": [0, 100_000, 0],
        "L_POSPAGOL_E": [0, 200_000, 0], "L_NO_ESPECIFICADO_E": [0, 0, 0],
        "L_TOTAL_E": [1_000_000, 2_300_000, 9_000_000],
    })
    data, meta = C5.build_metrics(raw)
    assert meta["anio"] == 2024
    assert data.iloc[-1]["L_TOTAL_E"] == pytest.approx(2.3)


def test_c6_uses_published_national_series() -> None:
    raw = pd.DataFrame({"ANIO": [2023, 2024, 2025], "MES": [12, 12, 6], "T_H_TELMOVIL_E": [110, 115, 120]})
    data, meta = C6.build_metrics(raw)
    assert meta["anio"] == 2024
    assert data.teledensidad.tolist() == [110, 115]


def test_c8_sums_all_quarters() -> None:
    raw = pd.DataFrame({"ANIO": [2024] * 4, "TRAF_SALIDA": [1_000_000, 2_000_000, 3_000_000, 4_000_000]})
    data, _ = C8.build_metrics(raw)
    assert data.iloc[0].trafico_millones_minutos == pytest.approx(10)


def test_c9_groups_market_share() -> None:
    raw = pd.DataFrame({"ANIO": [2024] * 4, "MES": [12] * 4, "K_GRUPO": ["G006", "G003", "G007", "C999"], "GRUPO": ["A", "B", "C", "D"], "MARKET_SHARE": ["55%", "14%", "15%", "16%"]})
    data, _ = C9.build_metrics(raw)
    assert data.iloc[0][C9.ORDER].sum() == pytest.approx(100)


def test_c10_c12_c16_ignore_partial_following_year() -> None:
    d10, m10 = C10.build_metrics(pd.DataFrame({"ANIO": [2024, 2025], "MES": [12, 6], "IHH_TELMOVIL_E": [3589, 3500]}))
    d12, m12 = C12.build_metrics(pd.DataFrame({"ANIO": [2024, 2025], "MES": [12, 6], "T_H_INTMOVIL_E": [102, 104]}))
    d16, m16 = C16.build_metrics(pd.DataFrame({"ANIO": [2024, 2025], "MES": [12, 6], "IHH_TELFIJA_E": ["4,033", "3,900"]}))
    assert (m10["anio"], d10.iloc[-1].ihh) == (2024, 3589)
    assert (m12["anio"], d12.iloc[-1].teledensidad) == (2024, 102)
    assert (m16["anio"], d16.iloc[-1].ihh) == (2024, 4033)


def test_c14_annualizes_months_in_same_units() -> None:
    rows = []
    for month in (1, 2, 12):
        rows.append({"ANIO": 2024, "MES": month, "TRAF_TB_2G_E": 1, "TRAF_TB_3G_E": 2,
                     "TRAF_TB_4G_E": 7, "TRAF_TB_NO_ESPECIFICADO_E": 0, "TOTAL_TB_E": 10})
    data, meta = C14.build_metrics(pd.DataFrame(rows))
    assert meta["anio"] == 2024
    assert data.iloc[0].TOTAL_TB_E == 30
    assert data.iloc[0].pct_4g == pytest.approx(70)


def test_c15_groups_internet_mobile_market() -> None:
    raw = pd.DataFrame({"ANIO": [2024] * 5, "MES": [12] * 5,
                        "K_GRUPO": ["G006", "G007", "C804", "G003", "C999"],
                        "GRUPO": ["A", "B", "C", "D", "E"],
                        "MARKET_SHARE": ["60%", "15%", "13%", "7%", "5%"]})
    data, _ = C15.build_metrics(raw)
    assert data.iloc[0][C15.ORDER].sum() == pytest.approx(100)
