from __future__ import annotations

import csv
import importlib.util
import io
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "figures" / "figura_a_2.py"
SPEC = importlib.util.spec_from_file_location("figura_a_2_test", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _csv_text(columns: list[str], rows: list[list[int]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(columns)
    writer.writerows(rows)
    return stream.getvalue()


def test_extract_period_uses_full_person_keys_and_new_entity_alias(tmp_path: Path):
    keys = list(MODULE.MERGE_KEYS)
    alias_keys = ["cve_ent" if key == "ent" else key for key in keys]
    key_rows = [
        [1, 9, 10, 11, 12, 13, 14, 1, 0, 1, 1, index]
        for index in (1, 2, 3)
    ]
    path = tmp_path / "enoe_2026_trim2_csv.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "ENOE_SDEMT226.csv",
            _csv_text(
                alias_keys + ["clase1", "clase2", "fac_tri"],
                [
                    key_rows[0] + [1, 1, 100],
                    key_rows[1] + [1, 1, 50],
                    key_rows[2] + [1, 2, 999],
                ],
            ),
        )
        archive.writestr(
            "ENOE_COE1T226.csv",
            _csv_text(
                alias_keys + ["p4a"],
                [
                    key_rows[0] + [517110],
                    key_rows[1] + [515120],
                    key_rows[2] + [517110],
                ],
            ),
        )

    result = MODULE.extract_period(path, 2026, 2)

    assert result["telecomunicaciones_personas"] == 100
    assert result["radiodifusion_personas"] == 50
    assert result["total_personas"] == 150
    assert result["telecomunicaciones_pct"] == 66.666667


def test_required_quarters_cover_reference_and_latest_period():
    downloader_dir = PROJECT_ROOT / "scripts" / "downloaders"
    sys.path.insert(0, str(downloader_dir))
    try:
        from inegi_enoe_playwright import required_quarters
    finally:
        sys.path.remove(str(downloader_dir))

    specs = required_quarters()
    assert len(specs) == 27
    assert specs[0].period == "2013-T2"
    assert specs[-1].period == "2026-T2"
    assert specs[-1].filename == "enoe_2026_trim2_csv.zip"
