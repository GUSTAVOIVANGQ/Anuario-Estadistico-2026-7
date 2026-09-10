from __future__ import annotations

import csv
import importlib.util
import io
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "figures" / "figura_a_4.py"
SPEC = importlib.util.spec_from_file_location("figura_a_4_test", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _bit_zip(path: Path) -> None:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(
        [
            "ANIO",
            " INV_INFRA_E ",
            " INV_ACT_NO_TANG_E  ",
            " INV_OTRO_ACT_E ",
            " INV_NO_ESP_E ",
            " INV_TOTAL_E ",
            "CONCESIONARIO",
        ]
    )
    writer.writerow(
        [2023, " 40,000,000,000 ", "10,000,000,000", "5,000,000,000", "-", "55,000,000,000", "Compañía"]
    )
    writer.writerow(
        [2024, " 30,000,000,000 ", "6,000,000,000", "4,000,000,000", "-", "40,000,000,000", "Compañía"]
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "TODO/TD_INVERSION_TELECOM_ITE_VA.csv",
            stream.getvalue().encode("latin1"),
        )


def test_a4_reads_only_required_bit_member_and_calculates_billions(tmp_path: Path):
    path = tmp_path / "TODO.zip"
    _bit_zip(path)

    raw = MODULE.load_bit_table(path)
    result = MODULE.calculate_annual_investment(raw)

    assert result["anio"].tolist() == [2023, 2024]
    assert result.iloc[-1]["total_miles_millones_pesos"] == 40.0
    assert result.iloc[-1]["infraestructura_pct"] == 75.0
    assert result.iloc[-1]["otros_activos_pct"] == 10.0
    assert result.iloc[-1]["activos_no_tangibles_pct"] == 15.0
    assert result.iloc[-1]["no_especificada_pct"] == 0.0
