from __future__ import annotations

import ast
import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _script(number: int) -> Path:
    return ROOT / "scripts" / "figures" / f"figura_e_{number}.py"


def _load(number: int):
    path = _script(number)
    spec = importlib.util.spec_from_file_location(f"test_e_{number}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _raw(year: int) -> Path:
    files = list((ROOT / "data" / "raw" / f"ift_mipymes_{year}_base" / "objects").glob("*/*.zip"))
    assert files
    return files[0]


def test_cada_figura_es_autonoma_y_declara_el_flujo_completo():
    for number in range(3, 9):
        source = _script(number).read_text(encoding="utf-8")
        tree = ast.parse(source)
        assert f'"E.{number}"' in source
        assert "context.acquire_source" in source
        assert "context.write_data_used" in source
        assert "context.record_calculation" in source
        assert "context.render_text" in source
        assert any(isinstance(node, ast.FunctionDef) and node.name == "generate" for node in tree.body)
        assert "_mipymes_common" not in source


def test_fuentes_e_indicadores_estan_registrados():
    with (ROOT / "inventario_fuentes.csv").open(encoding="utf-8-sig", newline="") as stream:
        sources = {row["source_id"]: row for row in csv.DictReader(stream)}
    for year in (2022, 2023, 2024):
        source = sources[f"ift_mipymes_{year}_base"]
        assert source["owner"] == "Instituto Federal de Telecomunicaciones (IFT)"
        assert source["detected_period"] == str(year)
    with (ROOT / "inventario_indicadores.csv").open(encoding="utf-8-sig", newline="") as stream:
        indicators = {row["id_indicador"]: row for row in csv.DictReader(stream)}
    for number in range(3, 9):
        assert "ift_mipymes_2024_base" in indicators[f"E.{number}"]["fuentes_requeridas"]
        assert indicators[f"E.{number}"]["implementacion"] == "actualizado"


def test_calculos_reproducen_las_referencias_publicadas():
    modules = {number: _load(number) for number in range(3, 9)}
    frames = {year: modules[3].load_raw(_raw(year)) for year in (2022, 2023, 2024)}
    assert modules[3].validate(modules[3].build_metrics(frames)) <= .1100001
    for number in (4, 5, 7, 8):
        data = modules[number].build_metrics({2023: frames[2023], 2024: frames[2024]})
        assert modules[number].validate(data) <= .1100001
    e6 = modules[6].build_metrics(frames[2024])
    for size, expected in modules[6].REFERENCE.items():
        actual = e6.loc[e6.tamano.eq(size), "porcentaje"].round(1).tolist()
        assert actual == pytest.approx(expected, abs=.1)


def test_png_finales_tienen_lienzo_16_por_9():
    from PIL import Image

    for number in range(3, 9):
        path = ROOT / "build" / "figures" / "E" / f"figura_e_{number}.png"
        assert path.is_file()
        with Image.open(path) as image:
            assert image.size == (3200, 1800)
