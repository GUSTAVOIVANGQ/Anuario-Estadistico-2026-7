import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ── 1. LECTURA Y CÁLCULO ──
CSV = r'C:\Users\ivan-\Documents\GitHub\anuario\datos\C.14\TD_TRAF_INTMOVIL_ITE_VA.csv'
df = pd.read_csv(CSV, encoding='latin-1')

for col in ['TRAF_TB_2G_E', 'TRAF_TB_3G_E', 'TRAF_TB_4G_E', 'TOTAL_TB_E']:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

df_f = df[(df['ANIO'] >= 2015) & (df['ANIO'] <= 2023)]
g = df_f.groupby('ANIO')[['TRAF_TB_2G_E', 'TRAF_TB_3G_E', 'TRAF_TB_4G_E', 'TOTAL_TB_E']].sum()

g['PCT_2G'] = (g['TRAF_TB_2G_E'] / g['TOTAL_TB_E'] * 100).round(1)
g['PCT_3G'] = (g['TRAF_TB_3G_E'] / g['TOTAL_TB_E'] * 100).round(1)
g['PCT_4G'] = (g['TRAF_TB_4G_E'] / g['TOTAL_TB_E'] * 100).round(1)

anios  = g.index.tolist()
h_2g   = g['TRAF_TB_2G_E'].tolist()
h_3g   = g['TRAF_TB_3G_E'].tolist()
h_4g   = g['TRAF_TB_4G_E'].tolist()
total  = g['TOTAL_TB_E'].tolist()

pct_2g = g['PCT_2G'].tolist()
pct_3g = g['PCT_3G'].tolist()
pct_4g = g['PCT_4G'].tolist()

# ── 2. COLORES Y FIGURA ──
COLOR_2G   = '#86adae'
COLOR_3G   = '#4c7d7e'
COLOR_4G   = '#132b2d'
C_TEXT     = '#3c3c3b'

plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

x = np.arange(len(anios))
width = 0.45

# Barras apiladas
ax.bar(x, h_2g, width, color=COLOR_2G, edgecolor='white', linewidth=0.5, zorder=3)
ax.bar(x, h_3g, width, bottom=h_2g, color=COLOR_3G, edgecolor='white', linewidth=0.5, zorder=3)
ax.bar(x, h_4g, width, bottom=[a + b for a, b in zip(h_2g, h_3g)], color=COLOR_4G, edgecolor='white', linewidth=0.5, zorder=3)

# ── 3. ETIQUETAS CHIPS Y LÍNEAS CODO (Escala Absoluta) ──
chip_style = dict(boxstyle="round,pad=0.3,rounding_size=0.6", fc="white", ec="#D1D1DF", lw=1.2)

# La distancia mínima se adapta a la escala masiva del eje Y para evitar traslapes
limite_y = max(total) * 1.15
min_dist = limite_y * 0.04  

for i, x_val in enumerate(x):
    last_y = -limite_y # Inicializar muy por debajo
    
    segmentos = [
        (pct_2g[i], h_2g[i] / 2, COLOR_2G),
        (pct_3g[i], h_2g[i] + h_3g[i] / 2, COLOR_3G),
        (pct_4g[i], h_2g[i] + h_3g[i] + h_4g[i] / 2, COLOR_4G)
    ]
    
    for j, (pct_val, y_center, color) in enumerate(segmentos):
        if pct_val >= 0.1: 
            # Empujar el chip hacia arriba si choca con el anterior
            y_text = max(y_center, last_y + min_dist)
            last_y = y_text
            
            x_text = x_val - (width / 2) - 0.12
            x_target = x_val - (width / 2)
            x_elbow = x_text + 0.02 + (j * 0.008)
            
            # Dibujar la línea que conecta el chip con el segmento
            ax.plot([x_text, x_elbow, x_elbow, x_target],
                    [y_text, y_text, y_center, y_center],
                    color="#A0A0B0", lw=1.2, zorder=3)
            
            # Dibujar el chip
            chip_text = f"{pct_val:.1f}%"
            ax.annotate(chip_text, xy=(x_text, y_text),
                        ha="right", va="center",
                        bbox=chip_style, color=color, fontweight='bold', fontsize=8,
                        zorder=4)

    # Total superior (este se mantiene como texto sobre la barra para no confundir con las particiones)
    ax.text(x_val, total[i] * 1.015, f'{total[i]:,.0f}', ha='center', va='bottom', fontsize=9, color=C_TEXT, fontweight='bold', zorder=4)

# ── 4. EJES Y ESTILO ──
ax.set_xticks(x)
ax.set_xticklabels([str(a) for a in anios], fontsize=10, fontweight='bold', color=C_TEXT)
ax.tick_params(axis='x', length=0, pad=8)
ax.set_ylim(0, limite_y)
ax.set_yticks([])

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)

# ── 5. ENCABEZADO Y PIE ──
fig.text(0.08, 0.92, '   ', fontsize=2, va='center', bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))
fig.text(0.095, 0.92, 'Figura C.14.', fontsize=14, fontweight='bold', color=C_TEXT, va='center')
fig.text(0.170, 0.92, 'Tráfico del servicio móvil de acceso a Internet (2015-2023)', fontsize=14, fontweight='medium', color=C_TEXT, va='center')

patches = [
    mpatches.Patch(color=COLOR_2G, label='Tráfico 2G'),
    mpatches.Patch(color=COLOR_3G, label='Tráfico 3G'),
    mpatches.Patch(color=COLOR_4G, label='Tráfico 4G'),
]
fig.legend(handles=patches, loc='lower center', bbox_to_anchor=(0.5, 0.08), ncol=3, frameon=False, prop={'weight': 'bold', 'size': 10}, labelcolor=C_TEXT)

fig.text(0.08, 0.05, "Fuente:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.115, 0.05, "IFT con datos de los operadores de telecomunicaciones.", fontsize=8, color=C_TEXT)
fig.text(0.08, 0.03, "Nota:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.108, 0.03, "Para cada año los datos se presentan acumulados al mes de diciembre.", fontsize=8, color=C_TEXT)

plt.subplots_adjust(left=0.10, right=0.92, top=0.85, bottom=0.18)

# ── 6. GUARDAR ──
os.makedirs('output', exist_ok=True)
plt.savefig('output/Figura_C14.png', dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print("Guardada: output/Figura_C14.png")