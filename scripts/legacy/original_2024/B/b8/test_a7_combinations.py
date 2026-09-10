import os
import pandas as pd
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", 'datos', 'A.7', 'microdatos')

conc = pd.read_csv(os.path.join(BASE, 'concentradohogar.csv'), usecols=['folioviv', 'foliohog', 'ing_cor', 'factor'])
hog = pd.read_csv(os.path.join(BASE, 'hogares.csv'), usecols=['folioviv', 'foliohog', 'telefono', 'celular', 'tv_paga', 'conex_inte'])

df = conc.merge(hog, on=['folioviv', 'foliohog'], how='left')
df = df.sort_values('ing_cor').reset_index(drop=True)
df['pct_cum'] = df['factor'].cumsum() / df['factor'].sum()
df['decil'] = pd.cut(df['pct_cum'], bins=np.linspace(0, 1, 11), labels=range(1, 11), include_lowest=True).astype(int)

d1 = df[df['decil'] == 1]
total = d1['factor'].sum()

res = []
res.append("--- Porcentaje en Decil 1 por servicio o combinaciones ---")
p_tel = d1[d1['telefono'] == 1]['factor'].sum() / total * 100
p_tv = d1[d1['tv_paga'] == 1]['factor'].sum() / total * 100
p_int = d1[d1['conex_inte'] == 1]['factor'].sum() / total * 100
p_cel = d1[d1['celular'] == 1]['factor'].sum() / total * 100
res.append(f"Teléfono: {p_tel:.2f}%")
res.append(f"TV Paga: {p_tv:.2f}%")
res.append(f"Internet: {p_int:.2f}%")
res.append(f"Celular: {p_cel:.2f}%")

p_fijas1 = d1[(d1['telefono'] == 1) | (d1['conex_inte'] == 1) | (d1['tv_paga'] == 1)]['factor'].sum() / total * 100
res.append(f"Fijas (Tel | Int | TV): {p_fijas1:.2f}%  <-- Mi Calculo actual")

p_fijas2 = d1[(d1['telefono'] == 1) | (d1['conex_inte'] == 1)]['factor'].sum() / total * 100
res.append(f"Fijas (Tel | Int): {p_fijas2:.2f}%")

p_fijas3 = d1[(d1['conex_inte'] == 1) | (d1['tv_paga'] == 1)]['factor'].sum() / total * 100
res.append(f"Fijas (Int | TV): {p_fijas3:.2f}%")

p_fijas4 = d1[(d1['telefono'] == 1) | (d1['tv_paga'] == 1)]['factor'].sum() / total * 100
res.append(f"Fijas (Tel | TV): {p_fijas4:.2f}%")

# Maybe "telecomunicaciones fijas" means fixed telephone ONLY ? No, 35% is too high (tel is ~15-20 usually in D1). Let's see.

with open(os.path.join(os.path.dirname(__file__), 'a7_comb_out.txt'), 'w', encoding='utf-8') as f:
    f.write("\n".join(res))
