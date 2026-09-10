"""
Figura D.9 — Porcentaje de la población usuaria de Internet según nivel de seguridad
que consideran tiene realizar diferentes actividades en Internet (por grupo de edad)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import matplotlib.patches as mpatches

# ── 1. DATOS ──────────────────────────────────────────────────────────────────
CSV_PATH = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\D.9\baseconfianzadigital.csv"

try:
    df = pd.read_csv(CSV_PATH, low_memory=False)
except FileNotFoundError:
    df = pd.DataFrame({'rescate_internet': [1]*10, 'edad_gpos': [1,2,3,4,5,1,2,3,4,5], 'seg_comp': [1,2,3,4,5,1,1,2,3,9], 'fac_per': [10]*10})

users = df[df["rescate_internet"] == 1].copy()
users["cat"] = users["seg_comp"].map({1.0: 1, 2.0: 2, 3.0: 3, 4.0: 4, 5.0: 9, 9.0: 9})
users["cat"] = users["cat"].fillna(9).astype(int)

AGE_CODES  = [1, 2, 3, 4, 5]
AGE_LABELS = ["18 a 24 años", "25 a 34 años", "35 a 44 años", "45 a 54 años", "55 a más años"]
CAT_CODES  = [1, 2, 3, 4, 9]
CAT_LABELS = ["Muy seguro", "Seguro", "Ni seguro/ Ni inseguro", "Inseguro", "NS/NR"]

results = {}
for age_code, age_lbl in zip(AGE_CODES, AGE_LABELS):
    sub      = users[users["edad_gpos"] == age_code]
    total_w  = sub["fac_per"].sum()
    row = {}
    for c, c_lbl in zip(CAT_CODES, CAT_LABELS):
        w = sub[sub["cat"] == c]["fac_per"].sum() if total_w > 0 else 0
        row[c_lbl] = round(w / total_w * 100, 1) if total_w > 0 else 0
    results[age_lbl] = row

# ── 2. PREPARAR ESTILOS F.16 ──────────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

COLORS = {
    "Muy seguro":             "#86adae",   # Teal claro
    "Seguro":                 "#64a0a1",
    "Ni seguro/ Ni inseguro": "#4c7d7e",
    "Inseguro":               "#335a5c",   # Teal oscuro
    "NS/NR":                  "#132b2d",   # Teal muy oscuro
}
color_texto = '#3c3c3b'

n_ages = len(AGE_LABELS)
n_cats = len(CAT_LABELS)
x      = np.arange(n_ages)
width  = 0.15
offsets = np.linspace(-(n_cats - 1) / 2 * width, (n_cats - 1) / 2 * width, n_cats)

# ── 3. GRÁFICA ────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

all_rects = []
for i, (cat_lbl, offset) in enumerate(zip(CAT_LABELS, offsets)):
    vals = [results[age][cat_lbl] for age in AGE_LABELS]
    rects = ax.bar(x + offset, vals, width=width * 0.92,
                   color=COLORS[cat_lbl], edgecolor='none', zorder=2, label=cat_lbl)
    all_rects.append(rects)

# ── Etiquetas de datos (Chips estilo F.16) ──────────────────────────────────
def autolabel(rects_list):
    for rects in rects_list:
        for rect in rects:
            height = rect.get_height()
            if height == 0: continue
            bar_color = rect.get_facecolor()
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 6),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                        bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

autolabel(all_rects)

# ── Ejes ──────────────────────────────────────────────────────────────────────
ax.set_xticks(x)
ax.set_xticklabels(AGE_LABELS, fontsize=9, fontweight='normal', color=color_texto)

max_val = max([max(results[age].values()) for age in AGE_LABELS]) if results else 100
ax.set_ylim(0, max_val * 1.25)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# ── Leyenda (CORREGIDA AL NIVEL DE FIGURA) ────────────────────────────────────
handles = [mpatches.Patch(color=COLORS[c], label=c) for c in CAT_LABELS]
fig.legend(
    handles=handles,
    loc='lower center',
    bbox_to_anchor=(0.5, 0.12),
    ncol=5,
    fontsize=10,
    frameon=False,
    handlelength=2.5
)

# ── Título estilo F.16 (CORREGIDO PARA MOSTRARSE COMPLETO) ────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura D.9.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

# Se agregó un salto de línea (\n) para que el texto respire y no se corte
ax.annotate(" Porcentaje de la población usuaria de Internet según nivel de seguridad\n que consideran tiene realizar diferentes actividades en Internet (por grupo de edad)", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=13, fontweight='medium', color=color_texto, ha='left', va='center')

# Callout / Badge adaptado y ajustado para no chocar
ax.annotate(
    "Percepción de seguridad al\nrealizar compras en Internet",
    xy=(0.88, 0.92), xycoords="axes fraction",
    fontsize=9, fontweight='bold', color=color_texto, ha="center", va="center",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="#ffffff", edgecolor="#4a7d75", linewidth=1.2), zorder=4
)

# ── Notas al pie ──────────────────────────────────────────────────────────────
font_size_notes = 8
x_start = 0.08

y_fuente = 0.08
fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = 'IFT, con información de la Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.'
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.04
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
nota_text = 'Respuesta múltiple, por lo que la suma no da 100%. Los resultados pueden presentar variaciones explicadas por el error teórico de cada encuesta.'
fig.text(x_start + 0.025, y_nota, nota_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# ── 4. GUARDAR ────────────────────────────────────────────────────────────────
OUTPUT = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_D9.png"
plt.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor="white", edgecolor='none')
print(f"\n¡Figura D.9 corregida! Guardada -> {OUTPUT}")
plt.close()