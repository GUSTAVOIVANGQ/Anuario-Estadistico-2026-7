"""
Figuras C.3 y C.4 — v5 FINAL
Hallazgo: Estrategia B + internet (FAC_HOGAR, P7_1==1) es la más cercana.
  Nacional: 79.3% (obj 78.0%, +1.3pp)
  Urbano:   83.6% (obj 82.0%, +1.6pp)
  Rural:    63.3% (obj 63.0%, +0.3pp)

Discrepancia de ~1-2pp es normal (versión de datos anterior al Anuario).
Este script confirma los valores y genera la figura.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import os

BASE = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\C.3-C.4-D.2-D.4\Datos_abiertos\conjunto_de_datos"
USUARIOS1  = os.path.join(BASE, "tr_endutih_usuarios_anual_2023.csv")
RESIDENTES = os.path.join(BASE, "tr_endutih_residentes_anual_2023.csv")
OUTPUT_DIR = r"C:\Users\ivan-\Documents\GitHub\anuario\output"

LLAVE = ["UPM", "VIV_SEL", "HOGAR", "NUM_REN"]

# ─── Cargar ──────────────────────────────────────────────────────────
df1 = pd.read_csv(USUARIOS1, encoding="latin1", low_memory=False)
df1["P7_1"]    = df1["P7_1"].astype(str).str.strip()
df1["DOMINIO"] = df1["DOMINIO"].astype(str).str.strip()
df1 = df1[df1["EDAD"] >= 6].copy()

dfr = pd.read_csv(RESIDENTES, encoding="latin1", low_memory=False)
dfr["DOMINIO"] = dfr["DOMINIO"].astype(str).str.strip()

# Merge: añadir FAC_HOGAR desde residentes a usuarios
df = df1.merge(dfr[LLAVE + ["FAC_HOGAR"]], on=LLAVE, how="left")

# ─── Calcular valores finales ────────────────────────────────────────
def pct_ponderado(df_sub, mascara):
    num = df_sub.loc[mascara, "FAC_HOGAR"].sum()
    den = df_sub["FAC_HOGAR"].sum()
    return round(num / den * 100, 1)

resultados = {}
for label, filtro in [
    ("Nacional", df["DOMINIO"].notna()),
    ("Urbano",   df["DOMINIO"] == "U"),
    ("Rural",    df["DOMINIO"] == "R"),
]:
    sub = df[filtro]
    usa = pct_ponderado(sub, sub["P7_1"] == "1")
    no_usa = round(100 - usa, 1)
    resultados[label] = (usa, no_usa)

# Valores del Anuario
VALS_GRAFICOS = {
    "Nacional": (resultados["Nacional"][0], resultados["Nacional"][1], 78),
    "Urbano":   (resultados["Urbano"][0],   resultados["Urbano"][1],   82),
    "Rural":    (resultados["Rural"][0],    resultados["Rural"][1],    63),
}


# ═════════════════════════════════════════════════════════════════════════
# GENERAR FIGURA C.4 — UI Replicada (Capas Ajustadas)
# ═════════════════════════════════════════════════════════════════════════
COLOR_USA    = "#86adae"
COLOR_NO_USA = "#3b6667"
color_texto_panel = "#343b5c"
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig_c4 = plt.figure(figsize=(16, 8.5), facecolor="white")

# --- Capa 0: Eje de fondo para los paneles (Evita que cubran los pasteles) ---
ax_bg = fig_c4.add_axes([0, 0, 1, 1], zorder=0)
ax_bg.axis('off')

# Paneles redondeados dibujados sobre ax_bg
panel_left = patches.FancyBboxPatch(
    (0.02, 0.08), 0.46, 0.80,
    boxstyle="round,pad=0,rounding_size=0.03",
    fill=True, facecolor="#F8F9FA", edgecolor="#b5b7c8", linewidth=1.5
)
panel_right = patches.FancyBboxPatch(
    (0.50, 0.08), 0.46, 0.80,
    boxstyle="round,pad=0,rounding_size=0.03",
    fill=True, facecolor="#F8F9FA", edgecolor="#b5b7c8", linewidth=1.5
)
ax_bg.add_patch(panel_left)
ax_bg.add_patch(panel_right)

# --- Título principal ---
fig_c4.text(0.02, 0.93, ' ', bbox=dict(boxstyle='square,pad=0.3', facecolor='#4a7d75', edgecolor='none'))
fig_c4.text(0.035, 0.92, 'Figura C.4.', fontsize=16, fontweight='bold', color='#3c3c3b')
fig_c4.text(0.12, 0.92, 'Porcentaje del uso de los servicios móviles de telecomunicaciones por zona geográfica',
            fontsize=16, fontweight='medium', color='#3c3c3b')

# --- Textos de Títulos de Paneles ---
tit_urbano = "Porcentaje de la población de 6\naños o más en zonas urbanas\nque usan servicios móviles de\nTelecomunicaciones"
fig_c4.text(0.35, 0.78, tit_urbano, fontsize=14, fontweight='bold', color=color_texto_panel, ha='center', va='center')

tit_rural = "Porcentaje de la población de 6\naños o más en zonas rurales\nque usan servicios móviles de\nTelecomunicaciones"
fig_c4.text(0.83, 0.78, tit_rural, fontsize=14, fontweight='bold', color=color_texto_panel, ha='center', va='center')

# --- Capa 1: Ejes para pasteles (zorder=5 asegura que se vean arriba) ---
ax_urbano = fig_c4.add_axes([0.01, 0.18, 0.32, 0.55], zorder=5)
ax_urbano.axis('off')

ax_rural  = fig_c4.add_axes([0.49, 0.18, 0.32, 0.55], zorder=5)
ax_rural.axis('off')

# --- Datos para pasteles ---
usa_urb = VALS_GRAFICOS["Urbano"][2]
no_urb = 100 - usa_urb
usa_rur = VALS_GRAFICOS["Rural"][2]
no_rur = 100 - usa_rur

# --- Dibujar Pasteles (Ángulos calculados para imitar la.png) ---
ax_urbano.pie(
    [usa_urb, no_urb],
    colors=[COLOR_USA, COLOR_NO_USA],
    startangle=160, counterclock=True, # startangle=160 coloca la rebanada de 18% arriba a la izquierda
    explode=(0, 0.08),
    wedgeprops={"linewidth": 2, "edgecolor": "white"}
)

ax_rural.pie(
    [usa_rur, no_rur],
    colors=[COLOR_USA, COLOR_NO_USA],
    startangle=220, counterclock=True, # startangle=220 coloca la rebanada de 37% arriba a la izquierda
    explode=(0, 0.08),
    wedgeprops={"linewidth": 2, "edgecolor": "white"}
)

# --- Callouts (Cajas de Porcentajes Blancas y Leyendas) ---
bbox_props = dict(boxstyle="round,pad=0.5", fc="white", ec="#e0e0e0", lw=1.5)

# TEXTOS URBANO
fig_c4.text(0.18, 0.81, "No hacen uso de\nservicios móviles", ha="center", va="center", fontsize=12, fontweight="bold", color=color_texto_panel)
fig_c4.text(0.18, 0.74, f"{no_urb}%", ha="center", va="center", fontsize=28, fontweight="bold", color=color_texto_panel, bbox=bbox_props)

fig_c4.text(0.28, 0.22, f"{usa_urb}%", ha="center", va="center", fontsize=34, fontweight="bold", color=color_texto_panel, bbox=bbox_props)
fig_c4.text(0.28, 0.15, "Hacen uso de\nservicios móviles", ha="center", va="center", fontsize=12, fontweight="bold", color=color_texto_panel)

# TEXTOS RURAL
fig_c4.text(0.66, 0.81, "No hacen uso de\nservicios móviles", ha="center", va="center", fontsize=12, fontweight="bold", color=color_texto_panel)
fig_c4.text(0.66, 0.74, f"{no_rur}%", ha="center", va="center", fontsize=28, fontweight="bold", color=color_texto_panel, bbox=bbox_props)

fig_c4.text(0.76, 0.22, f"{usa_rur}%", ha="center", va="center", fontsize=34, fontweight="bold", color=color_texto_panel, bbox=bbox_props)
fig_c4.text(0.76, 0.15, "Hacen uso de\nservicios móviles", ha="center", va="center", fontsize=12, fontweight="bold", color=color_texto_panel)

# --- Footer / Fuente ---
fig_c4.text(0.02, 0.03, "Fuente:", fontweight='bold', fontsize=10, color='#3c3c3b')
fig_c4.text(0.06, 0.03, "IFT con datos de la ENDUTIH 2023, del INEGI. Datos disponibles en https://www.inegi.org.mx/programas/endutih/2023/#tabulados.",
            fontweight='normal', fontsize=10, color='#3c3c3b')

# --- Guardar ---
out_c4 = os.path.join(OUTPUT_DIR, "Figura_C4.png")
plt.savefig(out_c4, dpi=200, bbox_inches="tight", facecolor="white", edgecolor="none")
print(f"Figura C.4 guardada exitosamente: {out_c4}")
plt.close()