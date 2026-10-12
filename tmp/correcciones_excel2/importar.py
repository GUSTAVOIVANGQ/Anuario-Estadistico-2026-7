import hashlib
import json
from pathlib import Path
import openpyxl
import pandas as pd
import sys
sys.path.insert(0, str(Path.cwd()))
from scripts.figures.figura_a_1 import extract_quarterly_data

root = Path.cwd()
work = root / 'tmp/correcciones_excel2'
folder = root / 'data/manual/editorial'
folder.mkdir(exist_ok=True)
sheet = openpyxl.load_workbook('C:/Users/gustavo.garcia/Downloads/Anuario_mejoras (1).xlsx', data_only=True).active
registry = root / 'assets/presentation/textos_editoriales_2026.json'
payload = json.loads(registry.read_text(encoding='utf-8'))
revision = payload['publication_revision']
revision['version'] = 2
revision['additional_source_workbook'] = 'Anuario_mejoras (1).xlsx'
title, body = sheet.cell(2,5).value.strip().split('\n\n', 1)
revision['introduction'] = {'title': title, 'body': body, 'publication_page': 6, 'workbook_row': 2}
parts = sheet.cell(3,5).value.strip().split('\n\n')
revision['introduction_notes'] = [{'title': parts[i], 'body': parts[i+1]} for i in range(0,len(parts),2)]
raw = pd.read_csv(work/'ingresos_BIT.csv')
raw = raw[raw.I_ANUAL_TRIM.eq('Trimestral') & raw.ANIO.isin([2024,2025])].copy()
raw.INGRESOS_TOTAL_E = pd.to_numeric(raw.INGRESOS_TOTAL_E.astype(str).str.replace(',',''), errors='raise')
income = raw.groupby(['ANIO','TRIM'], as_index=False).INGRESOS_TOTAL_E.sum()
income.columns = ['anio','trimestre','ingresos_miles_millones_pesos']
income.ingresos_miles_millones_pesos /= 1e9
income.to_csv(folder/'ingresos_BIT_2024_2025.csv',index=False)
gdp = extract_quarterly_data(pd.read_excel(work/'PIBT_2.xlsx',header=None))
gdp = gdp[(gdp.anio.isin([2024,2025])) & (gdp.trimestre==4)]
gdp.to_csv(folder/'pib_TyR_2024_2025_T4.csv',index=False)
sources = json.loads((work/'fuentes.json').read_text(encoding='utf-8'))
revision['economic_highlights'] = {}
for key, name, source in [('income','ingresos_BIT_2024_2025.csv',sources[0]),('gdp','pib_TyR_2024_2025_T4.csv',sources[1])]:
    revision['economic_highlights'][key] = {
        'year':2025, 'publication_page':8, 'workbook_row':4 if key=='income' else 5,
        'data_file':f'data/manual/editorial/{name}',
        'data_sha256':hashlib.sha256((folder/name).read_bytes()).hexdigest(),
        'source_url':source['url'], 'original_source_sha256':source['sha256'],
        'verified_on':'2026-10-12',
    }
payload['slots']['INTRODUCCION_1'] = title + '\n\n' + body
payload['slots']['INTRODUCCION_2'] = sheet.cell(3,5).value.strip()
registry.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Dos textos y dos cálculos de 2025 registrados sin alterar las correcciones anteriores.')
