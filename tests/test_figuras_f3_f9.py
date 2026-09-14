from __future__ import annotations
import ast,csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def script(number:int)->Path:return ROOT/"scripts"/"figures"/f"figura_f_{number}.py"

def test_cada_figura_es_un_script_autonomo_auditable():
    for number in range(3,10):
        source=script(number).read_text(encoding="utf-8");tree=ast.parse(source)
        assert f'FIGURE_ID="F.{number}"' in source or f'FIGURE_ID = "F.{number}"' in source
        assert "context.acquire_source" in source
        assert "context.write_data_used" in source
        assert "context.record_calculation" in source
        assert "context.render_text" in source
        assert "load_microdata" in source and "calculate" in source and "_plot" in source
        assert any(isinstance(node,ast.FunctionDef) and node.name=="generate" for node in tree.body)

def test_inventario_declara_mociba_2025_y_salidas_propias():
    with (ROOT/"inventario_indicadores.csv").open(encoding="utf-8-sig",newline="") as stream:rows={r["id_indicador"]:r for r in csv.DictReader(stream)}
    for number in range(3,10):
        row=rows[f"F.{number}"]
        assert row["implementacion"]=="actualizado"
        assert row["fuentes_requeridas"]=="inegi_mociba_2025"
        assert "inegi_mociba_2024_reference" in row["fuentes_referencia"]
        assert row["script"]==f"scripts/figures/figura_f_{number}.py"
        assert row["salida_esperada"]==f"build/figures/F/figura_f_{number}.png"

def test_fuentes_oficiales_mociba_son_zip_csv():
    with (ROOT/"inventario_fuentes.csv").open(encoding="utf-8-sig",newline="") as stream:rows={r["source_id"]:r for r in csv.DictReader(stream)}
    assert rows["inegi_mociba_2025"]["filename"]=="mociba2025_bd_csv.zip"
    assert rows["inegi_mociba_2025"]["detected_period"]=="2025"
    assert rows["inegi_mociba_2024_reference"]["filename"]=="mociba2024_bd_csv.zip"

def test_pies_conservan_solo_etiquetas_del_referente():
    for number in range(3,10):
        source=script(number).read_text(encoding="utf-8")
        assert '"Fuente:"' in source
        assert '"Nota:"' not in source
        assert "control editorial" not in source.lower()
        assert "revisión" not in source.lower()
