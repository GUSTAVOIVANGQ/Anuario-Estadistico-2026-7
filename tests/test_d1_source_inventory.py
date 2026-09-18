import csv
from pathlib import Path

from anuario2026.sources import load_sources


def test_d1_uses_current_tabulation_filenames_and_registers_all_sources():
    root = Path(__file__).resolve().parents[1]
    sources = load_sources(root)
    with (root / "inventario_indicadores.csv").open(encoding="utf-8-sig", newline="") as stream:
        indicator = next(row for row in csv.DictReader(stream) if row["id_indicador"] == "D.1")
    for table in ("hnal110", "hnal130", "hnal111"):
        source_id = f"inegi_endutih_2023_tabulado_{table}"
        expected = f"2023_{table}.xlsx"
        assert sources[source_id]["filename"] == expected
        assert sources[source_id]["exact_url"].endswith(f"/tabulados/{expected}")
        assert source_id in indicator["fuentes_requeridas"].split(";")
