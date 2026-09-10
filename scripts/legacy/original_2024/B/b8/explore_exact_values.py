import os
import pandas as pd
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", 'datos', 'A.7', 'microdatos')

print("Loading concentradohogar...")
conc = pd.read_csv(os.path.join(BASE, 'concentradohogar.csv'), usecols=['folioviv', 'foliohog', 'ing_cor', 'factor', 'comunica'])
print("Loading hogares...")
hog = pd.read_csv(os.path.join(BASE, 'hogares.csv'), usecols=['folioviv', 'foliohog', 'telefono', 'celular', 'tv_paga', 'conex_inte'])

print("Loading gastoshogar...")
gh = pd.read_csv(os.path.join(BASE, 'gastoshogar.csv'), usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri', 'gas_nm_tri'])
print("Loading gastospersona...")
gp = pd.read_csv(os.path.join(BASE, 'gastospersona.csv'), usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri'])

gh['gasto_tri'] = pd.to_numeric(gh['gasto_tri'], errors='coerce').fillna(0)
gh['gas_nm_tri'] = pd.to_numeric(gh['gas_nm_tri'], errors='coerce').fillna(0)
gh['gasto_total'] = gh['gasto_tri'] + gh['gas_nm_tri']

gp['gasto_tri'] = pd.to_numeric(gp['gasto_tri'], errors='coerce').fillna(0)
gp['gasto_total'] = gp['gasto_tri']

all_gasto = pd.concat([gh[['folioviv', 'foliohog', 'clave', 'gasto_total']], gp[['folioviv', 'foliohog', 'clave', 'gasto_total']]])

# We want fixed telecom:
fijas_claves = ['E001', 'E003', 'E004', 'E005']
# Mobile:
movil_claves = ['E002', 'E016'] # E002 is celular, what about others?

gasto_fijas = all_gasto[all_gasto['clave'].isin(fijas_claves)].groupby(['folioviv', 'foliohog'])['gasto_total'].sum().reset_index()
gasto_fijas.columns = ['folioviv', 'foliohog', 'gfijas_tri']

df = conc.merge(hog, on=['folioviv', 'foliohog'])
df = df.merge(gasto_fijas, on=['folioviv', 'foliohog'], how='left')
df['gfijas_tri'] = df['gfijas_tri'].fillna(0)

# Calculate deciles base on ing_cor
df = df.sort_values('ing_cor').reset_index(drop=True)
df['cum_factor'] = df['factor'].cumsum()
df['pct_cum'] = df['cum_factor'] / df['factor'].sum()
df['decil'] = pd.cut(df['pct_cum'], bins=np.linspace(0, 1, 11), labels=range(1, 11), include_lowest=True).astype(int)

# Indicators
df['tiene_fija'] = ((df['telefono'] == 1) | (df['tv_paga'] == 1) | (df['conex_inte'] == 1)).astype(int)
df['gasta_fija'] = (df['gfijas_tri'] > 0).astype(int)
df['tiene_y_gasta'] = ((df['tiene_fija'] == 1) & (df['gasta_fija'] == 1)).astype(int)

print("\n--- Hypothesis 1: Exact matches for Decil 1 and 10 using my definitions ---")
for d in [1, 10]:
    sub = df[(df['decil'] == d) & (df['tiene_y_gasta'] == 1)]
    w = sub['factor']
    
    gasto_tri_pond = (sub['gfijas_tri'] * w).sum() / w.sum()
    ing_cor_tri_pond = (sub['ing_cor'] * w).sum() / w.sum()
    
    g_mensual = gasto_tri_pond / 3
    i_mensual = ing_cor_tri_pond / 3
    
    pct = (g_mensual / i_mensual) * 100
    
    print(f"Decil {d}: G_Mensual=${g_mensual:.1f}, I_Mensual=${i_mensual:.1f}, %={pct:.1f}%")

print("\n--- Hypothesis 2: Using 'comunica' instead of specific Fijas ---")
for d in [1, 10]:
    sub = df[(df['decil'] == d) & (df['comunica'] > 0) & (df['tiene_fija'] == 1)]
    w = sub['factor']
    
    gasto_tri_pond = (sub['comunica'] * w).sum() / w.sum()
    ing_cor_tri_pond = (sub['ing_cor'] * w).sum() / w.sum()
    
    g_mensual = gasto_tri_pond / 3
    i_mensual = ing_cor_tri_pond / 3
    
    val1 = (g_mensual / i_mensual) * 100
    print(f"Decil {d} (comunica/3): G_Mensual=${g_mensual:.1f}, %={val1:.1f}%")

print("\n--- Hypothesis 3: Denominator represents ALL households in the decil (not just those who spend) ---")
for d in [1, 10]:
    sub = df[df['decil'] == d]
    w = sub['factor']
    
    gasto_tri_pond = (sub['gfijas_tri'] * w).sum() / w.sum()
    ing_cor_tri_pond = (sub['ing_cor'] * w).sum() / w.sum()
    
    g_mensual = gasto_tri_pond / 3
    i_mensual = ing_cor_tri_pond / 3
    
    pct = (g_mensual / i_mensual) * 100
    
    print(f"Decil {d}: G_Mensual_All=${g_mensual:.1f}, %={pct:.1f}%")
