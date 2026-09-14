# -*- coding: utf-8 -*-
"""
Figura B.5 — Líneas del Servicio Fijo de Telefonía por cada 100 hogares (1971-actual)

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

# ── 1. Cargar datos ────────────────────────────────────────────────────────
DATA_PATH = ensure_bit_table("TD_PENETRACION_H_TELFIJA_ITE_VA.csv", "B.5")
df = read_csv_flexible(DATA_PATH)
df["ANIO"] = numeric(df["ANIO"])
df["MES"] = numeric(df["MES"])
df["P_H_TELFIJA_E"] = numeric(df["P_H_TELFIJA_E"])
ULTIMO_ANIO = latest_december_year(df)

# ── 2. Filtrar: solo diciembre (MES=12), rango histórico 1971 al último año ───
# La columna P_H_TELFIJA_E ya contiene el cálculo: líneas / 100 hogares
df_plot = df[(df['MES'] == 12) & (df['ANIO'] >= 1971) & (df['ANIO'] <= ULTIMO_ANIO)].copy()
save_audit("B.5", df_plot[["ANIO", "P_H_TELFIJA_E"]])

anios = df_plot['ANIO'].values
valores = df_plot['P_H_TELFIJA_E'].values

# ── 3. Imprimir resultados usados para la figura ──────────────────────────────
print(f"Figura B.5. Líneas del Servicio Fijo de Telefonía por cada 100 hogares (1971-{ULTIMO_ANIO})")
print("\nValores calculados (líneas por cada 100 hogares, diciembre):")
print(df_plot[['ANIO', 'P_H_TELFIJA_E']].to_string(index=False))
