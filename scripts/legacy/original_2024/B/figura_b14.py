import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Polygon
import numpy as np
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

# ── DATOS Y CONFIGURACIÓN ────────────────────────────────────────────────
df = pd.read_csv('datos/b.14/TD_PENETRACIONES_BAF_ITE_VA.csv', encoding='latin1')
data = dict(zip(df['ENTIDAD'], df['P_BAF_E']))

plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
COLORS = ['#afafaf', '#737f7c', '#63918b', '#2d4f4b', '#012f2a']
LABELS = ['Menos de 28', '28 a 43', '44 a 59', '60 a 75', 'Más de 75']
BREAKS = [0, 28, 44, 60, 76, 9999]

def get_color(val):
    for i in range(len(BREAKS) - 1):
        if BREAKS[i] <= val < BREAKS[i + 1]: return COLORS[i]
    return COLORS[-1]

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GEOJSON_PATH = os.path.join(BASE_DIR, 'datos', 'mexico.json')
gdf = gpd.read_file(GEOJSON_PATH)

NAME_MAPPING = { 'Veracruz': 'Veracruz de Ignacio de la Llave', 'Michoacán': 'Michoacan de Ocampo', 'Coahuila': 'Coahuila de Zaragoza', 'México': 'Mexico.', 'Querétaro': 'Queretaro', 'Yucatán': 'Yucatan' }
gdf['name'] = gdf['name'].replace(NAME_MAPPING)
gdf['valor'] = gdf['name'].map(data).fillna(0)
gdf['color'] = gdf['valor'].apply(get_color)
gdf = gdf.to_crs(epsg=6372)

# ── FIGURA Y MAPA ────────────────────────────────────────────────────────
fig, ax_map = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax_map.set_facecolor('white')
ax_map.axis('off')

gdf.plot(ax=ax_map, color=gdf['color'], edgecolor='white', linewidth=0.5)
x_min, y_min, x_max, y_max = gdf.total_bounds
ax_map.set_xlim(x_min - 100000, x_max + 500000)
ax_map.set_ylim(y_min - 50000, y_max + 50000)

# ── BUBBLES Y CUADROS ────────────────────────────────────────────────────
bx, by, bw, bh = 0.735, 0.56, 0.215, 0.275
fig.add_artist(FancyBboxPatch((bx, by), bw, bh, boxstyle='round,pad=0.015,rounding_size=0.015', linewidth=1.0, edgecolor='#c0c0c0', facecolor='#f7f7f7', transform=fig.transFigure, zorder=6, clip_on=False))
fig.add_artist(Polygon(np.array([[bx + 0.015, by + 0.06], [bx + 0.065, by + 0.06], [bx - 0.018, by - 0.04]]), closed=True, facecolor='#f7f7f7', edgecolor='#c0c0c0', linewidth=1.0, transform=fig.transFigure, zorder=5, clip_on=False))
fig.text(bx + bw / 2, by + bh * 0.80, 'Accesos del servicio fijo de acceso\na Internet No Residencial por cada\n100 unidades económicas:', transform=fig.transFigure, fontsize=9.5, color='#3c3c3b', ha='center', va='center', zorder=7, multialignment='center', clip_on=False)
fig.text(bx + bw / 2, by + bh * 0.37, '47', transform=fig.transFigure, fontsize=60, fontweight='bold', color='#3c3c3b', ha='center', va='center', zorder=7, clip_on=False)
fig.add_artist(plt.Line2D([bx + 0.02, bx + bw - 0.02], [by + bh * 0.60, by + bh * 0.60], transform=fig.transFigure, color='#d0d0d0', linewidth=0.8, zorder=7, clip_on=False))

tx, ty, tw, th = 0.28, 0.155, 0.225, 0.095
fig.add_artist(FancyBboxPatch((tx, ty), tw, th, boxstyle='round,pad=0.012,rounding_size=0.012', linewidth=0, facecolor='#2d4f4b', transform=fig.transFigure, zorder=6, clip_on=False))
fig.add_artist(FancyBboxPatch((tx + 0.008, ty + 0.012), 0.038, th - 0.024, boxstyle='round,pad=0.005,rounding_size=0.008', linewidth=0, facecolor='#012f2a', transform=fig.transFigure, zorder=7, clip_on=False))
icon_cx, icon_cy, icon_hw, icon_hh = tx + 0.027, ty + th / 2, 0.010, 0.020
fig.add_artist(plt.Line2D([icon_cx - icon_hw, icon_cx - icon_hw*0.3, icon_cx + icon_hw*0.3, icon_cx + icon_hw], [icon_cy - icon_hh*0.4,  icon_cy + icon_hh*0.1, icon_cy - icon_hh*0.15, icon_cy + icon_hh*0.55], transform=fig.transFigure, color='white', linewidth=2.0, solid_capstyle='round', solid_joinstyle='round', zorder=8, clip_on=False))
fig.add_artist(plt.Line2D([icon_cx + icon_hw * 0.65, icon_cx + icon_hw], [icon_cy + icon_hh * 0.20, icon_cy + icon_hh * 0.55], transform=fig.transFigure, color='white', linewidth=2.0, solid_capstyle='round', zorder=8, clip_on=False))
text_cx = tx + 0.046 + (tw - 0.046) / 2
fig.text(text_cx, ty + th * 0.65, 'Tasa de crecimiento', transform=fig.transFigure, fontsize=9.5, fontweight='bold', color='white', ha='center', va='center', zorder=7, clip_on=False)
fig.text(text_cx, ty + th * 0.28, 'anual de 4.4%', transform=fig.transFigure, fontsize=9.5, fontweight='bold', color='white', ha='center', va='center', zorder=7, clip_on=False)

# ── TÍTULO Y LEYENDA CORREGIDA ───────────────────────────────────────────
fig.text(0.08, 0.94, ' ', bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'), va='center', fontsize=2)
fig.text(0.093, 0.94, 'Figura B.14.', fontsize=14, fontweight='bold', color='#3c3c3b', va='center')
fig.text(0.165, 0.94, 'Accesos del Servicio Fijo de Internet No Residencial por cada 100 unidades económicas por entidad federativa', fontsize=14, fontweight='medium', color='#3c3c3b', va='center')

leg = ax_map.legend(
    handles=[mpatches.Patch(facecolor=COLORS[i], edgecolor='none', label=LABELS[i]) for i in range(5)],
    title='Accesos del servicio fijo de acceso\na Internet No Residencial por cada\n100 unidades económicas:',
    loc='lower left',
    bbox_to_anchor=(0.08, 0.12),
    bbox_transform=fig.transFigure,
    prop={'weight': 'normal', 'size': 10},
    title_fontproperties={'weight': 'bold', 'size': 10},
    facecolor='white',
    labelcolor='#3c3c3b',
    edgecolor='none',
    framealpha=0.0,
    ncol=1,
    handletextpad=0.5,
    labelspacing=0.3,
    handlelength=1.2,
    borderpad=0.0,
    borderaxespad=0.
)
leg._legend_box.align = "left"
leg.get_title().set_multialignment('left')
leg.get_title().set_color('#3c3c3b')

fig.text(0.08, 0.07, 'Fuente:', fontsize=8, fontweight='bold', color='#3c3c3b', ha='left', va='center')
fig.text(0.11, 0.07, 'IFT con datos de los operadores a diciembre de 2023 y del DENUE del INEGI a noviembre de 2023. proxy dic 2024.', fontsize=8, fontweight='normal', color='#3c3c3b', ha='left', va='center')

plt.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.15)
os.makedirs('output', exist_ok=True)
plt.savefig('output/Figura_B14.png', dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')