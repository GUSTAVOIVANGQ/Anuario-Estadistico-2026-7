# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", 'datos', 'A.7', 'microdatos')

conc = pd.read_csv(os.path.join(BASE, 'concentradohogar.csv'), usecols=['folioviv', 'foliohog', 'ing_cor', 'factor', 'comunica'])
hog = pd.read_csv(os.path.join(BASE, 'hogares.csv'), usecols=['folioviv', 'foliohog', 'telefono', 'celular', 'tv_paga', 'conex_inte'])

gh = pd.read_csv(os.path.join(BASE, 'gastoshogar.csv'), usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri', 'gas_nm_tri'])
gp = pd.read_csv(os.path.join(BASE, 'gastospersona.csv'), usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri'])

gh['gasto'] = pd.to_numeric(gh['gasto_tri'], errors='coerce').fillna(0) + pd.to_numeric(gh['gas_nm_tri'], errors='coerce').fillna(0)
gp['gasto'] = pd.to_numeric(gp['gasto_tri'], errors='coerce').fillna(0)

todas = pd.concat([gh[['folioviv', 'foliohog', 'clave', 'gasto']], gp[['folioviv', 'foliohog', 'clave', 'gasto']]])

# Claves correctas de telecomunicaciones fijas (ENIGH 2022 serie R)
fijas_claves = ['R005', 'R006', 'R008', 'R009', 'R010', 'R011']
gf = todas[todas['clave'].isin(fijas_claves)].groupby(['folioviv', 'foliohog'])['gasto'].sum().reset_index()
gf.columns = ['folioviv', 'foliohog', 'gasto_fijas']

df = conc.merge(hog, on=['folioviv', 'foliohog'], how='left')
df = df.merge(gf, on=['folioviv', 'foliohog'], how='left')
df['gasto_fijas'] = pd.to_numeric(df['gasto_fijas'], errors='coerce').fillna(0)

df = df.sort_values('ing_cor').reset_index(drop=True)
df['pct_cum'] = df['factor'].cumsum() / df['factor'].sum()
df['decil'] = pd.cut(df['pct_cum'], bins=np.linspace(0, 1, 11), labels=range(1, 11), include_lowest=True).astype(int)

# Tiene fijas
df['tiene_fijas'] = ((df['telefono'] == 1) | (df['conex_inte'] == 1) | (df['tv_paga'] == 1)).astype(int)

# "Tiene Y Gasta" con la definicion anterior ('comunica' > 0, incluye movil)
df['dg_comunica'] = ((df['tiene_fijas'] == 1) & (df['comunica'] > 0)).astype(int)

# "Tiene Y Gasta" con la NUEVA definicion (solo claves de fijas)
df['dg_fijas'] = ((df['tiene_fijas'] == 1) & (df['gasto_fijas'] > 0)).astype(int)


res = [
    f"{'Decil':>5} | {'% Tiene Fijas':>15} | {'% Tiene y Gasta (Comunica)':>25} | {'% Tiene y Gasta (Fijas)':>25}",
    "-" * 80
]

for d in range(1, 11):
    sub = df[df['decil'] == d]
    total_hogares = sub['factor'].sum()
    
    tiene_pct = (sub[sub['tiene_fijas'] == 1]['factor'].sum() / total_hogares) * 100
    gasta_com_pct = (sub[sub['dg_comunica'] == 1]['factor'].sum() / total_hogares) * 100
    gasta_fij_pct = (sub[sub['dg_fijas'] == 1]['factor'].sum() / total_hogares) * 100
    
    res.append(f"{d:>5} | {tiene_pct:>14.1f}% | {gasta_com_pct:>24.1f}% | {gasta_fij_pct:>24.1f}%")

with open(os.path.join(os.path.dirname(__file__), 'a7_resultados.txt'), 'w', encoding='utf-8') as f:
    f.write("\n".join(res))

