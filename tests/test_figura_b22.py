from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "figures" / "figura_b_22.py"
SPEC = importlib.util.spec_from_file_location("figura_b_22_test", SCRIPT)
assert SPEC and SPEC.loader
B22 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B22)


def test_b22_uses_latest_bit_period_and_exact_denue_denominator():
    rows = []
    for entity in range(1, 33):
        rows.extend([
            {"K_ENTIDAD": entity, "ANIO": 2023, "MES": 12,
             "accesos_no_residenciales": 40},
            {"K_ENTIDAD": entity, "ANIO": 2024, "MES": 12,
             "accesos_no_residenciales": 30},
            {"K_ENTIDAD": entity, "ANIO": 2024, "MES": 12,
             "accesos_no_residenciales": 20},
        ])
    data, metadata = B22.build_metrics(
        pd.DataFrame(rows), {entity: 500 for entity in range(1, 33)}
    )
    assert (metadata["anio_bit"], metadata["mes_bit"]) == (2024, 12)
    assert metadata["penetracion_nacional"] == 10.0
    assert metadata["crecimiento_anual"] == 25.0
    assert data["penetracion_grafica"].tolist() == [10] * 32


def test_b22_counts_only_denue_dataset_csv(tmp_path: Path):
    archive_path = tmp_path / "denue.zip"
    dataset = "cve_ent,entidad\n01,Aguascalientes\n01,Aguascalientes\n02,Baja California\n"
    dictionary = "CAMPO,DESCRIPCION\ncve_ent,Entidad\n"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("diccionario_de_datos/diccionario.csv", dictionary.encode("latin-1"))
        archive.writestr("conjunto_de_datos/denue.csv", dataset.encode("latin-1"))
    with zipfile.ZipFile(archive_path) as archive:
        member = B22._dataset_csv_members(archive)[0]
        with archive.open(member) as stream:
            assert B22._count_csv_stream(stream) == {1: 2, 2: 1}


def test_b22_reference_color_breaks():
    assert B22._class_color(3) == B22.COLORS[0]
    assert B22._class_color(4) == B22.COLORS[1]
    assert B22._class_color(7) == B22.COLORS[2]
    assert B22._class_color(10) == B22.COLORS[3]
    assert B22._class_color(13) == B22.COLORS[4]
