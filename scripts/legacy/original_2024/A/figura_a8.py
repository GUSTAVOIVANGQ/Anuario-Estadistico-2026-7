# -*- coding: utf-8 -*-
"""
Figura A.8 – Gasto promedio y porcentaje de gasto en Servicios de
Telecomunicaciones Fijas de los hogares por decil de ingreso

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

# ==============================================================================
# 1. CARGA DE MICRODATOS ENIGH 2022
# ==============================================================================
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", 'datos', 'A.7', 'microdatos')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Cargando concentradohogar...")
concentrado = pd.read_csv(
    os.path.join(BASE, 'concentradohogar.csv'), low_memory=False,
    usecols=['folioviv', 'foliohog', 'ing_cor', 'factor', 'comunica'])
concentrado['ing_cor'] = pd.to_numeric(concentrado['ing_cor'], errors='coerce').fillna(0)
concentrado['comunica'] = pd.to_numeric(concentrado['comunica'], errors='coerce').fillna(0)

print("Cargando hogares...")
hogares = pd.read_csv(
    os.path.join(BASE, 'hogares.csv'), low_memory=False,
    usecols=['folioviv', 'foliohog', 'telefono', 'celular', 'tv_paga', 'conex_inte'])

print("Cargando gastoshogar (esto puede tardar)...")
gh = pd.read_csv(os.path.join(BASE, 'gastoshogar.csv'), low_memory=False,
                 usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri', 'gas_nm_tri'])

print("Cargando gastospersona...")
gp = pd.read_csv(os.path.join(BASE, 'gastospersona.csv'), low_memory=False,
                 usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri'])

# ==============================================================================
# 2. GASTO EN TELECOMUNICACIONES FIJAS
# ==============================================================================
FIJAS_CLAVES = ['R005', 'R006', 'R008', 'R009', 'R010', 'R011']
INFLACION_FACTOR = 1.064

gh['gasto'] = (pd.to_numeric(gh['gasto_tri'], errors='coerce').fillna(0)
               + pd.to_numeric(gh['gas_nm_tri'], errors='coerce').fillna(0))
gp['gasto'] = pd.to_numeric(gp['gasto_tri'], errors='coerce').fillna(0)

all_gastos = pd.concat([
    gh[['folioviv', 'foliohog', 'clave', 'gasto']],
    gp[['folioviv', 'foliohog', 'clave', 'gasto']]
])
gf = (all_gastos[all_gastos['clave'].isin(FIJAS_CLAVES)]
      .groupby(['folioviv', 'foliohog'])['gasto'].sum().reset_index())
gf.columns = ['folioviv', 'foliohog', 'gasto_fijas']

# ==============================================================================
# 3. MERGE
# ==============================================================================
print("Procesando datos...")
df = concentrado.merge(hogares, on=['folioviv', 'foliohog'], how='left')
df = df.merge(gf, on=['folioviv', 'foliohog'], how='left')
df['gasto_fijas'] = df['gasto_fijas'].fillna(0)

# ==============================================================================
# 4. DECILES
# ==============================================================================
df = df.sort_values('ing_cor').reset_index(drop=True)
df['cum_factor'] = df['factor'].cumsum()
total_factor = df['factor'].sum()
df['pct_cum'] = df['cum_factor'] / total_factor
df['decil'] = pd.cut(
    df['pct_cum'], bins=np.linspace(0, 1, 11),
    labels=range(1, 11), include_lowest=True
).astype(int)

# ==============================================================================
# 5. INDICADORES Y CÁLCULO POR DECIL
# ==============================================================================
df['tiene_fijas'] = (
    (df['telefono'] == 1) | (df['conex_inte'] == 1) | (df['tv_paga'] == 1)
).astype(int)
df['dg_fijas'] = ((df['tiene_fijas'] == 1) & (df['gasto_fijas'] > 0)).astype(int)

deciles = list(range(1, 11))
gasto_promedio = []
pct_gasto_ingreso = []

for d in deciles:
    sub = df[(df['decil'] == d) & (df['dg_fijas'] == 1)]
    w = sub['factor']
    gasto_mensual  = ((sub['gasto_fijas'] * w).sum() / w.sum() / 3) * INFLACION_FACTOR
    ingreso_mensual = ((sub['ing_cor'] * w).sum() / w.sum() / 3) * INFLACION_FACTOR
    gasto_promedio.append(round(gasto_mensual))
    pct_gasto_ingreso.append(
        round(gasto_mensual / ingreso_mensual * 100, 1) if ingreso_mensual > 0 else 0)

print("\nResultados por decil de ingreso:")
print(f"{'Decil':>5} {'Gasto mensual':>15} {'% Gasto/Ingreso':>17}")
for d, g, p in zip(deciles, gasto_promedio, pct_gasto_ingreso):
    print(f"{d:>5} {f'${g:,}':>15} {f'{p}%':>17}")

# ==============================================================================
# 6. FIGURA  (estilo canónico Figura A.1)
# ==============================================================================
print("\nGenerando figura...")

fig, ax1 = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax1.set_facecolor('#F8F8FA')

x = np.arange(len(deciles))
bar_width = 0.72           # ← mismo ancho que A.1

# ── Eje derecho: barras de gasto ──────────────────────────────────────────────
ax2 = ax1.twinx()

for i, g in enumerate(gasto_promedio):
    ax2.bar(x[i], g, width=bar_width, color=BAR_COLOR, edgecolor='none', zorder=2)

# Etiquetas de gasto dentro de la barra, parte inferior
for i, g in enumerate(gasto_promedio):
    ax2.text(x[i], g * 0.04, f'${g:,}',
             ha='center', va='bottom', fontsize=8,
             fontweight='bold', color='white', zorder=3)

gasto_max  = int(np.ceil(max(gasto_promedio) * 1.15 / 100) * 100)
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

pct_max = float(np.ceil(max(pct_gasto_ingreso) * 1.3 * 2) / 2)
ax1.set_ylim(0, pct_max)
ax1.yaxis.set_major_locator(mticker.MultipleLocator(1.0))
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}%'))
ax1.set_ylabel('% Gasto con respecto al ingreso', fontsize=11, color=TEXT_COLOR,
               labelpad=15)
ax1.tick_params(axis='y', labelsize=9, colors=TEXT_COLOR)

# Puntos y chips de porcentaje
ax1.scatter(x, pct_gasto_ingreso, color=LINE_COLOR, s=50, zorder=5)
for i, pct in enumerate(pct_gasto_ingreso):
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

# ── Encabezado: cuadrado + "Figura A.8." bold + subtítulo medium ─────────────
# Cuadrado decorativo via fig.text con bbox
fig.text(0.044, 0.897, ' ', fontsize=2, va='bottom',
         transform=fig.transFigure,
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2',
                   facecolor='#4a7d75', edgecolor='none'))

# "Figura A.8." bold
fig.text(0.055, 0.895, 'Figura A.8.', fontsize=14, fontweight='bold',
         color=TEXT_COLOR, va='bottom', transform=fig.transFigure)

# Subtítulo normal
fig.text(0.123, 0.895,
         'Gasto promedio y porcentaje de gasto en Servicios de '
         'Telecomunicaciones Fijas de los hogares por decil de ingreso',
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
# Línea 1: Fuente
fig.text(0.05, 0.055, 'Fuente: ', fontsize=8, color=TEXT_COLOR, va='top',
         fontweight='bold', transform=fig.transFigure)
fig.text(0.084, 0.055,
         'IFT con datos de la ENIGH 2022, del INEGI. '
         'Datos disponibles en: https://www.inegi.org.mx/programas/enigh/nc/2022/.',
         fontsize=8, color=TEXT_COLOR, va='top', fontweight='normal',
         transform=fig.transFigure)

# Línea 2: Notas
fig.text(0.05, 0.030, 'Notas: ', fontsize=8, color=TEXT_COLOR, va='top',
         fontweight='bold', transform=fig.transFigure)
fig.text(0.082, 0.030,
         'El gasto e ingreso utilizados para los porcentajes son el promedio para '
         'los hogares de cada decil de ingreso que disponen del servicio y gastan en él. '
         'Las cifras de ingresos y gastos fueron ajustadas con base a la inflación para '
         'reflejar su valor real en términos comparativos.',
         fontsize=8, color=TEXT_COLOR, va='top', fontweight='normal',
         transform=fig.transFigure)

# ── Exportar ─────────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
output_path = os.path.join(OUTPUT_DIR, 'figura_a8.png')
fig.savefig(output_path, dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"\nFigura guardada en: {output_path}")
plt.close(fig)