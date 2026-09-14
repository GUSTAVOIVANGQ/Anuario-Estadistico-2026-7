# -*- coding: utf-8 -*-
"""
Figura B.15 — Distribución de los accesos del Servicio Fijo de Internet
por rangos de velocidad (2013-actual)

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
INPUT = ensure_bit_table("TD_ACC_BAFXV_ITE_VA.csv", "B.15")

# ─── Lectura y filtro ─────────────────────────────────────────────────────────────
df = read_csv_flexible(INPUT)
df["ANIO"] = numeric(df["ANIO"])
df["MES"] = numeric(df["MES"])
for _c in ["A_V1_E", "A_V2_E", "A_V3_E", "A_V4_E", "A_NO_ESPECIFICADO_E", "A_TOTAL_E"]:
    df[_c] = numeric(df[_c])
ULTIMO_ANIO = latest_december_year(df)
dic = df[df["MES"] == 12].copy()
dic = dic[(dic["ANIO"] >= 2013) & (dic["ANIO"] <= ULTIMO_ANIO)]

# ─── Agregación por año ───────────────────────────────────────────────────────────
agg = dic.groupby("ANIO")[
    ["A_V1_E", "A_V2_E", "A_V3_E", "A_V4_E", "A_NO_ESPECIFICADO_E", "A_TOTAL_E"]
].sum()

# ─── Porcentajes ──────────────────────────────────────────────────────────────────
tot = agg["A_TOTAL_E"]
pct = pd.DataFrame({
    "v1": agg["A_V1_E"]               / tot * 100,
    "v2": agg["A_V2_E"]               / tot * 100,
    "v3": agg["A_V3_E"]               / tot * 100,
    "v4": agg["A_V4_E"]               / tot * 100,
    "ns": agg["A_NO_ESPECIFICADO_E"]  / tot * 100,
}, index=agg.index)

years = pct.index.tolist()
save_audit("B.15", pct.reset_index())

total_fin = int(agg.loc[ULTIMO_ANIO, "A_TOTAL_E"])

# ─── Imprimir resultados usados para la figura ─────────────────────────────────────
print(f"Figura B.15. Distribución de los accesos del Servicio Fijo de Internet por rangos "
      f"de velocidad (2013-{ULTIMO_ANIO})")

print(f"\nTotal nacional {ULTIMO_ANIO}: {total_fin:,}")

print("\nAccesos por rango de velocidad y año (valores absolutos):")
print(agg.to_string())

print("\nDistribución porcentual por rango de velocidad y año:")
print("v1 = 256 Kbps a 1.99 Mbps | v2 = 2 a 9.99 Mbps | v3 = 10 a 100 Mbps | "
      "v4 = mayores a 100 Mbps | ns = sin información")
print(pct.to_string())
