# -*- coding: utf-8 -*-
"""
Figura A.10 – Gasto promedio y porcentaje de gasto en Servicios de
Telecomunicaciones Móviles de los hogares por decil de ingreso

Barras verticales (gasto promedio mensual, eje derecho) +
puntos con etiqueta (% gasto respecto al ingreso, eje izquierdo).

Fuente: IFT con datos de la ENIGH 2022, del INEGI.
Datos disponibles en: https://www.inegi.org.mx/programas/enigh/nc/2022/.
"""

import os
import textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()

# ── Tipografía institucional ───────────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

# ── Tokens de color (Guia_colores.md) ─────────────────────────────────────────
BAR_COLOR  = '#86adae'   # teal claro — barras
LINE_COLOR = '#335a5c'   # teal oscuro — puntos
TEXT_COLOR = '#3c3c3b'   # gris institucional

# ── 1. Carga de microdatos ENIGH 2022 ─────────────────────────────────────────
BASE = os.path.join(os.path.dirname(__file__), "..", "..", 'datos', 'A.7', 'microdatos')

concentrado = pd.read_csv(
    os.path.join(BASE, 'concentradohogar.csv'), low_memory=False,
    usecols=['folioviv', 'foliohog', 'ing_cor', 'factor', 'comunica'])
concentrado['ing_cor'] = pd.to_numeric(concentrado['ing_cor'], errors='coerce').fillna(0)
concentrado['comunica'] = pd.to_numeric(concentrado['comunica'], errors='coerce').fillna(0)

hogares = pd.read_csv(
    os.path.join(BASE, 'hogares.csv'), low_memory=False,
    usecols=['folioviv', 'foliohog', 'telefono', 'celular', 'tv_paga', 'conex_inte'])

gh = pd.read_csv(os.path.join(BASE, 'gastoshogar.csv'), low_memory=False,
                 usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri', 'gas_nm_tri'])
gp = pd.read_csv(os.path.join(BASE, 'gastospersona.csv'), low_memory=False,
                 usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri'])

gh['gasto'] = (pd.to_numeric(gh['gasto_tri'], errors='coerce').fillna(0)
               + pd.to_numeric(gh['gas_nm_tri'], errors='coerce').fillna(0))
gp['gasto'] = pd.to_numeric(gp['gasto_tri'], errors='coerce').fillna(0)

MOVILES_CLAVES = ['E002']
all_gastos = pd.concat([gh[['folioviv', 'foliohog', 'clave', 'gasto']],
                        gp[['folioviv', 'foliohog', 'clave', 'gasto']]])
gm = (all_gastos[all_gastos['clave'].isin(MOVILES_CLAVES)]
      .groupby(['folioviv', 'foliohog'])['gasto'].sum().reset_index())
gm.columns = ['folioviv', 'foliohog', 'gasto_moviles']

df = concentrado.merge(hogares, on=['folioviv', 'foliohog'], how='left')
df = df.merge(gm, on=['folioviv', 'foliohog'], how='left')
df['gasto_moviles'] = df['gasto_moviles'].fillna(0)

# ── 1b. Deciles ───────────────────────────────────────────────────────────────
df = df.sort_values('ing_cor').reset_index(drop=True)
df['cum_factor'] = df['factor'].cumsum()
df['pct_cum'] = df['cum_factor'] / df['factor'].sum()
df['decil'] = pd.cut(
    df['pct_cum'], bins=np.linspace(0, 1, 11),
    labels=range(1, 11), include_lowest=True
).astype(int)

# ── 1c. Indicadores ───────────────────────────────────────────────────────────
df['tiene_moviles'] = (df['celular'] == 1).astype(int)
df['dg_moviles'] = ((df['tiene_moviles'] == 1) & (df['comunica'] > 0)).astype(int)

# ── 1d. Cálculo por decil ─────────────────────────────────────────────────────
deciles = list(range(1, 11))
gasto = []
pct_gasto = []

for d in deciles:
    sub = df[(df['decil'] == d) & (df['dg_moviles'] == 1)]
    w = sub['factor']
    gasto_mensual   = (sub['gasto_moviles'] * w).sum() / w.sum() / 3
    ingreso_mensual = (sub['ing_cor'] * w).sum() / w.sum() / 3
    gasto.append(round(gasto_mensual))
    pct_gasto.append(
        round(gasto_mensual / ingreso_mensual * 100, 1) if ingreso_mensual > 0 else 0)

# ==============================================================================
# 2. FIGURA  (estilo canónico Figura A.1)
# ==============================================================================
fig, ax1 = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax1.set_facecolor('#F8F8FA')

x = np.arange(len(deciles))
bar_width = 0.72           # ← mismo ancho que A.1

# ── Eje derecho: barras de gasto ──────────────────────────────────────────────
ax2 = ax1.twinx()

for i, g in enumerate(gasto):
    ax2.bar(x[i], g, width=bar_width, color=BAR_COLOR, edgecolor='none', zorder=2)

# Etiquetas de gasto dentro de la barra, parte inferior
for i, g in enumerate(gasto):
    ax2.text(x[i], g * 0.04, f'${g:,}',
             ha='center', va='bottom', fontsize=8,
             fontweight='bold', color='white', zorder=3)

gasto_max  = int(np.ceil(max(gasto) * 1.15 / 100) * 100)
gasto_tick = 200 if gasto_max > 1200 else 100
ax2.set_ylabel('Gasto promedio mensual', fontsize=11, color=TEXT_COLOR,
               rotation=270, labelpad=20)
ax2.set_ylim(0, gasto_max)
ax2.yaxis.set_major_locator(mticker.MultipleLocator(gasto_tick))
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'${int(v):,}'))
ax2.tick_params(axis='y', labelsize=9, colors=TEXT_COLOR)

# ── Eje izquierdo: % gasto ────────────────────────────────────────────────────
ax1.set_zorder(ax2.get_zorder() + 1)
ax1.set_frame_on(False)

pct_max = float(np.ceil(max(pct_gasto) * 1.3 * 2) / 2)
ax1.set_ylim(0, pct_max)
ax1.yaxis.set_major_locator(mticker.MultipleLocator(0.5))
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}%'))
ax1.set_ylabel('% Gasto con respecto al ingreso', fontsize=11, color=TEXT_COLOR,
               labelpad=15)
ax1.tick_params(axis='y', labelsize=9, colors=TEXT_COLOR)

# Puntos y chips de porcentaje
ax1.scatter(x, pct_gasto, color=LINE_COLOR, s=50, zorder=5)
for i, pct in enumerate(pct_gasto):
    ax1.annotate(f'{pct:.1f}%', xy=(x[i], pct),
                 xytext=(0, 12), textcoords='offset points',
                 ha='center', va='bottom', fontsize=8,
                 fontweight='bold', color=TEXT_COLOR,
                 bbox=dict(boxstyle='round,pad=0.3,rounding_size=0.8',
                           facecolor='white', edgecolor=LINE_COLOR, linewidth=0.8))

# ── Eje X ─────────────────────────────────────────────────────────────────────
ax1.set_xticks(x)
ax1.set_xticklabels(deciles, fontsize=10, fontweight='bold', color=TEXT_COLOR)
ax1.set_xlabel('Decil de ingreso', fontsize=10, fontweight='bold',
               color=TEXT_COLOR, labelpad=10)
ax1.tick_params(axis='x', length=0, pad=8, colors=TEXT_COLOR)
ax1.set_xlim(-0.6, len(deciles) - 0.4)

# ── Sin cuadrícula ───────────────────────────────────────────────────────────
ax1.grid(False)
ax2.grid(False)

# ── Bordes / spines ───────────────────────────────────────────────────────────
ax1.spines['top'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax1.spines['bottom'].set_color('#7c7c7c')
ax1.spines['left'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax2.spines['bottom'].set_color('#7c7c7c')
ax2.spines['left'].set_color('#7c7c7c')
ax2.spines['right'].set_color('#7c7c7c')

# ── Encabezado: cuadrado + "Figura A.10." bold + subtítulo medium ────────────
fig.text(0.044, 0.897, ' ', fontsize=2, va='bottom',
         transform=fig.transFigure,
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2',
                   facecolor='#4a7d75', edgecolor='none'))

fig.text(0.055, 0.895, 'Figura A.10.', fontsize=14, fontweight='bold',
         color=TEXT_COLOR, va='bottom', transform=fig.transFigure)

fig.text(0.130, 0.895,
         'Gasto promedio y porcentaje de gasto en Servicios de '
         'Telecomunicaciones Móviles de los hogares por decil de ingreso',
         fontsize=14, fontweight='normal', color=TEXT_COLOR,
         va='bottom', transform=fig.transFigure)

# ── Leyenda centrada ──────────────────────────────────────────────────────────
bar_patch  = mpatches.Patch(facecolor=BAR_COLOR, edgecolor='none',
                            label='Gasto mensual promedio')
line_patch = plt.Line2D([0], [0], marker='o', color='none', markersize=6,
                        markerfacecolor=LINE_COLOR, markeredgewidth=0,
                        label='% Gasto respecto al ingreso')
fig.legend(handles=[bar_patch, line_patch], loc='lower center',
           bbox_to_anchor=(0.5, 0.08), ncol=2, fontsize=10,
           frameon=False, handlelength=2.5)

# ── Notas al pie — esquina inferior izquierda ────────────────────────────────
fig.text(0.05, 0.055, 'Fuente: ', fontsize=8, color=TEXT_COLOR, va='top',
         fontweight='bold', transform=fig.transFigure)
fig.text(0.084, 0.055,
         'IFT con datos de la ENIGH 2022, del INEGI. '
         'Datos disponibles en: https://www.inegi.org.mx/programas/enigh/nc/2022/.',
         fontsize=8, color=TEXT_COLOR, va='top', fontweight='normal',
         transform=fig.transFigure)

fig.text(0.05, 0.030, 'Notas: ', fontsize=8, color=TEXT_COLOR, va='top',
         fontweight='bold', transform=fig.transFigure)
fig.text(0.082, 0.030,
         'El gasto e ingreso utilizados para los porcentajes son el promedio para '
         'los hogares de cada decil de ingreso que disponen del servicio y gastan en él. '
         'Las cifras de ingresos y gastos no fueron ajustadas por inflación '
         'dado que corresponden a un solo año de encuesta (2022).',
         fontsize=8, color=TEXT_COLOR, va='top', fontweight='normal',
         transform=fig.transFigure)

# ── Exportar ──────────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
output_path = os.path.join(os.path.dirname(__file__), "..", "..", 'output', 'Figura_A10.png')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
fig.savefig(output_path, dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"Figura guardada en: {output_path}")
plt.close(fig)