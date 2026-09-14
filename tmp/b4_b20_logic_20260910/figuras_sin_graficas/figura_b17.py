# -*- coding: utf-8 -*-
"""
Figura B.17 — Participación de mercado del servicio fijo de Internet (2013-actual)

Versión SIN generación de gráfica: calcula los mismos datos que alimentan
la figura original y los imprime en consola.
"""
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _bit_crt_common import (
    ROOT as PROJECT_ROOT, OUTPUT_DIR as PROJECT_OUTPUT_DIR,
    ensure_bit_table, ensure_bit_table_any, ensure_geojson,
    latest_december_year, read_csv_flexible, numeric, save_audit,
)

# ─── Rutas ────────────────────────────────────────────────────────────────────────
INPUT = ensure_bit_table("TD_MARKET_SHARE_BAF_ITE_VA.csv", "B.17")

# --- Cargar y limpiar ---
df = read_csv_flexible(INPUT)

df['MS'] = numeric(df['MARKET_SHARE'])
df['ANIO'] = numeric(df['ANIO'])
df['MES'] = numeric(df['MES'])
ULTIMO_ANIO = latest_december_year(df)

df_dic = df[(df['MES'] == 12) & (df['ANIO'] >= 2013) & (df['ANIO'] <= ULTIMO_ANIO)].copy()

# --- Mapeo a Grupos Institucionales ---
def asignar_grupo(nombre):
    n = str(nombre).upper()
    if 'MÓVIL' in n or 'MOVIL' in n or 'MÃ“VIL' in n or 'TELMEX' in n or 'CABLEMAS' in n or 'TELNOR' in n:
        return 'América Móvil'
    if 'TELEVISA' in n or 'CABLEVISION' in n:
        return 'Grupo Televisa'
    if 'MEGACABLE' in n:
        return 'Megacable-MCM'
    if 'SALINAS' in n or 'TOTALPLAY' in n:
        return 'Grupo Salinas'
    if 'AXTEL' in n:
        return 'Axtel'
    if 'MAXCOM' in n:
        return 'Maxcom'
    if 'CABLECOM' in n:
        return 'Cablecom'
    if nombre == 'IST':
        return 'IST'
    return 'Otros'

df_dic['GRUPO_AGR'] = df_dic['GRUPO'].apply(asignar_grupo)

pivot = df_dic.groupby(['ANIO', 'GRUPO_AGR'])['MS'].sum().unstack(fill_value=0)
pivot.index = pivot.index.astype(int)
save_audit("B.17", pivot.reset_index())

# ─── Imprimir resultados usados para la figura ─────────────────────────────────────
print(f"Figura B.17. Participación de mercado del servicio fijo de Internet (2013-{ULTIMO_ANIO})")
print("\nParticipación de mercado (%) por grupo y año:")
print(pivot.to_string())
