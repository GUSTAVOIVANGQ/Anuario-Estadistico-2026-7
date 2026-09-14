# -*- coding: utf-8 -*-
"""
Figura B.18 — Herfindahl-Hirschman (IHH). Concentración de mercado
del Servicio Fijo de Internet (2013-actual)

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

# --- Cargar datos ---
INPUT = ensure_bit_table("TD_IHH_BAF_ITE_VA.csv", "B.18")
df = read_csv_flexible(INPUT)
df['IHH_BAF_E'] = numeric(df['IHH_BAF_E'])
df['ANIO'] = numeric(df['ANIO'])
df['MES'] = numeric(df['MES'])
ULTIMO_ANIO = latest_december_year(df)

df_dic = df[(df['MES'] == 12) & (df['ANIO'] >= 2013) & (df['ANIO'] <= ULTIMO_ANIO)]
df_dic = df_dic.sort_values('ANIO').reset_index(drop=True)

df_dic['IHH_plot'] = df_dic['IHH_BAF_E']
save_audit("B.18", df_dic[["ANIO", "MES", "IHH_BAF_E"]])

# ─── Imprimir resultados usados para la figura ─────────────────────────────────────
print(f"Figura B.18. Herfindahl-Hirschman (IHH). Concentración de mercado del Servicio "
      f"Fijo de Internet (2013-{ULTIMO_ANIO})")
print("\nValores calculados (IHH por año):")
print(df_dic[["ANIO", "IHH_plot"]].to_string(index=False))
