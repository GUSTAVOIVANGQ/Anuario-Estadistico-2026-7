import pandas as pd
import numpy as np
import sys

# -- RUTAS -- ajusta según donde tengas los archivos
PATH_CONCENTRADO = r"C:\Users\ivan-\Documents\GitHub\anuario\scripts\a7\concentradohogar.csv"
PATH_HOGARES     = r"C:\Users\ivan-\Documents\GitHub\anuario\scripts\a7\hogares.csv"

# -- CARGA ------------------------------------------
cols_conc = ['folioviv','foliohog','ing_cor','comunica','factor','tot_integ']
cols_hog  = ['folioviv','foliohog','telefono','tv_paga','conex_inte']

conc = pd.read_csv(PATH_CONCENTRADO, usecols=cols_conc)
hog  = pd.read_csv(PATH_HOGARES,     usecols=cols_hog)

# -- MERGE ------------------------------------------
df = conc.merge(hog, on=['folioviv','foliohog'], how='left')

# -- DECIL PONDERADO --------------------------------
# Ingreso per cápita corriente
df['ing_pc'] = df['ing_cor'] / df['tot_integ'].replace(0, np.nan)

# Ordenar por ingreso per cápita
df = df.sort_values('ing_pc').reset_index(drop=True)

# Acumular factor de expansión y asignar decil (10 grupos de 10% c/u)
df['cum_factor'] = df['factor'].cumsum()
total_factor = df['factor'].sum()

df['decil'] = pd.cut(
    df['cum_factor'],
    bins=[i * total_factor / 10 for i in range(11)],
    labels=range(1, 11),
    include_lowest=True
)
df['decil'] = df['decil'].astype(int)

# -- VARIABLES DE TELECOMUNICACIONES FIJAS ----------
# Serie AZUL: hogar TIENE al menos un servicio fijo
#   telefono==1 OR tv_paga==1 OR conex_inte==1
df['tiene_telecom'] = (
    (df['telefono']  == 1) |
    (df['tv_paga']   == 1) |
    (df['conex_inte']== 1)
).astype(int)

# Serie NARANJA: tiene Y además gastó (comunica > 0)
df['tiene_y_gasta'] = (
    (df['tiene_telecom'] == 1) &
    (df['comunica'] > 0)
).astype(int)

# -- CÁLCULO PONDERADO POR DECIL --------------------
def pct_ponderado(grp, var):
    return np.average(grp[var], weights=grp['factor']) * 100

resultado = df.groupby('decil').apply(
    lambda g: pd.Series({
        'pct_tiene_telecom': pct_ponderado(g, 'tiene_telecom'),
        'pct_tiene_y_gasta': pct_ponderado(g, 'tiene_y_gasta'),
        'n_hogares_expandidos': g['factor'].sum()
    })
).reset_index()

print("\n=== FIGURA A.7 - Cálculo desde microdatos ENIGH 2022 ===\n")
print(f"{'Decil':<8} {'%Con telecom (azul)':<25} {'%Disponen y gastan (naranja)':<30}")
print("-"*65)
for _, row in resultado.iterrows():
    print(f"  {int(row['decil']):<6} {row['pct_tiene_telecom']:>20.1f}%  {row['pct_tiene_y_gasta']:>25.1f}%")

print("\n-- Valores esperados según Figura A.7 del Anuario --")
esperado_azul   = [35.1,50.3,59.8,68.0,75.2,80.3,85.5,90.2,93.4,97.2]
esperado_naranja= [24.7,38.4,48.6,57.7,65.0,70.9,77.2,83.6,87.5,93.2]
print(f"{'Decil':<8} {'Esperado azul':<20} {'Esperado naranja'}")
print("-"*50)
for i,(a,n) in enumerate(zip(esperado_azul, esperado_naranja),1):
    print(f"  {i:<6} {a:>15.1f}%   {n:>15.1f}%")
