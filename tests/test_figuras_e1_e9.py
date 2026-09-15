from __future__ import annotations

import ast
import csv
import importlib.util
from pathlib import Path

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


def _raw(source_id: str) -> Path:
    files = list((ROOT / "data" / "raw" / source_id / "objects").glob("*/*.zip"))
    assert files
    return files[0]


def test_cada_figura_es_autonoma_y_declara_el_flujo_completo():
    for number in (1, 9):
        source = _script(number).read_text(encoding="utf-8")
        tree = ast.parse(source)
        assert f'"E.{number}"' in source
        assert "context.acquire_source" in source
        assert "context.write_data_used" in source
        assert "context.record_calculation" in source
        assert "context.render_text" in source
        assert any(isinstance(node, ast.FunctionDef) and node.name == "generate" for node in tree.body)
        assert "legacy" not in source.lower()


def test_fuentes_e_indicadores_estan_registrados():
    with (ROOT / "inventario_fuentes.csv").open(encoding="utf-8-sig", newline="") as stream:
        sources = {row["source_id"]: row for row in csv.DictReader(stream)}
    assert sources["ift_segunda_encuesta_usuarios_2025"]["consumers"] == "E.1"
    assert sources["ift_segunda_encuesta_usuarios_2025"]["detected_period"] == "2024"
    assert sources["ift_mipymes_impexp_2022_base"]["consumers"] == "E.9"
    assert sources["ift_mipymes_impexp_2022_base"]["detected_period"] == "2022"
    with (ROOT / "inventario_indicadores.csv").open(encoding="utf-8-sig", newline="") as stream:
        indicators = {row["id_indicador"]: row for row in csv.DictReader(stream)}
    assert indicators["E.1"]["implementacion"] == "actualizado"
    assert indicators["E.9"]["implementacion"] == "actualizado"


def test_e1_reproduce_igs_historico_y_actual():
    module = _load(1)
    data = []
    for year, source_id in module.SOURCES.items():
        data.append(module.load_metrics(_raw(source_id), year))
    combined = module.pd.concat(data, ignore_index=True)
    assert module.validate(combined) <= .0000001


def test_e9_reproduce_los_porcentajes_publicados():
    module = _load(9)
    frame, _, question, factor = module.load_raw(_raw(module.SOURCE_ID))
    data = module.build_metrics(frame, question, factor)
    assert module.validate(data) <= .0000001
    assert round(float(data.porcentaje.sum()), 1) == 97.8


def test_png_finales_tienen_lienzo_16_por_9():
    from PIL import Image

    for number in (1, 9):
        path = ROOT / "build" / "figures" / "E" / f"figura_e_{number}.png"
        assert path.is_file()
        with Image.open(path) as image:
            assert image.size == (3200, 1800)
