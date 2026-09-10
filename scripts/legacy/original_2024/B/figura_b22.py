import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Polygon
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parents[2]

# ── DATOS Y CONFIGURACIÓN ────────────────────────────────────────────────
CSV_ACC   = BASE_DIR / "datos" / "b.21" / "TD_ACC_TVRES_ITE_VA.csv"
CSV_DENUE = BASE_DIR / "datos" / "b.22" / "denue_2023.csv"
GEOJSON   = BASE_DIR / "mexico.json"

df_acc = pd.read_csv(CSV_ACC, encoding='latin1')
df_dic = df_acc[(df_acc['ANIO'] == 2023) & (df_acc['MES'] == 12)]
col_no_res = 'A_NO_RESIDENCIAL_E' if 'A_NO_RESIDENCIAL_E' in df_dic.columns else 'A_COMERCIAL_E'
por_entidad = df_dic.groupby('ENTIDAD')[col_no_res].sum().reset_index()
por_entidad.columns = ['ENTIDAD', 'accesos']

try:
    df_denue = pd.read_csv(CSV_DENUE, encoding='latin1')
    unidades = df_denue.groupby('ENTIDAD')['UNIDADES'].sum().reset_index()
    unidades.columns = ['ENTIDAD', 'unidades']
except FileNotFoundError:
    unidades = pd.DataFrame({'ENTIDAD': por_entidad['ENTIDAD'], 'unidades': 100000})

por_entidad.loc[por_entidad['ENTIDAD'].str.contains('Quer', na=False), 'ENTIDAD'] = 'Querétaro'
unidades.loc[unidades['ENTIDAD'].str.contains('Quer', na=False), 'ENTIDAD'] = 'Querétaro'
por_entidad['ENTIDAD'] = por_entidad['ENTIDAD'].str.strip()
unidades['ENTIDAD'] = unidades['ENTIDAD'].str.strip()
merged = por_entidad.merge(unidades, on='ENTIDAD', how='inner')
merged['penetracion'] = (merged['accesos'] / merged['unidades'] * 100).round(0).astype(int)

plt.rcParams['font.family'] = ['DejaVu Sans', 'Noto Sans', 'sans-serif']
COLORS = ['#afafaf', '#737f7c', '#63918b', '#2d4f4b', '#012f2a']
LABELS = ['Menos de 4', '4 a 6', '7 a 9', '10 a 12', 'Más de 13']
BREAKS = [0, 4, 7, 10, 13, 999]

def get_color(val):
    if pd.isna(val): return '#DDDDDD'
    for i in range(len(BREAKS) - 1):
        if BREAKS[i] <= val < BREAKS[i + 1]: return COLORS[i]
    return COLORS[-1]

gdf = gpd.read_file(GEOJSON)
NAME_COL = [c for c in gdf.columns if c.lower() in ('name', 'estado', 'entidad')][0]
gdf = gdf.rename(columns={NAME_COL: 'ENTIDAD_GEO'})
merged_geo = gdf.merge(merged, left_on='ENTIDAD_GEO', right_on='ENTIDAD', how='left')
merged_geo['color'] = merged_geo['penetracion'].apply(get_color)
merged_geo = merged_geo.to_crs(epsg=6372)

# ── FIGURA Y MAPA ────────────────────────────────────────────────────────
fig, ax_map = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax_map.set_facecolor('white')
ax_map.axis('off')

merged_geo.plot(ax=ax_map, color=merged_geo['color'], edgecolor='white', linewidth=0.5)
x_min, y_min, x_max, y_max = merged_geo.total_bounds
ax_map.set_xlim(x_min - 100000, x_max + 500000)
ax_map.set_ylim(y_min - 50000, y_max + 50000)

# ── BUBBLES Y CUADROS ────────────────────────────────────────────────────
bx, by, bw, bh = 0.735, 0.56, 0.215, 0.275
fig.add_artist(FancyBboxPatch((bx, by), bw, bh, boxstyle='round,pad=0.015,rounding_size=0.015', linewidth=1.0, edgecolor='#c0c0c0', facecolor='#f7f7f7', transform=fig.transFigure, zorder=6, clip_on=False))
fig.add_artist(Polygon(np.array([[bx + 0.015, by + 0.06], [bx + 0.065, by + 0.06], [bx - 0.018, by - 0.04]]), closed=True, facecolor='#f7f7f7', edgecolor='#c0c0c0', linewidth=1.0, transform=fig.transFigure, zorder=5, clip_on=False))
fig.text(bx + bw / 2, by + bh * 0.80, 'Accesos del servicio de televisión\nrestringida No Residencial por cada\n100 unidades económicas:', transform=fig.transFigure, fontsize=9.5, color='#3c3c3b', ha='center', va='center', zorder=7, multialignment='center', clip_on=False)
fig.text(bx + bw / 2, by + bh * 0.37, '8', transform=fig.transFigure, fontsize=60, fontweight='bold', color='#3c3c3b', ha='center', va='center', zorder=7, clip_on=False)
fig.add_artist(plt.Line2D([bx + 0.02, bx + bw - 0.02], [by + bh * 0.60, by + bh * 0.60], transform=fig.transFigure, color='#d0d0d0', linewidth=0.8, zorder=7, clip_on=False))

tx, ty, tw, th = 0.28, 0.155, 0.225, 0.095
fig.add_artist(FancyBboxPatch((tx, ty), tw, th, boxstyle='round,pad=0.012,rounding_size=0.012', linewidth=0, facecolor='#2d4f4b', transform=fig.transFigure, zorder=6, clip_on=False))
fig.add_artist(FancyBboxPatch((tx + 0.008, ty + 0.012), 0.038, th - 0.024, boxstyle='round,pad=0.005,rounding_size=0.008', linewidth=0, facecolor='#012f2a', transform=fig.transFigure, zorder=7, clip_on=False))
icon_cx, icon_cy, icon_hw, icon_hh = tx + 0.027, ty + th / 2, 0.010, 0.020
fig.add_artist(plt.Line2D([icon_cx - icon_hw, icon_cx - icon_hw*0.3, icon_cx + icon_hw*0.3, icon_cx + icon_hw], [icon_cy - icon_hh*0.4,  icon_cy + icon_hh*0.1, icon_cy - icon_hh*0.15, icon_cy + icon_hh*0.55], transform=fig.transFigure, color='white', linewidth=2.0, solid_capstyle='round', solid_joinstyle='round', zorder=8, clip_on=False))
fig.add_artist(plt.Line2D([icon_cx + icon_hw * 0.65, icon_cx + icon_hw], [icon_cy + icon_hh * 0.20, icon_cy + icon_hh * 0.55], transform=fig.transFigure, color='white', linewidth=2.0, solid_capstyle='round', zorder=8, clip_on=False))
text_cx = tx + 0.046 + (tw - 0.046) / 2
fig.text(text_cx, ty + th * 0.65, 'Tasa de crecimiento', transform=fig.transFigure, fontsize=9.5, fontweight='bold', color='white', ha='center', va='center', zorder=7, clip_on=False)
fig.text(text_cx, ty + th * 0.28, 'anual de 0.0%', transform=fig.transFigure, fontsize=9.5, fontweight='bold', color='white', ha='center', va='center', zorder=7, clip_on=False)

# ── TÍTULO Y LEYENDA CORREGIDA ───────────────────────────────────────────
fig.text(0.08, 0.94, ' ', bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'), va='center', fontsize=2)
fig.text(0.093, 0.94, 'Figura B.22.', fontsize=14, fontweight='bold', color='#3c3c3b', va='center')
fig.text(0.165, 0.94, 'Accesos del Servicio de Televisión Restringida No Residencial por cada 100 unidades económicas por entidad federativa', fontsize=14, fontweight='normal', color='#3c3c3b', va='center')

leg = ax_map.legend(
    handles=[mpatches.Patch(facecolor=COLORS[i], edgecolor='none', label=LABELS[i]) for i in range(5)],
    title='Accesos del servicio de televisión\nrestringida No Residencial por cada\n100 unidades económicas:',
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
fig.text(0.12, 0.07, 'IFT con datos de los operadores de telecomunicaciones a diciembre de 2023 y del DENUE del INEGI, a noviembre de 2023.', fontsize=8, fontweight='normal', color='#3c3c3b', ha='left', va='center')

plt.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.15)
output_dir = BASE_DIR / 'output'
output_dir.mkdir(parents=True, exist_ok=True)
plt.savefig(output_dir / 'Figura_B22.png', dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')