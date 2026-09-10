# -*- coding: utf-8 -*-
"""
Figura H.2 – Horas dedicadas y rating promedio por género en canales nacionales

Barras verticales (Rating %, eje izquierdo) +
dispersión de puntos (Horas de programación, eje derecho).

Tipo: Barras y Dispersión  →  Guia_colores.md: sugerencia #64a0a1 + #ed8945
"""

import textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()

# ── Tipografía institucional ───────────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

# ── Tokens de color ────────────────────────────────────────────────────────────
COLOR_RATING = '#64a0a1'   # teal — barras (Rating)
COLOR_HORAS  = '#ed8945'   # naranja — puntos (Horas)
TEXT_COLOR   = '#3c3c3b'   # gris institucional

# ── 1. Cargar y procesar datos ─────────────────────────────────────────────────
import os
df = pd.read_csv(
    r'C:\Users\ivan-\Documents\GitHub\anuario\datos\H.2\TD_CONSUMO_GENERO_VA.csv',
    encoding='latin1')

df['GENERO'] = df['GENERO'].replace({
    'Películas': 'Películas',
    'Religión': 'Religión',
    'Comicos': 'Cómicos',
    'Dramatizado unitario': 'Dramatizado\nunitario',
    'Reality Show': 'Reality\nShow',
    'Talk Show': 'Talk\nShow'
})

df = df.sort_values(by='GENERO').reset_index(drop=True)
df['RATING_PCT'] = df['PORC_RATING'] * 100

# ── 2. Figura (estilo canónico A.1) ───────────────────────────────────────────
fig, ax1 = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax1.set_facecolor('#F8F8FA')

x = np.arange(len(df['GENERO']))
bar_width = 0.4           # Ajuste de grosor de barras para coincidir con referencia

# ── Eje izquierdo: barras Rating (%) ──────────────────────────────────────────
for i, val in enumerate(df['RATING_PCT']):
    ax1.bar(x[i], val, width=bar_width, color=COLOR_RATING, edgecolor='none', zorder=3)

ax1.set_ylabel('Rating (%)', fontsize=11, color=TEXT_COLOR, labelpad=15)
ax1.set_ylim(0, 3.5)
ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
ax1.set_yticks(np.arange(0, 3.51, 0.5))
ax1.tick_params(axis='y', labelsize=9, colors=TEXT_COLOR)

# ── Eje derecho: dispersión Horas de programación ─────────────────────────────
ax2 = ax1.twinx()
ax2.scatter(x, df['HORAS_PROGRAMACION'], color=COLOR_HORAS, s=150, zorder=4, alpha=1.0)
ax2.set_ylabel('Horas de programación (#)', fontsize=11, color=TEXT_COLOR,
               rotation=270, labelpad=20)
ax2.set_ylim(0, 21600)
ax2.set_yticks(np.arange(0, 21601, 2400))
ax2.tick_params(axis='y', labelsize=9, colors=TEXT_COLOR)

# ── Eje X ─────────────────────────────────────────────────────────────────────
ax1.set_xticks(x)
ax1.set_xticklabels(df['GENERO'], fontsize=9, fontweight='bold', color=TEXT_COLOR)
ax1.tick_params(axis='x', length=0, pad=8)

# ── Cuadrícula ───────────────────────────────────────────────────────────
ax1.set_axisbelow(True)
ax1.grid(axis='y', color='#d1d1d1', linewidth=1, zorder=0)
ax2.grid(False)

# ── Bordes / spines ───────────────────────────────────────────────────────────
ax1.spines['top'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax1.spines['bottom'].set_color('#7c7c7c')
ax1.spines['left'].set_color('#7c7c7c')
ax1.spines['right'].set_color('#7c7c7c')
ax2.spines['bottom'].set_color('#7c7c7c')
ax2.spines['left'].set_color('#7c7c7c')
ax2.spines['right'].set_color('#7c7c7c')

# ── Encabezado: cuadrado + "Figura H.2." bold + subtítulo medium ─────────────
fig.text(0.044, 0.897, ' ', fontsize=2, va='bottom',
         transform=fig.transFigure,
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2',
                   facecolor='#4a7d75', edgecolor='none'))

fig.text(0.055, 0.895, 'Figura H.2.', fontsize=14, fontweight='bold',
         color=TEXT_COLOR, va='bottom', transform=fig.transFigure)

fig.text(0.123, 0.895,
         'Horas dedicadas y rating promedio por género en canales nacionales',
         fontsize=14, fontweight='normal', color=TEXT_COLOR,
         va='bottom', transform=fig.transFigure)

# ── Leyenda centrada ──────────────────────────────────────────────────────────
bar_patch  = mpatches.Patch(color=COLOR_RATING, label='Rating Total personas')
line_patch = Line2D([0], [0], marker='o', color='w', markerfacecolor=COLOR_HORAS,
                    markersize=10, label='Horas de programación')
fig.legend(handles=[bar_patch, line_patch], loc='lower center',
           bbox_to_anchor=(0.5, 0.08), ncol=2, fontsize=10,
           frameon=False, handlelength=2.5)

# ── Notas al pie — esquina inferior izquierda ────────────────────────────────
fig.text(0.05, 0.055, 'Fuente: ', fontsize=8, color=TEXT_COLOR, va='top',
         fontweight='bold', transform=fig.transFigure)
fig.text(0.084, 0.055,
         'IFT con datos de medición de audiencias de canales nacionales '
         'de televisión abierta.',
         fontsize=8, color=TEXT_COLOR, va='top', fontweight='normal',
         transform=fig.transFigure)

fig.text(0.05, 0.030, 'Notas: ', fontsize=8, color=TEXT_COLOR, va='top',
         fontweight='bold', transform=fig.transFigure)
fig.text(0.082, 0.030,
         'El rating corresponde al porcentaje promedio de personas que sintonizaron '
         'cada género respecto al total de la población. Las horas de programación reflejan '
         'el total de horas transmitidas por género en el periodo de análisis.',
         fontsize=8, color=TEXT_COLOR, va='top', fontweight='normal',
         transform=fig.transFigure)

# ── Exportar ──────────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
output_path = r'C:\Users\ivan-\Documents\GitHub\anuario\output\figura_h2.png'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
fig.savefig(output_path, dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"Figura guardada en: {output_path}")
plt.close(fig)