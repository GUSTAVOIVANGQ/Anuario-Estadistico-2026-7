import json
from pathlib import Path
import openpyxl

root = Path(__file__).resolve().parents[2]
path = root / 'assets/presentation/textos_editoriales_2026.json'
payload = json.loads(path.read_text(encoding='utf-8'))
sheet = openpyxl.load_workbook(
    'C:/Users/gustavo.garcia/Downloads/Anuario_mejoras.xlsx', data_only=True
).active
sections = {}
keys = ['fundamento', 'personas_usuarias', 'tic', 'genero', 'radio_tv', 'nielsen']
for row, key in enumerate(keys, 2):
    text = sheet.cell(row, 5).value.strip().replace('telecomunicaciones ,', 'telecomunicaciones,')
    if key == 'fundamento':
        title, body = 'Fundamento legal', text
    else:
        title, body = text.split('\n\n', 1)
    sections[key] = {'title': title, 'body': body, 'workbook_row': row}
gemini = ('GEMINI: Asistente de inteligencia artificial generativa de Google '
          'para responder preguntas y crear contenido.')
payload['publication_revision'] = {
    'version': 1,
    'source_workbook': 'Anuario_mejoras.xlsx',
    'source_sheet': sheet.title,
    'legal_sections': sections,
    'omitted_template_pages': [4],
    'gemini_definition': gemini,
    'gemini_source': 'https://blog.google/intl/es-419/actualizaciones-de-producto/informacion/bard-se-convierte-en-gemini-ultra-10-y-una-nueva-aplicacion-movil/',
}
payload['slots']['LEGALES_1'] = '\n\n'.join(
    entry['title'] + '\n\n' + entry['body'] for entry in sections.values()
)
for key, value in payload['slots'].items():
    value = value.replace('Coordinación General de Planeación Estratégica', 'Dirección General de Planeación').replace('CGPE', 'DGP')
    if key == 'GLOSARIO_1_A':
        value = '\n'.join(gemini if line.startswith('BARD DE GOOGLE:') else line
                          for line in value.splitlines())
    payload['slots'][key] = value
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Seis textos importados del Excel y tres correcciones registradas.')
