from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import pytest

from anuario2026.pipeline import load_generator, preflight_status
from anuario2026.registry import load_figures, load_project_config
from anuario2026 import inram_radio as radio
from anuario2026.narratives import load_narrative_audit

ROOT = Path(__file__).resolve().parents[1]
ODS = ROOT / 'data/manual/H/datos_inram_h11_h14_2024.ods'
IDS = ['H.11', 'H.12', 'H.13', 'H.14']


@pytest.mark.parametrize('figure_id', IDS)
def test_supplied_raw_file_reproduces_all_published_2024_statistics(figure_id):
    curves, studies, details = radio.calculate_data(ODS, figure_id)
    assert radio.validar_2024(figure_id, curves, studies)
    assert len(studies) == 12
    assert len(details) == (1944 if figure_id == 'H.11' else 648)
    stats = radio.resumen(curves)
    for target, (mean, maximum, hour) in radio.REFERENCIA_2024[figure_id.replace('.', '')].items():
        assert round(stats[target]['promedio'], 2) == mean
        assert round(stats[target]['maximo'], 2) == maximum
        assert stats[target]['hora_maximo'] == hour
    # El control histórico no modifica la precisión conservada en la curva.
    assert stats['TOTAL']['promedio'] != round(stats['TOTAL']['promedio'], 2)


def sample_sheets():
    sheets = {'UNIVERSOS': [['PLAZA', 'TARGET', 'ESTUDIO', 'POBLACION']]}
    for city in radio.PLAZA_HOJAS:
        population = {'CDMX': 100, 'GDL': 200, 'MTY': 300}[city]
        for target, sheet in radio.PLAZA_HOJAS[city].items():
            sheets[sheet] = [['TIPO DE ESTUDIO', 'MEDIO', 'PLAZA', 'ESTUDIO',
                              'GRUPO', 'EMISORA', 'SIGLAS', 'BANDA', *radio.HORAS]]
            for study, multiplier in [('Julio 2025', 1), ('Agosto 2025', 3)]:
                # La segunda fila tiene otra banda: el método suma ambas.
                for band, value in [('AM', 2), ('FM', population / 100)]:
                    sheets[sheet].append(['Mediómetro', 'Radio', radio.PLAZA_NOMBRE[city],
                                          study, '', 'Estación', '', band,
                                          *([value * multiplier] * 18)])
                sheets['UNIVERSOS'].append([radio.PLAZA_NOMBRE[city], target, study,
                                            str(population * multiplier)])
    return sheets


def test_weighting_and_period_follow_manual_content(monkeypatch):
    sheets = sample_sheets()
    monkeypatch.setattr(radio, 'leer_ods', lambda p: sheets)
    curves, studies, _ = radio.calculate_data(ODS, 'H.11')
    # Meses con ratings y universos diferentes: el segundo contribuye nueve veces.
    # (3*100*10 + 4*200*10 + 5*300*10) / (100*4 + 200*4 + 300*4)
    np.testing.assert_allclose(curves['TOTAL'], 65 / 6)
    assert studies == ['Julio 2025', 'Agosto 2025']
    assert not radio.validar_2024('H.11', curves, studies)
    text = radio.narrative_text(ROOT, 'H.11', curves, studies)
    assert 'julio 2025 a agosto 2025' in text
    assert '10.83%' in text and 'IFT10' not in text


@pytest.mark.parametrize('problem,match', [
    ('missing_sheet', 'Falta la hoja'), ('missing_population', 'Falta universo'),
    ('duplicate_population', 'duplicado'), ('zero_population', 'Universo inválido'),
    ('nan_rating', 'Ratings inválidos'), ('missing_hour', 'Registro incompleto'),
    ('mismatched_months', 'no coinciden'), ('wrong_city', 'Plaza incorrecta'),
    ('unknown_month', 'no reconocido'),
])
def test_invalid_manual_inputs_are_rejected(monkeypatch, problem, match):
    sheets = deepcopy(sample_sheets())
    rows = sheets['CDMX_TOTAL']
    if problem == 'missing_sheet': del sheets['CDMX_TOTAL']
    elif problem == 'missing_population': sheets['UNIVERSOS'].pop(1)
    elif problem == 'duplicate_population': sheets['UNIVERSOS'].append(sheets['UNIVERSOS'][1])
    elif problem == 'zero_population': sheets['UNIVERSOS'][1][3] = '0'
    elif problem == 'nan_rating': rows[1][8] = 'nan'
    elif problem == 'missing_hour': rows[1].pop()
    elif problem == 'mismatched_months': del sheets['CDMX_HOMBRES'][3:]
    elif problem == 'wrong_city': rows[1][2] = 'Monterrey'
    elif problem == 'unknown_month': rows[1][3] = 'Mes 2025'
    monkeypatch.setattr(radio, 'leer_ods', lambda p: sheets)
    with pytest.raises(ValueError, match=match): radio.calculate_data(ODS, 'H.11')


def test_missing_file_reports_exact_manual_location_without_acquisition(tmp_path):
    figures = load_figures(ROOT, load_project_config(ROOT))
    for figure in [f for f in figures if f.figure_id in IDS]:
        assert callable(load_generator(figure))
        state, message, files = preflight_status(tmp_path, figure)
        assert state == 'BLOQUEADA_INSUMO_MANUAL'
        assert 'datos_inram_h11_h14_2024.ods' in message
        assert str(tmp_path / 'data/manual/H') in message
        assert not files


def test_narrative_rejects_changed_manual_file(tmp_path):
    for rel in ['assets/presentation/narrativas_figuras_2026.json',
                'data/manual/H/datos_inram_h11_h14_2024.ods']:
        destination = tmp_path / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, destination)
    data = tmp_path / 'results.csv'; data.write_text('target,porcentaje\nTOTAL,20\n')
    text = tmp_path / 'h11.md'; text.write_text('Promedio de 20.00%.')
    manual = tmp_path / 'data/manual/H/datos_inram_h11_h14_2024.ods'
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    payload = {'result': {'data_path': str(data), 'text_path': str(text),
                         'manual_path': manual.relative_to(tmp_path).as_posix(),
                         'data_sha256': digest(data), 'text_sha256': digest(text),
                         'manual_sha256': digest(manual),
                         'narrative_mode': 'manual_inram_records_only'}}
    meta = tmp_path / 'build/metadata/h_11.json'; meta.parent.mkdir(parents=True)
    meta.write_text(json.dumps(payload), encoding='utf-8')
    record = load_narrative_audit(tmp_path, run_dir=None).records['H.11']
    assert record.verification_status == 'verified'
    assert record.updated_text == text.read_text()
    manual.write_bytes(manual.read_bytes() + b'changed')
    assert load_narrative_audit(tmp_path, run_dir=None).records['H.11'].verification_status == 'data_changed'


def test_ods_number_uses_raw_value_instead_of_formatted_text():
    from xml.etree import ElementTree as ET
    cell = ET.fromstring(f'<table:table-cell xmlns:table="{radio.NS["table"]}" '
                         f'xmlns:office="{radio.NS["office"]}" xmlns:text="{radio.NS["text"]}" '
                         'office:value-type="float" office:value="1.23456789">'
                         '<text:p>1.23</text:p></table:table-cell>')
    assert radio._texto_celda(cell) == '1.23456789'
