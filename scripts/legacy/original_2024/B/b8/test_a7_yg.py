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

# Combinations of Fijas
gf_all = todas[todas['clave'].isin(['R005', 'R006', 'R008', 'R009', 'R010', 'R011'])].groupby(['folioviv', 'foliohog'])['gasto'].sum().reset_index()
gf_all.columns = ['folioviv', 'foliohog', 'gasto_all']

gf_notv = todas[todas['clave'].isin(['R005', 'R006', 'R008', 'R010', 'R011'])].groupby(['folioviv', 'foliohog'])['gasto'].sum().reset_index()
gf_notv.columns = ['folioviv', 'foliohog', 'gasto_notv']

df = conc.merge(hog, on=['folioviv', 'foliohog'], how='left')
df = df.merge(gf_all, on=['folioviv', 'foliohog'], how='left')
df = df.merge(gf_notv, on=['folioviv', 'foliohog'], how='left')
df['gasto_all'] = df['gasto_all'].fillna(0)
df['gasto_notv'] = df['gasto_notv'].fillna(0)

df = df.sort_values('ing_cor').reset_index(drop=True)
df['pct_cum'] = df['factor'].cumsum() / df['factor'].sum()
df['decil'] = pd.cut(df['pct_cum'], bins=np.linspace(0, 1, 11), labels=range(1, 11), include_lowest=True).astype(int)

# "Hogares con telecomunicaciones fijas" (Target: 35.1%)
# Could it be just (telefono==1) | (conex_inte==1) | (gasto_all>0) -> Excluding TV from definition?
df['t1'] = ((df['telefono'] == 1) | (df['conex_inte'] == 1) | (df['tv_paga'] == 1) | (df['gasto_all'] > 0)).astype(int)
df['t2'] = ((df['telefono'] == 1) | (df['conex_inte'] == 1) | (df['tv_paga'] == 1)).astype(int)

# "Hogares que disponen y gastan" (Target: 24.7%)
df['yg1'] = ((df['t1'] == 1) & (df['gasto_all'] > 0)).astype(int)
df['yg2'] = ((df['t2'] == 1) & (df['gasto_all'] > 0)).astype(int)
df['yg3'] = ((df['t2'] == 1) & (df['gasto_notv'] > 0)).astype(int)
df['yg4'] = ((df['t2'] == 1) & (df['comunica'] > 0)).astype(int)

# New idea: maybe "gastan en telecomunicaciones fijas" means their 'gasto_all' > 0 AND 'comunica' > 0? No makes zero sense.
# What if it's Gasto > 0 but ONLY from gastoshogar, not gastospersona? (Telecom bills are rarely paid as personal expenses but sometimes they are).
gh_only = gh[gh['clave'].isin(['R005', 'R006', 'R008', 'R009', 'R010', 'R011'])].groupby(['folioviv', 'foliohog'])['gasto'].sum().reset_index()
gh_only.columns = ['folioviv', 'foliohog', 'gasto_gh_only']
df = df.merge(gh_only, on=['folioviv', 'foliohog'], how='left')
df['gasto_gh_only'] = df['gasto_gh_only'].fillna(0)
df['yg5'] = ((df['t2'] == 1) & (df['gasto_gh_only'] > 0)).astype(int)

res = []
for d in [1, 5, 10]:
    sub = df[df['decil'] == d]
    tot = sub['factor'].sum()
    
    t1_p = sub[sub['t1']==1]['factor'].sum() / tot * 100
    t2_p = sub[sub['t2']==1]['factor'].sum() / tot * 100
    
    yg1_p = sub[sub['yg1']==1]['factor'].sum() / tot * 100
    yg2_p = sub[sub['yg2']==1]['factor'].sum() / tot * 100
    yg3_p = sub[sub['yg3']==1]['factor'].sum() / tot * 100
    yg4_p = sub[sub['yg4']==1]['factor'].sum() / tot * 100
    yg5_p = sub[sub['yg5']==1]['factor'].sum() / tot * 100

    res.append(f"D{d} | T1(Amp): {t1_p:.1f}% | T2(Eq): {t2_p:.1f}% || YG1(Amp_All): {yg1_p:.1f}% | YG2(Eq_All): {yg2_p:.1f}% | YG3(Eq_NoTV): {yg3_p:.1f}% | YG4(Eq_Comunica): {yg4_p:.1f}% | YG5(Eq_GHonly): {yg5_p:.1f}%")

with open(os.path.join(os.path.dirname(__file__), 'a7_test_yg.txt'), 'w', encoding='utf-8') as f:
    f.write("\n".join(res))
