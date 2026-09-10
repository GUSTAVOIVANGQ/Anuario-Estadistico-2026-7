import os
import pandas as pd
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", 'datos', 'A.7', 'microdatos')

conc = pd.read_csv(os.path.join(BASE, 'concentradohogar.csv'), usecols=['folioviv', 'foliohog', 'ing_cor', 'factor', 'comunica'])
gh = pd.read_csv(os.path.join(BASE, 'gastoshogar.csv'), usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri', 'gas_nm_tri'])
gp = pd.read_csv(os.path.join(BASE, 'gastospersona.csv'), usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri'])

gh['gasto'] = pd.to_numeric(gh['gasto_tri'], errors='coerce').fillna(0) + pd.to_numeric(gh['gas_nm_tri'], errors='coerce').fillna(0)
gp['gasto'] = pd.to_numeric(gp['gasto_tri'], errors='coerce').fillna(0)

todas = pd.concat([gh[['folioviv', 'foliohog', 'clave', 'gasto']], gp[['folioviv', 'foliohog', 'clave', 'gasto']]])

# Claves fijas
todas_fijas = todas[todas['clave'].isin(['E001', 'E003', 'E004', 'E005'])]
gf = todas_fijas.groupby(['folioviv', 'foliohog'])['gasto'].sum().reset_index()
gf.columns = ['folioviv', 'foliohog', 'gasto_fijas']

df = conc.merge(gf, on=['folioviv', 'foliohog'], how='left')
df['gasto_fijas'] = pd.to_numeric(df['gasto_fijas'], errors='coerce').fillna(0)

df = df.sort_values('ing_cor').reset_index(drop=True)
df['pct_cum'] = df['factor'].cumsum() / df['factor'].sum()
df['decil'] = pd.cut(df['pct_cum'], bins=np.linspace(0, 1, 11), labels=range(1, 11), include_lowest=True).astype(int)

res = []
sub1 = df[(df['decil'] == 1) & (df['gasto_fijas'] > 0)]
g1 = (sub1['gasto_fijas'] * sub1['factor']).sum() / sub1['factor'].sum() / 3
res.append(f"Decil 1 Gasto Medio ponderado mensual: ${g1:.2f}")

sub10 = df[(df['decil'] == 10) & (df['gasto_fijas'] > 0)]
g10 = (sub10['gasto_fijas'] * sub10['factor']).sum() / sub10['factor'].sum() / 3
res.append(f"Decil 10 Gasto Medio ponderado mensual: ${g10:.2f}")

with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", 'res_final.txt'), 'w', encoding='utf-8') as f:
    f.write("\n".join(res))
