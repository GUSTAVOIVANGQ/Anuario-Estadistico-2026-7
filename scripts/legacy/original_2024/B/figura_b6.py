"""
Figura B.6 — Líneas del Servicio Fijo de Telefonía Residencial
por cada 100 hogares por entidad federativa.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Polygon, FancyArrowPatch
import matplotlib.patheffects as pe
import geopandas as gpd
from pathlib import Path
import sys
import os
import urllib.request
import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ── 1. RUTAS Y LECTURA DE DATOS ──────────────────────────────────────────
BASE_DIR = r'C:\Users\ivan-\Documents\GitHub\anuario'
DATA_PATH = os.path.join(BASE_DIR, 'datos', 'B.6', 'TD_PENETRACIONES_TELFIJA_ITE_VA.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'Figura_B6.png')

os.makedirs(OUTPUT_DIR, exist_ok=True)

try:
    df = pd.read_csv(DATA_PATH, encoding='latin1')
    df = df[df['ANIO'] == df['ANIO'].max()].copy()
    data = dict(zip(df['ENTIDAD'], df['P_RES_H_TELFIJA_E']))
except FileNotFoundError:
    print("Aviso: Archivo CSV no encontrado. Se necesita el path correcto.")
    data = {}

# ── 2. ESTILOS GLOBALES (CRT Guía) ───────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
plt.rcParams['text.color'] = '#3c3c3b'
plt.rcParams['axes.labelcolor'] = '#3c3c3b'

# ── 3. RANGOS Y COLORES ──────────────────────────────────────────────────
COLORS = ['#afafaf', '#737f7c', '#63918b', '#2d4f4b', '#012f2a']
LABELS = ['Menos de 29', '29 a 42', '43 a 55', '56 a 68', 'Más de 68']
BREAKS = [0, 29, 43, 56, 69, 999]

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
    'Veracruz': 'Veracruz de Ignacio de la Llave',
    'Michoacán': 'Michoacán de Ocampo',
    'Coahuila': 'Coahuila de Zaragoza',
}
gdf['name'] = gdf['name'].replace(NAME_MAPPING)

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
ax_map.set_ylim(y_min - 50000, y_max + 50000)

# ── 7. SPEECH BUBBLE "53" (esquina superior derecha) ─────────────────────
nacional_val = data.get('Nacional', 53)

# Coordenadas en fig.transFigure
bx, by = 0.735, 0.56   # esquina inferior-izquierda del globo
bw, bh = 0.215, 0.275  # ancho y alto

# Cuerpo redondeado del globo
bubble = FancyBboxPatch(
    (bx, by), bw, bh,
    boxstyle='round,pad=0.015,rounding_size=0.015',
    linewidth=1.0,
    edgecolor='#c0c0c0',
    facecolor='#f7f7f7',
    transform=fig.transFigure,
    zorder=6,
    clip_on=False
)
fig.add_artist(bubble)

# Cola del globo (triángulo apuntando abajo-izquierda hacia el mapa)
tail_pts = np.array([
    [bx + 0.015, by + 0.06],   # base izquierda
    [bx + 0.065, by + 0.06],   # base derecha
    [bx - 0.018, by - 0.04],   # punta
])
tail = Polygon(
    tail_pts,
    closed=True,
    facecolor='#f7f7f7',
    edgecolor='#c0c0c0',
    linewidth=1.0,
    transform=fig.transFigure,
    zorder=5,
    clip_on=False
)
fig.add_artist(tail)

# Texto: subtítulo dentro del globo
fig.text(
    bx + bw / 2, by + bh * 0.80,
    'Líneas del servicio fijo de Telefonía\nResidencial por cada 100 hogares:',
    transform=fig.transFigure,
    fontsize=9.5, color='#3c3c3b',
    ha='center', va='center', zorder=7,
    multialignment='center',
    clip_on=False
)

# Número grande
fig.text(
    bx + bw / 2, by + bh * 0.37,
    f'{int(nacional_val)}',
    transform=fig.transFigure,
    fontsize=60, fontweight='bold', color='#3c3c3b',
    ha='center', va='center', zorder=7,
    clip_on=False
)

# Línea separadora sutil
line_y = by + bh * 0.60
fig.add_artist(plt.Line2D(
    [bx + 0.02, bx + bw - 0.02], [line_y, line_y],
    transform=fig.transFigure,
    color='#d0d0d0', linewidth=0.8, zorder=7, clip_on=False
))

# ── 8. RECUADRO OSCURO "TASA DE CRECIMIENTO" ─────────────────────────────
# Posicionado en la parte inferior-central sobre el mapa
tx, ty = 0.28, 0.155
tw, th = 0.225, 0.095

# Fondo oscuro
growth_box = FancyBboxPatch(
    (tx, ty), tw, th,
    boxstyle='round,pad=0.012,rounding_size=0.012',
    linewidth=0,
    edgecolor='none',
    facecolor='#2d4f4b',
    transform=fig.transFigure,
    zorder=6,
    clip_on=False
)
fig.add_artist(growth_box)

# Cuadro ícono (izquierda, color más oscuro)
icon_box = FancyBboxPatch(
    (tx + 0.008, ty + 0.012), 0.038, th - 0.024,
    boxstyle='round,pad=0.005,rounding_size=0.008',
    linewidth=0,
    facecolor='#012f2a',
    transform=fig.transFigure,
    zorder=7,
    clip_on=False
)
fig.add_artist(icon_box)

# Línea de tendencia (ícono mini chart) — dibujada a mano con lines
icon_cx = tx + 0.008 + 0.019  # centro x del ícono
icon_cy = ty + th / 2          # centro y
icon_hw = 0.010                # mitad ancho
icon_hh = 0.020                # mitad alto
# Línea en zigzag ascendente
xs = [icon_cx - icon_hw, icon_cx - icon_hw*0.3, icon_cx + icon_hw*0.3, icon_cx + icon_hw]
ys = [icon_cy - icon_hh*0.4,  icon_cy + icon_hh*0.1, icon_cy - icon_hh*0.15, icon_cy + icon_hh*0.55]
fig.add_artist(plt.Line2D(
    xs, ys,
    transform=fig.transFigure,
    color='white', linewidth=2.0, solid_capstyle='round', solid_joinstyle='round',
    zorder=8, clip_on=False
))
# Punto final (flecha implícita)
fig.add_artist(plt.Line2D(
    [icon_cx + icon_hw * 0.65, icon_cx + icon_hw],
    [icon_cy + icon_hh * 0.20, icon_cy + icon_hh * 0.55],
    transform=fig.transFigure,
    color='white', linewidth=2.0, solid_capstyle='round',
    zorder=8, clip_on=False
))

# Texto: "Tasa de crecimiento" en blanco
text_cx = tx + 0.008 + 0.038 + (tw - 0.008 - 0.038) / 2 + 0.008
fig.text(
    text_cx, ty + th * 0.65,
    'Tasa de crecimiento',
    transform=fig.transFigure,
    fontsize=9.5, fontweight='bold', color='white',
    ha='center', va='center', zorder=7, clip_on=False
)
fig.text(
    text_cx, ty + th * 0.28,
    'anual de 1.9%',
    transform=fig.transFigure,
    fontsize=9.5, fontweight='bold', color='white',
    ha='center', va='center', zorder=7, clip_on=False
)

# ── 9. TÍTULO ────────────────────────────────────────────────────────────
fig.text(0.08, 0.94, ' ', 
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'),
         va='center', fontsize=2)

fig.text(0.093, 0.94, 'Figura B.6.', 
         fontsize=14, fontweight='bold', color='#3c3c3b', va='center')

fig.text(0.165, 0.94, 'Líneas del Servicio Fijo de Telefonía Residencial por cada 100 hogares por entidad federativa', 
         fontsize=14, fontweight='medium', color='#3c3c3b', va='center')

# ── 10. LEYENDA ──────────────────────────────────────────────────────────
legend_patches = [
    mpatches.Patch(facecolor=COLORS[i], edgecolor='none', label=LABELS[i])
    for i in range(5)
]

leg = ax_map.legend(
    handles=legend_patches,
    title='Líneas del servicio fijo de Telefonía\nResidencial por cada 100 hogares:',
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

# ── 11. PIE DE FIGURA ─────────────────────────────────────────────────────
fig.text(0.08, 0.07, 'Fuente:', 
         fontsize=8, fontweight='bold', color='#3c3c3b', ha='left', va='center')

fig.text(0.11, 0.07, 'IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de 2023 y de la ENDUTIH 2023 del INEGI.', 
         fontsize=8, fontweight='normal', color='#3c3c3b', ha='left', va='center')

plt.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.15)

plt.savefig(OUTPUT_PATH, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
print(f"Figura guardada: {OUTPUT_PATH}")