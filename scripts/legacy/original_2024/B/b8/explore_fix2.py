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

# Let's look at Decil 1 gasto_fijas > 0
sub1 = df[(df['decil'] == 1) & (df['gasto_fijas'] > 0)]
print("--- Decil 1: Gasto Fijas > 0 ---")
print("Contador de hogares:", len(sub1))
print("Gasto promedio trimestral (sin div 3): $", (sub1['gasto_fijas'] * sub1['factor']).sum() / sub1['factor'].sum())
print("Gasto mensual promedio ponderado: $", (sub1['gasto_fijas'] * sub1['factor']).sum() / sub1['factor'].sum() / 3)
print("Distribucion del gasto_fijas trimestral (sin ponderar):")
print(sub1['gasto_fijas'].describe())

print("\nVerificando los cuantiles de gasto_fijas para todos los gastos en fijas (hogares con >0):")
print(df[df['gasto_fijas']>0]['gasto_fijas'].describe())

# Check Decil 10
sub10 = df[(df['decil'] == 10) & (df['gasto_fijas'] > 0)]
print("\n--- Decil 10: Gasto Fijas > 0 ---")
print("Gasto mensual promedio ponderado: $", (sub10['gasto_fijas'] * sub10['factor']).sum() / sub10['factor'].sum() / 3)
