from __future__ import annotations

import ast
import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _script(number: int) -> Path:
    return ROOT / "scripts" / "figures" / f"figura_d_{number}.py"


def _load(number: int):
    path = _script(number)
    spec = importlib.util.spec_from_file_location(f"test_d_{number}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _raw_path() -> Path:
    candidates = list((ROOT / "data" / "raw" / "ift_ecsi_2024_base" / "objects").glob("*/baseconfianzadigital.csv"))
    assert candidates
    return candidates[0]


def test_cada_figura_es_autonoma_y_declara_el_flujo_completo():
    for number in range(5, 12):
        source = _script(number).read_text(encoding="utf-8")
        tree = ast.parse(source)
        assert f'"D.{number}"' in source
        assert "context.acquire_source" in source
        assert "context.write_data_used" in source
        assert "context.record_calculation" in source
        assert "context.render_text" in source
        assert any(isinstance(node, ast.FunctionDef) and node.name == "generate" for node in tree.body)
        assert "_ecsi_d_common" not in source


def test_fuente_e_indicadores_estan_registrados():
    with (ROOT / "inventario_fuentes.csv").open(encoding="utf-8-sig", newline="") as stream:
        sources = {row["source_id"]: row for row in csv.DictReader(stream)}
    source = sources["ift_ecsi_2024_base"]
    assert source["owner"] == "Instituto Federal de Telecomunicaciones (IFT)"
    assert source["detected_period"] == "2024"
    with (ROOT / "inventario_indicadores.csv").open(encoding="utf-8-sig", newline="") as stream:
        indicators = {row["id_indicador"]: row for row in csv.DictReader(stream)}
    for number in range(5, 12):
        assert indicators[f"D.{number}"]["fuentes_requeridas"] == "ift_ecsi_2024_base"
        assert indicators[f"D.{number}"]["implementacion"] == "actualizado"


def test_calculos_reproducen_las_cifras_publicadas():
    raw = _raw_path()
    for number in range(5, 12):
        module = _load(number)
        if number == 5:
            data, _ = module.build_metrics(module.load_raw(raw))
        else:
            data = module.load_and_calculate(raw)
        assert len(data) > 0
        if number in (5, 8):
            assert data.porcentaje.round(1).tolist() == pytest.approx(module.REFERENCE, abs=.1)


def test_png_finales_tienen_lienzo_16_por_9():
    from PIL import Image
    for number in range(5, 12):
        path = ROOT / "build" / "figures" / "D" / f"figura_d_{number}.png"
        assert path.is_file()
        with Image.open(path) as image:
            assert image.size == (3200, 1800)
