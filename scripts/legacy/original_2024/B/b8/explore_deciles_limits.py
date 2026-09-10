import os
import pandas as pd
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", 'datos', 'A.7', 'microdatos')

conc = pd.read_csv(os.path.join(BASE, 'concentradohogar.csv'), usecols=['folioviv', 'foliohog', 'ing_cor', 'factor'])
df = conc.sort_values('ing_cor').reset_index(drop=True)
df['pct_cum'] = df['factor'].cumsum() / df['factor'].sum()
df['decil'] = pd.cut(df['pct_cum'], bins=np.linspace(0, 1, 11), labels=range(1, 11), include_lowest=True).astype(int)

with open(os.path.join(os.path.dirname(__file__), 'limits_out.txt'), 'w', encoding='utf-8') as f:
    f.write("--- Límites superiores de Ingreso Corriente Trimestral por Decil ---\n")
    f.write(df.groupby('decil')['ing_cor'].max().to_string() + "\n\n")

    f.write("--- Media de Ingreso Corriente Trimestral por Decil ---\n")
    media = df.groupby('decil').apply(lambda x: (x['ing_cor']*x['factor']).sum() / x['factor'].sum())
    f.write(media.to_string() + "\n\n")

    f.write("--- Valores de otras columnas en hogares.csv ---\n")
    hog = pd.read_csv(os.path.join(BASE, 'hogares.csv'), nrows=1000)
    cols = [c for c in hog.columns if 'tv' in c.lower() or 'telef' in c.lower() or 'inte' in c.lower() or 'paga' in c.lower() or 'internet' in c.lower()]
    f.write(str(cols) + "\n")
