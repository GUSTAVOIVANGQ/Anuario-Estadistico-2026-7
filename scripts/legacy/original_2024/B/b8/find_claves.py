import os
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", 'datos', 'A.7', 'datos_abiertos', 'conjunto_de_datos_gastoshogar_enigh2022_ns', 'catalogos')

df = pd.read_csv(os.path.join(BASE, 'gastos.csv'), encoding='latin-1')

# Buscamos cualquier cosa relacionada con telecomunicaciones
mask = df.iloc[:, 1].str.contains('telef|internet|televis|cable|paquete|comunica|recarga|saldo', case=False, na=False)
matching = df[mask]

with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", 'telecom_claves.txt'), 'w', encoding='utf-8') as f:
    f.write(matching.to_string())
