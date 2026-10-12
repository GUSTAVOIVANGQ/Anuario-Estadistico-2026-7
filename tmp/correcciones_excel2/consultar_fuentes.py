from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import urllib.request

root = Path(__file__).parent
sources = [
    ('ingresos_BIT.csv', 'https://bit.crt.gob.mx/descargas/datos/tabs/TD_INGRESOS_TELECOM_ITE_VA.csv'),
    ('PIBT_2.xlsx', 'https://www.inegi.org.mx/contenidos/programas/pib/2018/tabulados/ori/PIBT_2.xlsx'),
]

def fetch(item):
    name, url = item
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'AnuarioEstadistico2026/0.30'})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
            final_url = response.url
        (root / name).write_bytes(data)
        return {'file': name, 'url': final_url, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    except Exception as error:
        return {'file': name, 'url': url, 'error': str(error)}

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(fetch, sources))
(root / 'fuentes.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps(results, indent=2))
