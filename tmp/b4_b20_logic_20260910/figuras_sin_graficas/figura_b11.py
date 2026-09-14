# -*- coding: utf-8 -*-
"""
Figura B.11 — Accesos del Servicio Fijo de Internet (2000-actual)

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

# ── 1. Cargar datos ───────────────────────────────────────────────────────────
DATA_PATH = ensure_bit_table("TD_ACC_INTER_HIS_ITE_VA.csv", "B.11")
df = read_csv_flexible(DATA_PATH)
df["MES"] = numeric(df["MES"])
df["ANIO"] = numeric(df["ANIO"])
df["A_TOTAL_E"] = numeric(df["A_TOTAL_E"])
ULTIMO_ANIO = latest_december_year(df)
df_dic = df[df["MES"] == 12].groupby("ANIO")["A_TOTAL_E"].sum().reset_index()
df_plot = df_dic[(df_dic["ANIO"] >= 2000) & (df_dic["ANIO"] <= ULTIMO_ANIO)].reset_index(drop=True)
save_audit("B.11", df_plot)

# ── 2. Imprimir resultados usados para la figura ──────────────────────────────
print(f"Figura B.11. Accesos del Servicio Fijo de Internet (2000-{ULTIMO_ANIO})")
print("\nValores calculados (accesos totales, diciembre de cada año):")
print(df_plot.to_string(index=False))
