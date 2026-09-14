from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    path = ROOT / "scripts" / "figures" / f"figura_{name}.py"
    spec = importlib.util.spec_from_file_location(f"figura_{name}_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B1 = _load("b_1")
B2 = _load("b_2")
B3 = _load("b_3")
C3 = _load("c_3")
C4 = _load("c_4")
D2 = _load("d_2")
D3 = _load("d_3")
D4 = _load("d_4")


def _hogares() -> pd.DataFrame:
    combinations = [
        (1, 1, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1),
        (1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, 0),
    ]
    rows = []
    for domain in ("R", "U"):
        for internet, tv, phone in combinations:
            rows.append({
                "P4_4": "1" if internet else "2",
                "P4_5": "1" if internet else "",
                "P5_1": "1" if tv else "2",
                "P5_5": "1" if phone else "2",
                "DOMINIO": domain,
                "FAC_HOG": "1" if domain == "R" else "2",
            })
    return pd.DataFrame(rows)


def test_b1_b2_b3_use_fac_hog_and_the_declared_domain():
    national, total_n = B1.build_metrics(_hogares())
    rural, total_r = B2.build_metrics(_hogares())
    urban, total_u = B3.build_metrics(_hogares())
    assert (total_n, total_r, total_u) == (24, 8, 16)
    expected = {
        "Tres servicios": 12.5,
        "Dos servicios": 37.5,
        "Un servicio": 37.5,
        "Ninguno": 12.5,
    }
    for frame in (national, rural, urban):
        totals = frame.loc[frame["grupo"].eq("total")].set_index("categoria")["porcentaje"]
        assert totals.to_dict() == expected
        assert totals.sum() == pytest.approx(100.0)


def test_c3_c4_reproduce_the_reference_estimator_and_ignore_under_six():
    rows = [
        {"EDAD": "6", "P8_1": "1", "P8_4_2": "1", "FAC_PER": "1230", "DOMINIO": "U"},
        {"EDAD": "6", "P8_1": "2", "P8_4_2": "2", "FAC_PER": "270", "DOMINIO": "U"},
        {"EDAD": "6", "P8_1": "1", "P8_4_2": "1", "FAC_PER": "252", "DOMINIO": "R"},
        {"EDAD": "6", "P8_1": "2", "P8_4_2": "2", "FAC_PER": "148", "DOMINIO": "R"},
        {"EDAD": "5", "P8_1": "1", "P8_4_2": "1", "FAC_PER": "9999", "DOMINIO": "R"},
    ]
    expected = {"Nacional": 78, "Urbano": 82, "Rural": 63}
    for module in (C3, C4):
        result = module.build_metrics(pd.DataFrame(rows))
        values = result.set_index("zona")["porcentaje_uso_grafica"].to_dict()
        assert values == expected


def test_d2_requires_cellphone_availability_and_smartphone_type():
    ages = [6, 12, 18, 25, 35, 45, 55]
    user_rows = []
    user2_rows = []
    for index, age in enumerate(ages, start=1):
        for suffix, answer in ((1, "1"), (2, "2")):
            key = {"UPM": str(index), "VIV_SEL": "1", "HOGAR": "1", "NUM_REN": str(suffix)}
            user_rows.append({**key, "EDAD": str(age), "P7_1": answer, "FAC_PER": "1"})
            # Sólo la primera persona dispone de celular y usa smartphone.
            user2_rows.append({**key, "P8_1": answer, "P8_4_2": answer})
    result = D2.build_metrics(pd.DataFrame(user_rows), pd.DataFrame(user2_rows))
    assert result["smartphone_pct"].tolist() == [50.0] * 7
    assert result["internet_pct"].tolist() == [50.0] * 7


def test_d3_is_a_fac_per_weighted_average():
    ages = [6, 12, 18, 25, 35, 45, 55, 65]
    rows = []
    for age in ages:
        rows.extend([
            {"EDAD": age, "P7_4": 2, "FAC_PER": 1},
            {"EDAD": age, "P7_4": 4, "FAC_PER": 3},
        ])
    result = D3.build_metrics(pd.DataFrame(rows))
    assert result["horas_promedio"].tolist() == [3.5] * 8


def test_d4_denominator_is_people_using_any_iot_device():
    rows = []
    for index in range(10):
        row = {column: "2" for column in D4.VARIABLES}
        row[D4.VARIABLES[index]] = "1"
        row["FAC_PER"] = "1"
        rows.append(row)
    result, denominator = D4.build_metrics(pd.DataFrame(rows))
    assert denominator == 10
    assert result["porcentaje"].tolist() == [10.0] * 10
