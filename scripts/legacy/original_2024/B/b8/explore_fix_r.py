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

# Claves correctas de telecomunicaciones fijas (ENIGH 2022)
fijas_claves = ['R005', 'R006', 'R008', 'R009', 'R010', 'R011']
gf = todas[todas['clave'].isin(fijas_claves)].groupby(['folioviv', 'foliohog'])['gasto'].sum().reset_index()
gf.columns = ['folioviv', 'foliohog', 'gasto_fijas']

df = conc.merge(gf, on=['folioviv', 'foliohog'], how='left')
df['gasto_fijas'] = pd.to_numeric(df['gasto_fijas'], errors='coerce').fillna(0)

# Deciles
df = df.sort_values('ing_cor').reset_index(drop=True)
df['pct_cum'] = df['factor'].cumsum() / df['factor'].sum()
df['decil'] = pd.cut(df['pct_cum'], bins=np.linspace(0, 1, 11), labels=range(1, 11), include_lowest=True).astype(int)

hog = pd.read_csv(os.path.join(BASE, 'hogares.csv'), usecols=['folioviv', 'foliohog', 'telefono', 'celular', 'tv_paga', 'conex_inte'])
df = df.merge(hog, on=['folioviv', 'foliohog'], how='left')
df['tiene_fijas'] = ((df['telefono'] == 1) | (df['conex_inte'] == 1) | (df['tv_paga'] == 1)).astype(int)

res = []
for d in range(1, 11):
    # La nota dice: promedio para hogares que "disponen del servicio y gastan en él"
    sub = df[(df['decil'] == d) & (df['tiene_fijas'] == 1) & (df['gasto_fijas'] > 0)]
    if len(sub) > 0:
        gasto_mensual = (sub['gasto_fijas'] * sub['factor']).sum() / sub['factor'].sum() / 3
        ingr_mensual = (sub['ing_cor'] * sub['factor']).sum() / sub['factor'].sum() / 3
        pct = (gasto_mensual / ingr_mensual) * 100
        res.append(f"Decil {d}: Gasto=${gasto_mensual:.0f}, %={pct:.1f}%")

with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", 'res_correcto.txt'), 'w', encoding='utf-8') as f:
    f.write("\n".join(res))
