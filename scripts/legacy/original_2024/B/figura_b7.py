"""
Figura B.7 — Líneas del Servicio Fijo de Telefonía No Residencial
por cada 100 unidades económicas por entidad federativa.

Fuente datos: TD_PENETRACIONES_TELFIJA_ITE_VA.csv (BIT IFT)
Nota: Datos disponibles corresponden a dic 2024 (proxy de dic 2023).
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Polygon
import numpy as np
import geopandas as gpd
from pathlib import Path
import sys
import os
import urllib.request

sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ── 1. RUTAS Y LECTURA DE DATOS ──────────────────────────────────────────
BASE_DIR  = r'C:\Users\ivan-\Documents\GitHub\anuario'
DATA_PATH = os.path.join(BASE_DIR, 'datos', 'B.6', 'TD_PENETRACIONES_TELFIJA_ITE_VA.csv')
OUTPUT_DIR  = os.path.join(BASE_DIR, 'output')
OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'Figura_B7.png')
os.makedirs(OUTPUT_DIR, exist_ok=True)

try:
    df   = pd.read_csv(DATA_PATH, encoding='latin1')
    df   = df[df['ANIO'] == df['ANIO'].max()].copy()
    data = dict(zip(df['ENTIDAD'], df['P_NRES_H_TELFIJA_E']))
except FileNotFoundError:
    print("Aviso: Archivo CSV no encontrado.")
    data = {}

# ── 2. ESTILOS GLOBALES ───────────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
plt.rcParams['text.color']        = '#3c3c3b'
plt.rcParams['axes.labelcolor']   = '#3c3c3b'

# ── 3. RANGOS Y COLORES (paleta gris-verde institucional) ────────────────
COLORS = ['#afafaf', '#737f7c', '#63918b', '#2d4f4b', '#012f2a']
LABELS = ['Menos de 38', '39 a 60', '61 a 97', '98 a 114', 'Más de 114']
BREAKS = [0, 39, 61, 98, 115, 9999]

def get_color(val):
    for i in range(len(BREAKS) - 1):
        if BREAKS[i] <= val < BREAKS[i + 1]:
            return COLORS[i]
    return COLORS[-1]

# ── 4. MAPA DE MÉXICO (GeoPandas) ────────────────────────────────────────
GEOJSON_PATH = os.path.join(BASE_DIR, 'datos', 'mexico.json')
if not os.path.exists(GEOJSON_PATH):
    print("Descargando mapa de México...")
    os.makedirs(os.path.dirname(GEOJSON_PATH), exist_ok=True)
    urllib.request.urlretrieve(
        'https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json',
        GEOJSON_PATH
    )

gdf = gpd.read_file(GEOJSON_PATH)

NAME_MAPPING = {
    'Veracruz':  'Veracruz de Ignacio de la Llave',
    'Michoacán': 'Michoacán de Ocampo',
    'Coahuila':  'Coahuila de Zaragoza',
}
gdf['name']  = gdf['name'].replace(NAME_MAPPING)
gdf['valor'] = gdf['name'].map(data).fillna(0)
gdf['color'] = gdf['valor'].apply(get_color)
gdf = gdf.to_crs(epsg=6372)

# ── 5. FIGURA ─────────────────────────────────────────────────────────────
fig, ax_map = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax_map.set_facecolor('white')
ax_map.axis('off')

# ── 6. DIBUJAR MAPA ──────────────────────────────────────────────────────
gdf.plot(ax=ax_map, color=gdf['color'], edgecolor='white', linewidth=0.5)

x_min, y_min, x_max, y_max = gdf.total_bounds
ax_map.set_xlim(x_min - 100000, x_max + 500000)
ax_map.set_ylim(y_min - 50000,  y_max + 50000)

# ── 7. SPEECH BUBBLE NACIONAL ─────────────────────────────────────────────
nacional_val = data.get('Nacional', 128)

bx, by = 0.735, 0.56
bw, bh = 0.215, 0.275

bubble = FancyBboxPatch(
    (bx, by), bw, bh,
    boxstyle='round,pad=0.015,rounding_size=0.015',
    linewidth=1.0, edgecolor='#c0c0c0', facecolor='#f7f7f7',
    transform=fig.transFigure, zorder=6, clip_on=False
)
fig.add_artist(bubble)

tail_pts = np.array([
    [bx + 0.015, by + 0.06],
    [bx + 0.065, by + 0.06],
    [bx - 0.018, by - 0.04],
])
tail = Polygon(
    tail_pts, closed=True,
    facecolor='#f7f7f7', edgecolor='#c0c0c0', linewidth=1.0,
    transform=fig.transFigure, zorder=5, clip_on=False
)
fig.add_artist(tail)

fig.text(
    bx + bw / 2, by + bh * 0.80,
    'Líneas del servicio fijo de Telefonía\nNo Residencial por cada 100\nunidades económicas:',
    transform=fig.transFigure,
    fontsize=9.5, color='#3c3c3b',
    ha='center', va='center', zorder=7,
    multialignment='center', clip_on=False
)
fig.text(
    bx + bw / 2, by + bh * 0.34,
    f'{int(nacional_val)}',
    transform=fig.transFigure,
    fontsize=58, fontweight='bold', color='#3c3c3b',
    ha='center', va='center', zorder=7, clip_on=False
)

line_y = by + bh * 0.60
fig.add_artist(plt.Line2D(
    [bx + 0.02, bx + bw - 0.02], [line_y, line_y],
    transform=fig.transFigure,
    color='#d0d0d0', linewidth=0.8, zorder=7, clip_on=False
))

# ── 8. RECUADRO TASA DE CRECIMIENTO ──────────────────────────────────────
tx, ty = 0.28, 0.155
tw, th = 0.225, 0.095

growth_box = FancyBboxPatch(
    (tx, ty), tw, th,
    boxstyle='round,pad=0.012,rounding_size=0.012',
    linewidth=0, edgecolor='none', facecolor='#2d4f4b',
    transform=fig.transFigure, zorder=6, clip_on=False
)
fig.add_artist(growth_box)

icon_box = FancyBboxPatch(
    (tx + 0.008, ty + 0.012), 0.038, th - 0.024,
    boxstyle='round,pad=0.005,rounding_size=0.008',
    linewidth=0, facecolor='#012f2a',
    transform=fig.transFigure, zorder=7, clip_on=False
)
fig.add_artist(icon_box)

icon_cx = tx + 0.008 + 0.019
icon_cy = ty + th / 2
icon_hw, icon_hh = 0.010, 0.020
xs = [icon_cx - icon_hw, icon_cx - icon_hw*0.3,
      icon_cx + icon_hw*0.3, icon_cx + icon_hw]
ys = [icon_cy - icon_hh*0.4, icon_cy + icon_hh*0.1,
      icon_cy - icon_hh*0.15, icon_cy + icon_hh*0.55]
fig.add_artist(plt.Line2D(
    xs, ys, transform=fig.transFigure,
    color='white', linewidth=2.0,
    solid_capstyle='round', solid_joinstyle='round',
    zorder=8, clip_on=False
))

text_cx = tx + 0.008 + 0.038 + (tw - 0.008 - 0.038) / 2 + 0.008
fig.text(text_cx, ty + th * 0.65, 'Tasa de crecimiento',
         transform=fig.transFigure,
         fontsize=9.5, fontweight='bold', color='white',
         ha='center', va='center', zorder=7, clip_on=False)
fig.text(text_cx, ty + th * 0.28, 'anual de 13.3%',
         transform=fig.transFigure,
         fontsize=9.5, fontweight='bold', color='white',
         ha='center', va='center', zorder=7, clip_on=False)

# ── 9. TÍTULO ────────────────────────────────────────────────────────────
fig.text(0.08, 0.94, ' ',
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2',
                   facecolor='#4a7d75', edgecolor='none'),
         va='center', fontsize=2)
fig.text(0.093, 0.94, 'Figura B.7.',
         fontsize=14, fontweight='bold', color='#3c3c3b', va='center')
fig.text(0.165, 0.94,
         'Líneas del Servicio Fijo de Telefonía No Residencial por cada 100 unidades económicas por entidad federativa',
         fontsize=14, fontweight='medium', color='#3c3c3b', va='center')

# ── 10. LEYENDA ──────────────────────────────────────────────────────────
legend_patches = [
    mpatches.Patch(facecolor=COLORS[i], edgecolor='none', label=LABELS[i])
    for i in range(5)
]
leg = ax_map.legend(
    handles=legend_patches,
    title='Líneas del servicio fijo de Telefonía\nNo Residencial por cada 100\nunidades económicas:',
    loc='lower left',
    bbox_to_anchor=(0.08, 0.12),
    bbox_transform=fig.transFigure,
    prop={'weight': 'normal', 'size': 10},
    title_fontproperties={'weight': 'bold', 'size': 10},
    facecolor='white', labelcolor='#3c3c3b',
    edgecolor='none', framealpha=0.0,
    ncol=1, handletextpad=0.5, labelspacing=0.3,
    handlelength=1.2, borderpad=0.0, borderaxespad=0.
)
leg._legend_box.align = "left"
leg.get_title().set_multialignment('left')
leg.get_title().set_color('#3c3c3b')

# ── 11. PIE DE FIGURA ─────────────────────────────────────────────────────
fig.text(0.08, 0.07, 'Fuente:',
         fontsize=8, fontweight='bold', color='#3c3c3b', ha='left', va='center')
fig.text(0.115, 0.07,
         'IFT con datos de los operadores de telecomunicaciones a diciembre de 2023 y del DENUE del INEGI, a noviembre de 2023.',
         fontsize=8, fontweight='normal', color='#3c3c3b', ha='left', va='center')
fig.text(0.08, 0.055, 'Nota:',
         fontsize=8, fontweight='bold', color='#3c3c3b', ha='left', va='center')
fig.text(0.108, 0.055,
         'valores graficados son proxy de dic 2024 (diferencia variable por estado respecto a dic 2023).',
         fontsize=8, fontweight='normal', color='#3c3c3b', ha='left', va='center')

plt.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.15)
plt.savefig(OUTPUT_PATH, dpi=200, bbox_inches='tight',
            facecolor=fig.get_facecolor(), edgecolor='none')
print(f"✓ Figura guardada: {OUTPUT_PATH}")