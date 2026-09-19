from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "figures" / "figura_g_1.py"


def _module():
    spec = importlib.util.spec_from_file_location("figura_g_1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_script_is_autonomous():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "context.acquire_source" in source
    assert "context.write_data_used" in source
    assert "context.record_calculation" in source
    assert "def main()" in source
    assert "figura_" not in "\n".join(line for line in source.splitlines() if line.startswith("from scripts"))


def test_calculation_uses_latest_common_year(tmp_path):
    radio = pd.DataFrame({
        "ANIO": [2022, 2023, 2023, 2023],
        "BANDA": ["AM", "AM", "FM", "FM"],
        "TIPO_USO": ["COMERCIAL", "COMERCIAL", "PUBLICO", "SOCIAL INDIGENA"],
        "NO_ESTACIONES": [99, 7, 5, 2],
    })
    tdt = pd.DataFrame({
        "ANIO": [2022, 2023, 2023, 2023],
        "DISTINTIVO": ["OLD", "A", "A", "B"],
        "TIPO_USO": ["COMERCIAL", "COMERCIAL", "COMERCIAL", "PUBLICO"],
    })
    radio_path = tmp_path / "radio.csv"
    tdt_path = tmp_path / "tdt.csv"
    radio.to_csv(radio_path, index=False)
    tdt.to_csv(tdt_path, index=False)
    data, comparison, year = _module().calculate_data(radio_path, tdt_path)
    assert year == 2023
    values = data.set_index(["servicio", "categoria"]).concesiones
    assert values["AM", "Comerciales"] == 7
    assert values["FM", "Públicas"] == 5
    assert values["TDT", "Comerciales"] == 1
    assert values["TDT", "Públicas"] == 1
    assert len(comparison) == 15


def test_inventory_and_configuration_register_g1():
    indicators = (ROOT / "inventario_indicadores.csv").read_text(encoding="utf-8-sig")
    sources = (ROOT / "inventario_fuentes.csv").read_text(encoding="utf-8-sig")
    config = (ROOT / "config" / "proyecto.json").read_text(encoding="utf-8")
    assert "G.1,G," in indicators
    assert "crt_bit_srs_estaciones_entidad_actual" in sources
    assert '"G.1"' in config and "figura_g_1.py" in config


def test_generated_png_is_16_9():
    path = ROOT / "build" / "figures" / "G" / "figura_g_1.png"
    assert path.is_file()
    with Image.open(path) as image:
        assert image.size == (3200, 1800)
