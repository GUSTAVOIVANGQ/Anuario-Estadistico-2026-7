# -*- coding: utf-8 -*-
"""Figura B.8 — Tráfico de minutos del Servicio Fijo de Telefonía.

Versión SIN generación de gráfica: calcula los mismos datos que alimentan
la figura original y los imprime en consola.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _bit_crt_common import (
    OUTPUT_DIR as PROJECT_OUTPUT_DIR,
    ensure_bit_table_any,
    latest_december_year,
    normalize_columns,
    numeric,
    read_csv_flexible,
    save_audit,
)

# ── 1. DATOS CRUDOS BIT/CRT ──────────────────────────────────────────────────
# El archivo heredado de B.8 estaba sustituido por el código de B.18. Esta
# versión busca la tabla de tráfico de telefonía fija dentro de la descarga BIT.
CANDIDATOS = [
    "TD_TRAF_HIST_TELFIJA_ITE_VA.csv",
    "TD_TRAF_TELFIJA_ITE_VA.csv",
    "TD_TRAF_HIST_TELFIJA_VA.csv",
    "TD_TRAF_TELFIJA_VA.csv",
]
DATA_PATH = ensure_bit_table_any(CANDIDATOS, "B.8", keywords=("traf", "telfija"))
df = normalize_columns(read_csv_flexible(DATA_PATH))

if "ANIO" not in df.columns:
    raise RuntimeError(f"La tabla {DATA_PATH.name} no contiene ANIO.")
df["ANIO"] = numeric(df["ANIO"])
if "MES" in df.columns:
    df["MES"] = numeric(df["MES"])
    ULTIMO_ANIO = latest_december_year(df)
    base = df[df["MES"] == 12].copy()
else:
    ULTIMO_ANIO = int(df["ANIO"].dropna().max())
    base = df.copy()

# El Anuario grafica tráfico LOCAL DE SALIDA. Se identifica la variable sin
# sumar LDI ni tráfico recibido. Si el esquema futuro cambia de forma ambigua,
# se detiene para evitar publicar una cifra incorrecta.
preferidas = [
    "TRAF_LOCAL_SALIDA", "TRAFICO_LOCAL_SALIDA", "TRAF_SALIDA_LOCAL",
    "MIN_LOCAL_SALIDA", "MINUTOS_LOCAL_SALIDA", "TRAF_LOCAL_E",
    "TRAFICO_LOCAL_E", "TRAF_LOCAL", "TRAFICO_LOCAL", "TRAF_SALIDA",
]
col_traf = next((c for c in preferidas if c in base.columns), None)
if col_traf is None:
    posibles = [
        c for c in base.columns
        if ("TRAF" in c or "MINUT" in c)
        and "LOCAL" in c
        and not any(x in c for x in ("LDI", "INTERN", "RECIB", "ENTRAD"))
    ]
    salida = [c for c in posibles if "SALIDA" in c]
    if len(salida) == 1:
        col_traf = salida[0]
    elif len(posibles) == 1:
        col_traf = posibles[0]
    else:
        raise RuntimeError(
            "No se pudo identificar de forma unívoca la columna de tráfico local "
            f"en {DATA_PATH.name}. Candidatas encontradas: {posibles}. "
            "No se hará una suma heurística para evitar alterar el indicador."
        )

base[col_traf] = numeric(base[col_traf])
serie_raw = base.groupby("ANIO", dropna=True)[col_traf].sum(min_count=1).sort_index()
serie_raw = serie_raw.loc[(serie_raw.index >= 2000) & (serie_raw.index <= ULTIMO_ANIO)]
if serie_raw.empty:
    raise RuntimeError("No hay observaciones de tráfico local para el rango de la figura.")

# Los eFormatos reportan minutos efectivos; la figura se expresa en millones.
trafico = serie_raw / 1_000_000.0
resultados = pd.DataFrame({
    "ANIO": trafico.index.astype(int),
    "TRAFICO_LOCAL_MINUTOS": serie_raw.values,
    "TRAFICO_LOCAL_MILLONES_MINUTOS": trafico.values,
    "COLUMNA_ORIGEN": col_traf,
})
save_audit("B.8", resultados)

# ── 2. Imprimir resultados usados para la figura ──────────────────────────────
print(f"Figura B.8. Tráfico de minutos del Servicio Fijo de Telefonía (2000-{ULTIMO_ANIO})")
print(f"Columna de origen utilizada: {col_traf}")
print("\nValores calculados (tráfico local de salida por año):")
print(resultados.to_string(index=False))
