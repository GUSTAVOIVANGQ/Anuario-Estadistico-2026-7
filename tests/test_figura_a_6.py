from __future__ import annotations

import csv
import importlib.util
import io
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "figures" / "figura_a_6.py"
SPEC = importlib.util.spec_from_file_location("figura_a_6_test", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _income_zip(path: Path) -> None:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["ANIO", "TRIM", " INGRESOS_TOTAL_E ", "I_ANUAL_TRIM"])
    for year in range(2017, 2025):
        for quarter in range(1, 5):
            writer.writerow([year, quarter, f"{year * 1_000_000_000:,}", "Trimestral"])
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "TODO/TD_INGRESOS_TELECOM_ITE_VA.csv",
            stream.getvalue().encode("latin1"),
        )


def test_a6_uses_latest_income_data_and_latest_complete_margin_period(tmp_path: Path):
    path = tmp_path / "TODO.zip"
    _income_zip(path)

    raw = MODULE.load_income_table(path)
    result, source_latest = MODULE.build_series(raw)

    assert source_latest == (2024, 4)
    assert result[["anio", "trimestre"]].iloc[-1].tolist() == [2024, 4]
    assert result.iloc[-1]["ingresos_miles_millones_pesos"] == 2024.0
    assert not result.iloc[-1]["desglose_disponible"]
    complete = result.loc[result["desglose_disponible"]].iloc[-1]
    assert complete["margen_pct"] == 29
    assert complete["margen_miles_millones_pesos"] == 586.67
    assert complete["egresos_miles_millones_pesos"] == 1436.33
