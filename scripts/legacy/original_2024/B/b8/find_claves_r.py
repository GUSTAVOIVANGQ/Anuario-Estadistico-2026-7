import os
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", 'datos', 'A.7', 'datos_abiertos', 'conjunto_de_datos_gastoshogar_enigh2022_ns', 'catalogos')
df = pd.read_csv(os.path.join(BASE, 'gastos.csv'), encoding='latin-1')

# Buscamos claves R
matching = df[df.iloc[:, 0].str.startswith('R', na=False)]

with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", 'claves_R.txt'), 'w', encoding='utf-8') as f:
    f.write(matching.to_string())
