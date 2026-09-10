"""
Figura D.8 — Percepción o grado de confianza que las personas tienen al hacer uso del Internet
Fuente: IFT, con información de la Encuesta de Confianza en el Servicio de Internet (ECSI) 2024
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np

# ── 1. DATOS ──────────────────────────────────────────────────────────────────
CSV_PATH = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\D.8\baseconfianzadigital.csv"

try:
    df = pd.read_csv(CSV_PATH, low_memory=False)
except FileNotFoundError:
    # Fallback para pruebas si no existe el archivo
    df = pd.DataFrame({'conf_int': [1,2,3,4,5,9], 'fac_per': [10, 20, 15, 30, 20, 5]})

CODES   = [1, 2, 3, 4, 5, 9]
LABELS  = ["Nada", "Poco", "Le es indiferente", "Algo", "Mucho", "NS/NR"]

valid    = df[df["conf_int"].isin(CODES)].copy()
weighted = valid.groupby("conf_int")["fac_per"].sum()
total    = weighted.sum()
pct      = (weighted / total * 100).round(1)

values = [pct.get(c, 0) for c in CODES]

# ── 2. COLORES (Paleta Teal Institucional) ────────────────────────────────────
COLORS = [
    "#86adae",   # Teal claro
    "#64a0a1",   
    "#4c7d7e",   
    "#3b6667",   
    "#335a5c",   # Teal oscuro
    "#132b2d"    # Teal muy oscuro
]
color_texto = '#3c3c3b'

# ── 3. GRÁFICA ────────────────────────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

x      = np.arange(len(LABELS))
width  = 0.55

bars = ax.bar(x, values, width=width, color=COLORS, edgecolor='none', zorder=2)

# ── Etiquetas de datos (Chips estilo F.16) ──────────────────────────────────
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        bar_color = rect.get_facecolor()
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                    bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

autolabel(bars)

# ── Ejes ──────────────────────────────────────────────────────────────────────
ax.set_xticks(x)
ax.set_xticklabels(LABELS, fontsize=9, fontweight='normal', color=color_texto)

max_val = max(values) if values else 100
ax.set_ylim(0, max_val * 1.25)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# ── Leyenda de colores (CORREGIDA AL NIVEL DE FIGURA) ─────────────────────────
legend_items = [mpatches.Patch(color=COLORS[i], label=LABELS[i]) for i in range(len(LABELS))]
fig.legend(
    handles=legend_items,
    ncol=6,
    loc='lower center',
    bbox_to_anchor=(0.5, 0.12),
    frameon=False,
    fontsize=10,
    handlelength=2.5,
)

# ── Título estilo F.16 ────────────────────────────────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura D.8.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Percepción o grado de confianza que las personas tienen al hacer uso del Internet", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# ── Notas al pie ──────────────────────────────────────────────────────────────
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = 'IFT, con información de la Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.'
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# ── 4. GUARDAR ────────────────────────────────────────────────────────────────
OUTPUT = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_D8.png"
plt.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor="white", edgecolor='none')
print(f"\n¡Figura D.8 corregida! Guardada -> {OUTPUT}")
plt.close()