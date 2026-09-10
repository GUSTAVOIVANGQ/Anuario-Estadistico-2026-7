from __future__ import annotations

import csv
import importlib.util
import io
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "figures" / "figura_a_3.py"
SPEC = importlib.util.spec_from_file_location("figura_a_3_test", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _dynamic_csv(path: Path) -> None:
    with path.open("w", encoding="latin1", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Instituto Nacional de Estadística y Geografía"])
        writer.writerow([])
        writer.writerow(
            [
                "Título",
                "Índice nacional, Nacional, total",
                "Índice nacional, Nacional, 08 Comunicaciones",
            ]
        )
        writer.writerow(["Dic 2010", "75.0", "160.0"])
        writer.writerow(["Dic 2023", "132.373", "91.819751"])
        writer.writerow(["Jul 2024", "136.003", "90.402427"])


def _current_zip(path: Path) -> None:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["COBERTURA", "PERIODICIDAD", "FECHA", "CONCEPTO", "VALOR", "UNIDAD_MEDIDA", "ESTATUS"])
    rows = [
        ("01/12/2010", 75.0),
        ("01/12/2023", 132.373),
        ("01/07/2024", 136.003),
        ("01/08/2025", 140.1),
        ("01/12/2025", 143.042),
        ("01/08/2026", 145.8),
    ]
    for date, value in rows:
        writer.writerow(
            [
                "Nacional",
                "Mensual",
                date,
                "Índice Nacional de Precios al Consumidor (INPC)",
                value,
                "Índice",
                "Definitivo",
            ]
        )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "conjunto_de_datos/conjunto_de_datos_inpc_mensual.csv",
            stream.getvalue().encode("latin1"),
        )


def test_a3_reads_both_official_structures_and_stops_ipcom_in_2024(tmp_path: Path):
    dynamic_path = tmp_path / "historico.csv"
    current_path = tmp_path / "vigente.zip"
    _dynamic_csv(dynamic_path)
    _current_zip(current_path)

    dynamic = MODULE.load_dynamic_series(dynamic_path)
    current = MODULE.load_current_inpc(current_path)
    result = MODULE.build_annual_series(dynamic, current)

    assert result.iloc[-1]["periodo_inpc"] == "2026-08"
    assert result.iloc[-1]["inpc"] == 145.8
    assert result.loc[result["anio"].eq(2024), "ipcom"].iloc[0] == 90.402427
    assert result.loc[result["anio"].eq(2025), "ipcom"].isna().all()
    assert result.loc[result["anio"].eq(2026), "ipcom"].isna().all()


def test_dynamic_cache_is_preferred_when_available(tmp_path: Path, monkeypatch):
    cached = tmp_path / "data" / "raw" / MODULE.DYNAMIC_SOURCE_ID / "objects" / "abc" / "a3.csv"
    cached.parent.mkdir(parents=True)
    _dynamic_csv(cached)
    monkeypatch.delenv("ANUARIO_FORCE_DOWNLOAD", raising=False)

    result = MODULE.acquire_dynamic_source(tmp_path)

    assert result.path == cached
    assert result.cache_status == "REUTILIZADO"
