import os
import pandas as pd
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", 'datos', 'A.7', 'microdatos')

conc = pd.read_csv(os.path.join(BASE, 'concentradohogar.csv'), usecols=['folioviv', 'foliohog', 'ing_cor', 'factor'])
hog = pd.read_csv(os.path.join(BASE, 'hogares.csv'), usecols=['folioviv', 'foliohog', 'telefono', 'celular', 'tv_paga', 'conex_inte'])

gh = pd.read_csv(os.path.join(BASE, 'gastoshogar.csv'), usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri', 'gas_nm_tri'])
gp = pd.read_csv(os.path.join(BASE, 'gastospersona.csv'), usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri'])

gh['gasto'] = pd.to_numeric(gh['gasto_tri'], errors='coerce').fillna(0) + pd.to_numeric(gh['gas_nm_tri'], errors='coerce').fillna(0)
gp['gasto'] = pd.to_numeric(gp['gasto_tri'], errors='coerce').fillna(0)

todas = pd.concat([gh[['folioviv', 'foliohog', 'clave', 'gasto']], gp[['folioviv', 'foliohog', 'clave', 'gasto']]])

# Claves correctas de telecomunicaciones fijas
fijas_claves = ['R005', 'R006', 'R008', 'R009', 'R010', 'R011']
gf = todas[todas['clave'].isin(fijas_claves)].groupby(['folioviv', 'foliohog'])['gasto'].sum().reset_index()
gf.columns = ['folioviv', 'foliohog', 'gasto_fijas']

df = conc.merge(hog, on=['folioviv', 'foliohog'], how='left')
df = df.merge(gf, on=['folioviv', 'foliohog'], how='left')
df['gasto_fijas'] = df['gasto_fijas'].fillna(0)

df = df.sort_values('ing_cor').reset_index(drop=True)
df['pct_cum'] = df['factor'].cumsum() / df['factor'].sum()
df['decil'] = pd.cut(df['pct_cum'], bins=np.linspace(0, 1, 11), labels=range(1, 11), include_lowest=True).astype(int)

# 1. Sólo por equipamiento
df['tiene_equipo'] = ((df['telefono'] == 1) | (df['conex_inte'] == 1) | (df['tv_paga'] == 1)).astype(int)

# 2. Por equipamiento O por gasto
df['tiene_ampliado'] = ((df['tiene_equipo'] == 1) | (df['gasto_fijas'] > 0)).astype(int)

# 3. Disponen y Gasta
df['tiene_y_gasta'] = ((df['tiene_equipo'] == 1) & (df['gasto_fijas'] > 0)).astype(int)

# 4. Disponen y Gasta (Ampliado) -> Básicamente los que gastan
df['tiene_y_gasta_amp'] = ((df['tiene_ampliado'] == 1) & (df['gasto_fijas'] > 0)).astype(int)

res = []
for d in range(1, 11):
    sub = df[df['decil'] == d]
    tot = sub['factor'].sum()
    
    p_eq = sub[sub['tiene_equipo'] == 1]['factor'].sum() / tot * 100
    p_amp = sub[sub['tiene_ampliado'] == 1]['factor'].sum() / tot * 100
    p_yg = sub[sub['tiene_y_gasta'] == 1]['factor'].sum() / tot * 100
    p_yg_amp = sub[sub['tiene_y_gasta_amp'] == 1]['factor'].sum() / tot * 100

    res.append(f"Decil {d:>2} | Eq: {p_eq:.1f}% | Amp: {p_amp:.1f}% || YG_Eq: {p_yg:.1f}% | YG_Amp: {p_yg_amp:.1f}%")

with open(os.path.join(os.path.dirname(__file__), 'a7_test_amp.txt'), 'w', encoding='utf-8') as f:
    f.write("\n".join(res))
