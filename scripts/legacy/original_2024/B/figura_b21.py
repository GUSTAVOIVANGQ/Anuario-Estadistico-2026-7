import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Polygon
import numpy as np
from pathlib import Path
import sys
from dbfread import DBF

sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ── 1. RUTAS Y DATOS ─────────────────────────────────────────────────────
CSV_ACC   = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\b.21\TD_ACC_TVRES_ITE_VA.csv"
DBF_HOG   = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\b.21\tic_2023_hogares.DBF"
GEOJSON   = r"C:\Users\ivan-\Documents\GitHub\anuario\mexico.json"

ENT_MAP = {
    1: 'Aguascalientes', 2: 'Baja California', 3: 'Baja California Sur', 4: 'Campeche', 5: 'Coahuila de Zaragoza', 6: 'Colima', 7: 'Chiapas', 8: 'Chihuahua', 9: 'Ciudad de México', 10: 'Durango', 11: 'Guanajuato', 12: 'Guerrero', 13: 'Hidalgo', 14: 'Jalisco', 15: 'México', 16: 'Michoacán de Ocampo', 17: 'Morelos', 18: 'Nayarit', 19: 'Nuevo León', 20: 'Oaxaca', 21: 'Puebla', 22: 'Querétaro', 23: 'Quintana Roo', 24: 'San Luis Potosí', 25: 'Sinaloa', 26: 'Sonora', 27: 'Tabasco', 28: 'Tamaulipas', 29: 'Tlaxcala', 30: 'Veracruz de Ignacio de la Llave', 31: 'Yucatán', 32: 'Zacatecas'
}

df_acc = pd.read_csv(CSV_ACC, encoding='latin1')
df_dic = df_acc[(df_acc['ANIO'] == 2023) & (df_acc['MES'] == 12)]
por_entidad = df_dic.groupby('ENTIDAD')['A_RESIDENCIAL_E'].sum().reset_index()
por_entidad.columns = ['ENTIDAD', 'accesos']

tabla = DBF(DBF_HOG, encoding='latin1')
df_hog = pd.DataFrame(iter(tabla))
df_hog['ENT'] = df_hog['ENT'].astype(int)
df_hog['ENTIDAD'] = df_hog['ENT'].map(ENT_MAP)
df_hog['FAC_HOG'] = pd.to_numeric(df_hog['FAC_HOG'], errors='coerce')
hogares = df_hog.groupby('ENTIDAD')['FAC_HOG'].sum().reset_index()
hogares.columns = ['ENTIDAD', 'hogares']

merged = por_entidad.merge(hogares, on='ENTIDAD', how='inner')
merged['penetracion'] = (merged['accesos'] / merged['hogares'] * 100).round(0).astype(int)

# ── 2. ESTILOS GLOBALES Y COLORES ────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
plt.rcParams['text.color'] = '#3c3c3b'

COLORS = ['#afafaf', '#737f7c', '#63918b', '#2d4f4b', '#012f2a']
LABELS = ['Menos de 55', '56 a 65', '66 a 75', '76 a 85', 'Más de 85']
BREAKS = [0, 55, 66, 76, 86, 9999]

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

# ── 3. FIGURA Y MAPA ─────────────────────────────────────────────────────
fig, ax_map = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax_map.set_facecolor('white')
ax_map.axis('off')

merged_geo.plot(ax=ax_map, color=merged_geo['color'], edgecolor='white', linewidth=0.5)
x_min, y_min, x_max, y_max = merged_geo.total_bounds
ax_map.set_xlim(x_min - 100000, x_max + 500000)
ax_map.set_ylim(y_min - 50000, y_max + 50000)

# ── 4. SPEECH BUBBLE "58" ────────────────────────────────────────────────
bx, by = 0.735, 0.56
bw, bh = 0.215, 0.275
fig.add_artist(FancyBboxPatch((bx, by), bw, bh, boxstyle='round,pad=0.015,rounding_size=0.015', linewidth=1.0, edgecolor='#c0c0c0', facecolor='#f7f7f7', transform=fig.transFigure, zorder=6, clip_on=False))
fig.add_artist(Polygon(np.array([[bx + 0.015, by + 0.06], [bx + 0.065, by + 0.06], [bx - 0.018, by - 0.04]]), closed=True, facecolor='#f7f7f7', edgecolor='#c0c0c0', linewidth=1.0, transform=fig.transFigure, zorder=5, clip_on=False))

fig.text(bx + bw / 2, by + bh * 0.80, 'Accesos del servicio de televisión\nrestringida residencial\npor cada 100 hogares:', transform=fig.transFigure, fontsize=9.5, color='#3c3c3b', ha='center', va='center', zorder=7, multialignment='center', clip_on=False)
fig.text(bx + bw / 2, by + bh * 0.37, '58', transform=fig.transFigure, fontsize=60, fontweight='bold', color='#3c3c3b', ha='center', va='center', zorder=7, clip_on=False)
fig.add_artist(plt.Line2D([bx + 0.02, bx + bw - 0.02], [by + bh * 0.60, by + bh * 0.60], transform=fig.transFigure, color='#d0d0d0', linewidth=0.8, zorder=7, clip_on=False))

# ── 5. TÍTULO Y LEYENDA (CORREGIDA) ──────────────────────────────────────
fig.text(0.08, 0.94, ' ', bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'), va='center', fontsize=2)
fig.text(0.093, 0.94, 'Figura B.21.', fontsize=14, fontweight='bold', color='#3c3c3b', va='center')
fig.text(0.165, 0.94, 'Accesos del Servicio de Televisión Restringida Residencial por cada 100 hogares por entidad federativa', fontsize=14, fontweight='medium', color='#3c3c3b', va='center')

leg = ax_map.legend(
    handles=[mpatches.Patch(facecolor=COLORS[i], edgecolor='none', label=LABELS[i]) for i in range(5)],
    title='Accesos del servicio de televisión\nrestringida residencial\npor cada 100 hogares:',
    loc='lower left',
    bbox_to_anchor=(0.08, 0.12),    # ← Posicionamiento estricto a x=0.08
    bbox_transform=fig.transFigure, # ← Anclado a la figura, no al mapa
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
# Alineación estricta a la izquierda para elementos internos de la leyenda
leg._legend_box.align = "left"
leg.get_title().set_multialignment('left')
leg.get_title().set_color('#3c3c3b')

fig.text(0.08, 0.07, 'Fuente:', fontsize=8, fontweight='bold', color='#3c3c3b', ha='left', va='center')
fig.text(0.12, 0.07, 'IFT con datos de los operadores de telecomunicaciones a diciembre de 2023 y de la ENDUTIH 2023 del INEGI.', fontsize=8, fontweight='normal', color='#3c3c3b', ha='left', va='center')

plt.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.15)
os.makedirs('output', exist_ok=True)
plt.savefig('output/Figura_B21.png', dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')