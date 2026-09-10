import os

import pandas as pd
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", 'datos', 'A.7', 'microdatos')

conc = pd.read_csv(os.path.join(BASE, 'concentradohogar.csv'), usecols=['folioviv', 'foliohog', 'ing_cor', 'factor', 'comunica'])
hog = pd.read_csv(os.path.join(BASE, 'hogares.csv'), usecols=['folioviv', 'foliohog', 'telefono', 'celular', 'tv_paga', 'conex_inte'])

gh = pd.read_csv(os.path.join(BASE, 'gastoshogar.csv'), usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri', 'gas_nm_tri'])
gp = pd.read_csv(os.path.join(BASE, 'gastospersona.csv'), usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri'])

gh['gasto'] = pd.to_numeric(gh['gasto_tri'], errors='coerce').fillna(0) + pd.to_numeric(gh['gas_nm_tri'], errors='coerce').fillna(0)
gp['gasto'] = pd.to_numeric(gp['gasto_tri'], errors='coerce').fillna(0)

todas = pd.concat([gh[['folioviv', 'foliohog', 'clave', 'gasto']], gp[['folioviv', 'foliohog', 'clave', 'gasto']]])

fijas_claves = ['E001', 'E003', 'E004', 'E005']
gf = todas[todas['clave'].isin(fijas_claves)].groupby(['folioviv', 'foliohog'])['gasto'].sum().reset_index()
gf.columns = ['folioviv', 'foliohog', 'gasto_fijas']

df = conc.merge(hog, on=['folioviv', 'foliohog'], how='left')
df = df.merge(gf, on=['folioviv', 'foliohog'], how='left')
df['gasto_fijas'] = df['gasto_fijas'].fillna(0)

df = df.sort_values('ing_cor').reset_index(drop=True)
df['cum_factor'] = df['factor'].cumsum()
df['pct_cum'] = df['cum_factor'] / df['factor'].sum()
df['decil'] = pd.cut(df['pct_cum'], bins=np.linspace(0, 1, 11), labels=range(1, 11), include_lowest=True).astype(int)

df['tiene_fijas'] = ((df['telefono'] == 1) | (df['conex_inte'] == 1) | (df['tv_paga'] == 1)).astype(int)

with open(os.path.join(os.path.dirname(__file__), 'res.txt'), 'w', encoding='utf-8') as f:
    f.write("=== METODO 1: Solo gasto_fijas > 0 ===\n")
    for d in range(1, 11):
        sub = df[(df['decil'] == d) & (df['tiene_fijas'] == 1) & (df['gasto_fijas'] > 0)]
        w = sub['factor']
        gasto_mensual = (sub['gasto_fijas'] * w).sum() / w.sum() / 3
        ingreso_mensual = (sub['ing_cor'] * w).sum() / w.sum() / 3
        pct = (gasto_mensual / ingreso_mensual) * 100
        f.write(f"Decil {d}: Gasto=${gasto_mensual:.0f}, Ingreso=${ingreso_mensual:.0f}, %={pct:.1f}%\n")
    
    f.write("\n=== METODO 2: comunica > 0 ===\n")
    for d in range(1, 11):
        sub = df[(df['decil'] == d) & (df['tiene_fijas'] == 1) & (df['comunica'] > 0)]
        w = sub['factor']
        gasto_mensual = (sub['gasto_fijas'] * w).sum() / w.sum() / 3
        ingreso_mensual = (sub['ing_cor'] * w).sum() / w.sum() / 3
        pct = (gasto_mensual / ingreso_mensual) * 100
        f.write(f"Decil {d}: Gasto=${gasto_mensual:.0f}, Ingreso=${ingreso_mensual:.0f}, %={pct:.1f}%\n")

