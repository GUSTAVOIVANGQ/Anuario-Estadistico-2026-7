# -*- coding: utf-8 -*-
"""Figura B.10 — IHH del Servicio Fijo de Telefonía.

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
# Se prefiere una tabla IHH específica si BIT la ofrece. Si no existe, el IHH
# se reproduce exactamente desde las participaciones de mercado: Σ(cuota²).
DATA_PATH = ensure_bit_table_any(
    ["TD_IHH_TELFIJA_ITE_VA.csv", "TD_MARKET_SHARE_TELFIJA_ITE_VA.csv"],
    "B.10",
    keywords=("telfija",),
)
df = normalize_columns(read_csv_flexible(DATA_PATH))
df["ANIO"] = numeric(df["ANIO"])
df["MES"] = numeric(df["MES"])
ULTIMO_ANIO = latest_december_year(df)
dic = df[(df["MES"] == 12) & (df["ANIO"] >= 2013) & (df["ANIO"] <= ULTIMO_ANIO)].copy()

col_ihh = next((c for c in ["IHH_TELFIJA_E", "IHH_TELFIJA", "IHH_E", "IHH"] if c in dic.columns), None)
if col_ihh:
    dic[col_ihh] = numeric(dic[col_ihh])
    data = dic.groupby("ANIO", as_index=False)[col_ihh].first().rename(columns={col_ihh: "ihh"})
    data["metodo"] = f"campo BIT {col_ihh}"
else:
    if "MARKET_SHARE" not in dic.columns:
        raise RuntimeError(
            f"{DATA_PATH.name} no contiene un IHH ni MARKET_SHARE para reproducirlo."
        )
    dic["MARKET_SHARE"] = numeric(dic["MARKET_SHARE"])
    grupo_col = "GRUPO" if "GRUPO" in dic.columns else None
    if grupo_col:
        cuotas = dic.groupby(["ANIO", grupo_col], as_index=False)["MARKET_SHARE"].sum()
    else:
        cuotas = dic[["ANIO", "MARKET_SHARE"]].dropna().copy()
    cuotas["cuota2"] = cuotas["MARKET_SHARE"] ** 2
    data = cuotas.groupby("ANIO", as_index=False)["cuota2"].sum().rename(columns={"cuota2": "ihh"})
    data["metodo"] = "suma de cuadrados de MARKET_SHARE"

data = data.sort_values("ANIO").reset_index(drop=True)
save_audit("B.10", data)

# ── 2. Imprimir resultados usados para la figura ──────────────────────────────
print(f"Figura B.10. Índice Herfindahl-Hirschman (IHH). Concentración de mercado "
      f"del Servicio Fijo de Telefonía (2013-{ULTIMO_ANIO})")
print("\nValores calculados (IHH por año):")
print(data.to_string(index=False))
