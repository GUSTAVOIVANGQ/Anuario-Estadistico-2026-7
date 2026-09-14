#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figura B.9 — Participación de mercado del Servicio Fijo de Telefonía (serie desde 2013)

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

# ── 1. LECTURA Y LIMPIEZA ──
data_file = ensure_bit_table("TD_MARKET_SHARE_TELFIJA_ITE_VA.csv", "B.9")
df = read_csv_flexible(data_file)
df["ANIO"] = numeric(df["ANIO"])
df["MES"] = numeric(df["MES"])
df["MARKET_SHARE"] = numeric(df["MARKET_SHARE"])
ULTIMO_ANIO = latest_december_year(df)

# ── 2. FILTRO ──
df_dic = df[(df["MES"] == 12) & (df["ANIO"].between(2013, ULTIMO_ANIO))].copy()

# ── 3. MAPEO ──
mapeo = {
    "AMÉRICA MÓVIL":  "América Móvil",
    "GRUPO TELEVISA": "Grupo Televisa",
    "MEGACABLE-MCM":  "Megacable-MCM",
    "GRUPO SALINAS":  "Grupo Salinas",
    "AXTEL":          "Axtel",
    "TELEFÓNICA":     "Telefónica",
}
df_dic["GRUPO_FIGURA"] = df_dic["GRUPO"].map(mapeo).fillna("Otros")

# ── 4. PIVOTE ──
pivot = df_dic.groupby(["ANIO", "GRUPO_FIGURA"])["MARKET_SHARE"].sum().unstack(fill_value=0)

orden = [
    "América Móvil", "Grupo Televisa", "Megacable-MCM",
    "Grupo Salinas", "Axtel", "Telefónica", "Otros"
]
pivot = pivot.reindex(columns=orden, fill_value=0)
years = pivot.index.astype(int).tolist()
save_audit("B.9", pivot.reset_index())

# ── 5. Imprimir resultados usados para la figura ──────────────────────────────
print(f"Figura B.9. Participación de mercado del Servicio Fijo de Telefonía (2013-{ULTIMO_ANIO})")
print("\nParticipación de mercado (%) por grupo y año:")
print(pivot.to_string())
