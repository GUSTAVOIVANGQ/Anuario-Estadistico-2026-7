from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load(number: int):
    path = PROJECT_ROOT / "scripts" / "figures" / f"figura_a_{number}.py"
    name = f"figura_a_{number}_test"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


A7 = _load(7)
A8 = _load(8)
A9 = _load(9)
A10 = _load(10)


def test_bundle_member_selector_prefers_the_2024_data_table():
    names = [
        "conjunto_de_datos_hogares_enigh2024_ns/catalogos/si_no.csv",
        "conjunto_de_datos_hogares_enigh2024_ns/conjunto_de_datos/"
        "conjunto_de_datos_hogares_enigh2024_ns.csv",
        "conjunto_de_datos_hogares_enigh2024_ns/diccionario_de_datos/"
        "diccionario_datos_hogares_enigh2024_ns.csv",
    ]
    expected = names[1]
    assert A7._member(names, "hogares") == expected
    assert A8._member(names, "hogares") == expected
    assert A9._member(names, "hogares") == expected
    assert A10._member(names, "hogares") == expected


def _tables():
    concentrated: list[dict[str, str]] = []
    households: list[dict[str, str]] = []
    expenses: list[dict[str, str]] = []
    for index in range(100):
        decile = index // 10 + 1
        household_id = str(index + 1)
        concentrated.append({
            "folioviv": household_id, "foliohog": "1",
            "ing_cor": str(decile * 3000), "factor": "1",
        })
        households.append({
            "folioviv": household_id, "foliohog": "1",
            "telefono": "1", "tv_paga": "0", "conex_inte": "0", "celular": "1",
        })
        expenses.extend([
            {"folioviv": household_id, "foliohog": "1", "clave": "083101",
             "gasto_tri": str(decile * 300), "gas_nm_tri": "0"},
            {"folioviv": household_id, "foliohog": "1", "clave": "083201",
             "gasto_tri": str(decile * 150), "gas_nm_tri": "0"},
        ])
    gp = pd.DataFrame(columns=["folioviv", "foliohog", "clave", "gasto_tri"])
    return pd.DataFrame(concentrated), pd.DataFrame(households), pd.DataFrame(expenses), gp


def test_a7_and_a8_use_enigh_2024_fixed_service_keys_and_weighted_deciles():
    concentrated, households, gh, gp = _tables()
    a7 = A7.build_metrics(concentrated, households.drop(columns="celular"), gh, gp)
    a8 = A8.build_metrics(concentrated, households.drop(columns="celular"), gh, gp)

    assert a7["anio"].unique().tolist() == [2024]
    assert a7["decil"].tolist() == list(range(1, 11))
    assert a7["pct_hogares_con_telecom_fijas"].tolist() == [100.0] * 10
    assert a7["pct_hogares_disponen_y_gastan"].tolist() == [100.0] * 10
    assert a8.iloc[0]["gasto_promedio_mensual_pesos"] == 100
    assert a8.iloc[-1]["gasto_promedio_mensual_pesos"] == 1000
    assert a8["gasto_pct_ingreso"].tolist() == [10.0] * 10


def test_a9_and_a10_use_mobile_ccif_keys_not_legacy_education_key():
    concentrated, households, gh, gp = _tables()
    mobile_households = households[["folioviv", "foliohog", "celular"]]
    a9 = A9.build_metrics(concentrated, mobile_households, gh, gp)
    a10 = A10.build_metrics(concentrated, mobile_households, gh, gp)

    assert "E002" not in A9.MOVILES_CLAVES_2024
    assert A9.MOVILES_CLAVES_2024 == {"083201", "083202", "083405"}
    assert a9["anio"].unique().tolist() == [2024]
    assert a9["pct_hogares_con_telecom_moviles"].tolist() == [100.0] * 10
    assert a9["pct_hogares_disponen_y_gastan"].tolist() == [100.0] * 10
    assert a10.iloc[0]["gasto_promedio_mensual_pesos"] == 50
    assert a10.iloc[-1]["gasto_promedio_mensual_pesos"] == 500
    assert a10["gasto_pct_ingreso"].tolist() == [5.0] * 10
