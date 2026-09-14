# -*- coding: utf-8 -*-
"""
Figura B.13 — Accesos del Servicio Fijo de Acceso a Internet Residencial
por cada 100 hogares por entidad federativa.

Versión SIN generación de gráfica (sin mapa): calcula los mismos datos
que alimentan la figura original (valor por entidad, rango/color asignado,
valor nacional y tasa de crecimiento anual) y los imprime en consola.

Fuente datos: TD_PENETRACIONES_BAF_ITE_VA.csv (BIT IFT)
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
DATA_PATH = ensure_bit_table("TD_PENETRACIONES_BAF_ITE_VA.csv", "B.13")

df_all = read_csv_flexible(DATA_PATH)
df_all["ANIO"] = numeric(df_all["ANIO"])
df_all["MES"] = numeric(df_all["MES"])
METRICA = next((c for c in ["P_RES_H_BAF_E", "P_RES_H_BAF", "P_BAF_E"] if c in df_all.columns), None)
if METRICA is None:
    raise RuntimeError(f"No se encontró la variable residencial esperada en {DATA_PATH.name}. Columnas: {list(df_all.columns)}")
df_all[METRICA] = numeric(df_all[METRICA])
ULTIMO_ANIO = latest_december_year(df_all)
ANIO_PREVIO = ULTIMO_ANIO - 1
df = df_all[(df_all["ANIO"] == ULTIMO_ANIO) & (df_all["MES"] == 12)].copy()
data = dict(zip(df["ENTIDAD"], df[METRICA]))
if "Nacional" not in data:
    raise RuntimeError("BIT no contiene la fila Nacional para B.13; no se estimará a partir de promedios estatales.")
nacional_val = float(data["Nacional"])
prev = df_all[(df_all["ANIO"] == ANIO_PREVIO) & (df_all["MES"] == 12) & (df_all["ENTIDAD"].astype(str).str.strip().str.casefold() == "nacional")][METRICA]
tasa_crecimiento = ((nacional_val / float(prev.iloc[0])) - 1) * 100 if len(prev) and float(prev.iloc[0]) != 0 else float("nan")
aud = df[["ANIO", "MES", "ENTIDAD", METRICA]].rename(columns={METRICA: "P_RESIDENCIAL_BAF"})
save_audit("B.13", aud)

# ── 2. RANGOS Y COLORES (los mismos de la figura original) ───────────────
COLORS = ['#afafaf', '#737f7c', '#63918b', '#2d4f4b', '#012f2a']
LABELS = ['Menos de 35', '36 a 47', '48 a 59', '60 a 70', 'Más de 70']
BREAKS = [0, 36, 48, 60, 71, 9999]

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
print(f"Figura B.13. Accesos del Servicio Fijo de Acceso a Internet Residencial por cada "
      f"100 hogares por entidad federativa (diciembre {ULTIMO_ANIO})")

print(f"\nValor nacional: {int(nacional_val)}")
print(f"Tasa de crecimiento anual (dic {ANIO_PREVIO} - dic {ULTIMO_ANIO}): {tasa_crecimiento:.1f}%")

print("\nValores por entidad federativa (accesos residenciales por cada 100 hogares):")
tabla = pd.DataFrame({
    "ENTIDAD": list(data.keys()),
    "P_RESIDENCIAL_BAF": list(data.values()),
})
tabla["RANGO"] = tabla["P_RESIDENCIAL_BAF"].apply(get_label)
tabla["COLOR"] = tabla["P_RESIDENCIAL_BAF"].apply(get_color)
print(tabla.sort_values("P_RESIDENCIAL_BAF", ascending=False).to_string(index=False))
