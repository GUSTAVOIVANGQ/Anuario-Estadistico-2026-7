from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "figures" / "figura_a_1.py"
SPEC = importlib.util.spec_from_file_location("figura_a_1_test", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_extract_quarterly_data_uses_labels_instead_of_fixed_rows():
    frame = pd.DataFrame([[None] * 9 for _ in range(12)])
    frame.iat[2, 0] = "Concepto"
    frame.iat[2, 1] = "2013P"
    frame.iat[2, 5] = "2014"
    frame.iloc[3, 1:9] = ["T1", "T2", "T3", "T4", "T1R", "T2R", "T3P", "T4P"]
    frame.iat[4, 0] = "Millones de pesos a precios de 2018"
    frame.iat[5, 0] = "____aB.1bP - Producto interno bruto"
    frame.iat[7, 0] = "515 - Radio y televisión"
    frame.iat[9, 0] = "517 - Telecomunicaciones"
    frame.iloc[5, 1:9] = [10_000, 11_000, 12_000, 13_000, 14_000, 15_000, 16_000, 17_000]
    frame.iloc[7, 1:9] = [10, 11, 12, 13, 14, 15, 16, 17]
    frame.iloc[9, 1:9] = [90, 99, 108, 117, 126, 135, 144, 153]

    result = MODULE.extract_quarterly_data(frame)

    assert result["periodo"].tolist() == [
        "2013-T1",
        "2013-T2",
        "2013-T3",
        "2013-T4",
        "2014-T1",
        "2014-T2",
        "2014-T3",
        "2014-T4",
    ]
    assert result.iloc[-1]["tyr_millones_pesos"] == 170
    assert result.iloc[-1]["participacion_tyr_pct"] == 1.0
