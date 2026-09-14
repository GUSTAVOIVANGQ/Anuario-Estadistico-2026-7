# -*- coding: utf-8 -*-
"""
Figura B.6 — Líneas del Servicio Fijo de Telefonía Residencial
por cada 100 hogares por entidad federativa.

Versión SIN generación de gráfica (sin mapa): calcula los mismos datos
que alimentan la figura original (valor por entidad, rango/color asignado,
valor nacional y tasa de crecimiento anual) y los imprime en consola.
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

# ── 1. RUTAS Y LECTURA DE DATOS ──────────────────────────────────────────
DATA_PATH = ensure_bit_table("TD_PENETRACIONES_TELFIJA_ITE_VA.csv", "B.6")

df_all = read_csv_flexible(DATA_PATH)
df_all["ANIO"] = numeric(df_all["ANIO"])
df_all["MES"] = numeric(df_all["MES"])
df_all["P_RES_H_TELFIJA_E"] = numeric(df_all["P_RES_H_TELFIJA_E"])
ULTIMO_ANIO = latest_december_year(df_all)
ANIO_PREVIO = ULTIMO_ANIO - 1
df = df_all[(df_all["ANIO"] == ULTIMO_ANIO) & (df_all["MES"] == 12)].copy()
data = dict(zip(df["ENTIDAD"], df["P_RES_H_TELFIJA_E"]))
if "Nacional" not in data:
    raise RuntimeError("BIT no contiene la fila Nacional para B.6; no se estimará a partir de promedios estatales.")
nacional_val = float(data["Nacional"])
prev = df_all[(df_all["ANIO"] == ANIO_PREVIO) & (df_all["MES"] == 12) & (df_all["ENTIDAD"].astype(str).str.strip().str.casefold() == "nacional")]["P_RES_H_TELFIJA_E"]
tasa_crecimiento = ((nacional_val / float(prev.iloc[0])) - 1) * 100 if len(prev) and float(prev.iloc[0]) != 0 else float("nan")
save_audit("B.6", df[["ANIO", "MES", "ENTIDAD", "P_RES_H_TELFIJA_E"]])

# ── 2. RANGOS Y COLORES (los mismos de la figura original) ───────────────
COLORS = ['#afafaf', '#737f7c', '#63918b', '#2d4f4b', '#012f2a']
LABELS = ['Menos de 29', '29 a 42', '43 a 55', '56 a 68', 'Más de 68']
BREAKS = [0, 29, 43, 56, 69, 999]

def get_color(val):
    for i in range(len(BREAKS) - 1):
        if BREAKS[i] <= val < BREAKS[i + 1]:
            return COLORS[i]
    return COLORS[-1]

def get_label(val):
    for i in range(len(BREAKS) - 1):
        if BREAKS[i] <= val < BREAKS[i + 1]:
            return LABELS[i]
    return LABELS[-1]

# ── 3. Imprimir resultados usados para la figura ──────────────────────────────
print(f"Figura B.6. Líneas del Servicio Fijo de Telefonía Residencial por cada 100 hogares "
      f"por entidad federativa (diciembre {ULTIMO_ANIO})")

print(f"\nValor nacional: {int(nacional_val)}")
print(f"Tasa de crecimiento anual (dic {ANIO_PREVIO} - dic {ULTIMO_ANIO}): {tasa_crecimiento:.1f}%")

print("\nValores por entidad federativa (líneas residenciales por cada 100 hogares):")
tabla = pd.DataFrame({
    "ENTIDAD": list(data.keys()),
    "P_RES_H_TELFIJA_E": list(data.values()),
})
tabla["RANGO"] = tabla["P_RES_H_TELFIJA_E"].apply(get_label)
tabla["COLOR"] = tabla["P_RES_H_TELFIJA_E"].apply(get_color)
print(tabla.sort_values("P_RES_H_TELFIJA_E", ascending=False).to_string(index=False))
