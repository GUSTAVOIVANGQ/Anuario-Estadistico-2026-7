# -*- coding: utf-8 -*-
"""
Figura B.20 — Accesos del Servicio de Televisión Restringida por cada
100 hogares (1998-actual)

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

# ── 1. Leer datos ─────────────────────────────────────────────────────────────
DATA_PATH = ensure_bit_table("TD_PENETRACION_H_TVRES_ITE_VA.csv", "B.20")
df = read_csv_flexible(DATA_PATH)
df["ANIO"] = numeric(df["ANIO"])
df["MES"] = numeric(df["MES"])
df["P_H_TVRES_E"] = numeric(df["P_H_TVRES_E"])
ULTIMO_ANIO = latest_december_year(df)

# ── 2. Filtrar diciembre, rango histórico 1998 al último año ──────────────────
df_plot = (df[(df['MES'] == 12) &
              (df['ANIO'] >= 1998) &
              (df['ANIO'] <= ULTIMO_ANIO)]
           .sort_values('ANIO')
           .reset_index(drop=True))
save_audit("B.20", df_plot[["ANIO", "P_H_TVRES_E"]])

# ── 3. Imprimir resultados usados para la figura ──────────────────────────────
print(f"Figura B.20. Accesos del Servicio de Televisión Restringida por cada 100 hogares "
      f"(1998-{ULTIMO_ANIO})")
print("\nValores calculados (accesos por cada 100 hogares, diciembre de cada año):")
print(df_plot[["ANIO", "P_H_TVRES_E"]].to_string(index=False))
