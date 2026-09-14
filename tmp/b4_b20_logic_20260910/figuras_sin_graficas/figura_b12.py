# -*- coding: utf-8 -*-
"""
Figura B.12 — Accesos del Servicio Fijo de Internet por cada 100 hogares (2000-actual)

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
DATA_PATH = ensure_bit_table("TD_PENETRACION_H_BAF_ITE_VA.csv", "B.12")
df = read_csv_flexible(DATA_PATH)
df["MES"] = numeric(df["MES"])
df["ANIO"] = numeric(df["ANIO"])
df["P_BAF_E"] = numeric(df["P_BAF_E"])
ULTIMO_ANIO = latest_december_year(df)
df_plot = df[df["MES"] == 12][["ANIO", "P_BAF_E"]].copy()
df_plot = df_plot[(df_plot["ANIO"] >= 2000) & (df_plot["ANIO"] <= ULTIMO_ANIO)].sort_values("ANIO").reset_index(drop=True)
save_audit("B.12", df_plot)

# ── 2. Imprimir resultados usados para la figura ──────────────────────────────
print(f"Figura B.12. Accesos del Servicio Fijo de Internet por cada 100 hogares (2000-{ULTIMO_ANIO})")
print("\nValores calculados (accesos por cada 100 hogares, diciembre de cada año):")
print(df_plot.to_string(index=False))
