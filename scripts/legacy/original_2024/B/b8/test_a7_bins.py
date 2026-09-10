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

df = conc.merge(hog, on=['folioviv', 'foliohog'], how='left')
df = df.merge(gf_all, on=['folioviv', 'foliohog'], how='left')
df['gasto_all'] = df['gasto_all'].fillna(0)

# BINNING CON CORTES EXACTOS DEL INEGI Y MI PREVIO QCUT (SON LOS MISMOS QUE OBTUVE ANTES)
bins = [-np.inf, 18735.24, 25881.42, 32517.37, 39447.73, 47327.94, 56680.30, 68754.08, 86372.37, 119978.95, np.inf]
df['decil'] = pd.cut(df['ing_cor'], bins=bins, labels=range(1, 11), right=True).astype(int)

# "Hogares con telecomunicaciones fijas" (Target: 35.1%)
df['t1'] = ((df['telefono'] == 1) | (df['conex_inte'] == 1) | (df['tv_paga'] == 1) | (df['gasto_all'] > 0)).astype(int)

# "Hogares que disponen y gastan" (Target: 24.7%)
df['yg1'] = ((df['t1'] == 1) & (df['gasto_all'] > 0)).astype(int)

# Also test 'comunica' > 0 for gastan
df['yg2'] = ((df['t1'] == 1) & (df['comunica'] > 0)).astype(int)

# Also test 'Eq' stringently
df['eq'] = ((df['telefono'] == 1) | (df['conex_inte'] == 1) | (df['tv_paga'] == 1)).astype(int)
df['eq_yg_all'] = ((df['eq'] == 1) & (df['gasto_all'] > 0)).astype(int)
df['eq_yg_com'] = ((df['eq'] == 1) & (df['comunica'] > 0)).astype(int)


res = []
for d in [1, 5, 10]:
    sub = df[df['decil'] == d]
    tot = sub['factor'].sum()
    
    t1_p = sub[sub['t1']==1]['factor'].sum() / tot * 100
    eq_p = sub[sub['eq']==1]['factor'].sum() / tot * 100
    
    yg1_p = sub[sub['yg1']==1]['factor'].sum() / tot * 100
    yg2_p = sub[sub['yg2']==1]['factor'].sum() / tot * 100
    eqy_p = sub[sub['eq_yg_all']==1]['factor'].sum() / tot * 100
    eqc_p = sub[sub['eq_yg_com']==1]['factor'].sum() / tot * 100

    res.append(f"D{d} | T1(Amp): {t1_p:.1f}% | Eq: {eq_p:.1f}% || YG1(Amp/All): {yg1_p:.1f}% | YG2(Amp/Comunica): {yg2_p:.1f}% | Eq_YG(All): {eqy_p:.1f}% | Eq_YG(Comunica): {eqc_p:.1f}%")

with open(os.path.join(os.path.dirname(__file__), 'a7_test_bins.txt'), 'w', encoding='utf-8') as f:
    f.write("\n".join(res))
