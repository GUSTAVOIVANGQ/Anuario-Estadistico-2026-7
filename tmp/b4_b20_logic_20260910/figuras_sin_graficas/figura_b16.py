# -*- coding: utf-8 -*-
"""
Figura B.16 — Distribución de los accesos al servicio fijo de Internet
por tecnología de conexión y por segmento (residencial / no residencial)

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
INPUT = ensure_bit_table("TD_ACC_BAF_XT_XC_VA.csv", "B.16")

# ─── Lectura ──────────────────────────────────────────────────────────────────────
df = read_csv_flexible(INPUT)
df["ANIO"] = numeric(df["ANIO"])
df["MES"] = numeric(df["MES"])
for _c in ["A_RESIDENCIAL_E", "A_NO_RESIDENCIAL_E"]:
    df[_c] = numeric(df[_c])
ULTIMO_ANIO = latest_december_year(df)
ANIO_PREVIO = ULTIMO_ANIO - 1

# Normalizar nombre duplicado
df["TECNO_ACCESO_INTERNET"] = df["TECNO_ACCESO_INTERNET"].str.strip()
df["TECNO_ACCESO_INTERNET"] = df["TECNO_ACCESO_INTERNET"].replace(
    {"TecnologÃ­a MÃ³vil": "TecnologÃ­a mÃ³vil"}
)

# ─── Filtros ──────────────────────────────────────────────────────────────────────
TECNO_PRINCIPALES = ["Fibra óptica", "Cable coaxial", "DSL",
                     "Tecnología móvil", "Satelital"]

def get_totals(year, mes=12):
    d = df[(df["ANIO"] == year) & (df["MES"] == mes)]
    d = d[d["TECNO_ACCESO_INTERNET"].isin(TECNO_PRINCIPALES)]
    res   = d.groupby("TECNO_ACCESO_INTERNET")["A_RESIDENCIAL_E"].sum()
    nores = d.groupby("TECNO_ACCESO_INTERNET")["A_NO_RESIDENCIAL_E"].sum()
    return res.reindex(TECNO_PRINCIPALES, fill_value=0), \
           nores.reindex(TECNO_PRINCIPALES, fill_value=0)

res23,  nores23  = get_totals(ULTIMO_ANIO)
res22,  nores22  = get_totals(ANIO_PREVIO)

# ─── Tasas de crecimiento ─────────────────────────────────────────────────────────
def tasa(v23, v22):
    return {t: ((v23[t] - v22[t]) / v22[t] * 100) if v22[t] > 0 else 0
            for t in TECNO_PRINCIPALES}

tc_res   = tasa(res23,  res22)
tc_nores = tasa(nores23, nores22)

total_res   = res23.sum()
total_nores = nores23.sum()
tc_total_res   = (total_res   - res22.sum())   / res22.sum()   * 100
tc_total_nores = (total_nores - nores22.sum()) / nores22.sum() * 100

auditoria = pd.DataFrame({
    "tecnologia": TECNO_PRINCIPALES,
    "residencial_actual": [res23[t] for t in TECNO_PRINCIPALES],
    "residencial_previo": [res22[t] for t in TECNO_PRINCIPALES],
    "no_residencial_actual": [nores23[t] for t in TECNO_PRINCIPALES],
    "no_residencial_previo": [nores22[t] for t in TECNO_PRINCIPALES],
})
save_audit("B.16", auditoria)

# ─── Imprimir resultados usados para la figura ─────────────────────────────────────
print(f"Figura B.16. Distribución de los accesos al servicio fijo de Internet por tecnología "
      f"de conexión y por segmento (dic {ANIO_PREVIO} - dic {ULTIMO_ANIO})")

print(f"\nAccesos residenciales a nivel nacional ({ULTIMO_ANIO}): {int(total_res):,}")
print(f"Tasa de crecimiento anual (residencial, total): {tc_total_res:.1f}%")
print(f"\nAccesos no residenciales a nivel nacional ({ULTIMO_ANIO}): {int(total_nores):,}")
print(f"Tasa de crecimiento anual (no residencial, total): {tc_total_nores:.1f}%")

print("\nAuditoría completa por tecnología (accesos actuales y previos, ambos segmentos):")
print(auditoria.to_string(index=False))

print("\nTasas de crecimiento anual por tecnología — segmento Residencial:")
for t in TECNO_PRINCIPALES:
    print(f"  {t}: {tc_res[t]:.1f}%")

print("\nTasas de crecimiento anual por tecnología — segmento No Residencial:")
for t in TECNO_PRINCIPALES:
    print(f"  {t}: {tc_nores[t]:.1f}%")

print("\nDistribución porcentual por tecnología — segmento Residencial:")
for t in TECNO_PRINCIPALES:
    pct = res23[t] / total_res * 100 if total_res else 0
    print(f"  {t}: {pct:.1f}%")

print("\nDistribución porcentual por tecnología — segmento No Residencial:")
for t in TECNO_PRINCIPALES:
    pct = nores23[t] / total_nores * 100 if total_nores else 0
    print(f"  {t}: {pct:.1f}%")
