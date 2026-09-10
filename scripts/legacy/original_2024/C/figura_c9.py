import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

from estilos import COLORES_OPERADORES

# ── 1. LECTURA Y LIMPIEZA ──
df = pd.read_csv(r'C:\Users\ivan-\Documents\GitHub\anuario\datos\C.9\TD_MARKET_SHARE_TELMOVIL_ITE_VA.csv', encoding='latin1')

df['MARKET_SHARE'] = (df['MARKET_SHARE'].astype(str).str.replace('%', '').str.strip())
df['MARKET_SHARE'] = pd.to_numeric(df['MARKET_SHARE'], errors='coerce')

df = df[(df['MES'] == 12) & (df['ANIO'].between(2013, 2023))]

# ── 2. MAPEO ──
def mapear_grupo(nombre):
    if nombre == 'AMÉRICA MÓVIL':
        return 'América Móvil'
    elif nombre == 'TELEFÓNICA':
        return 'Telefónica'
    elif nombre in ('AT&T', 'IUSACELL-UNEFÓN', 'NEXTEL', 'IUSACELL-UNEFÃ“N'):
        return 'AT&T'
    else:
        return 'Otros'

df['GRUPO_FIGURA'] = df['GRUPO'].apply(mapear_grupo)

pivot = df.groupby(['ANIO', 'GRUPO_FIGURA'])['MARKET_SHARE'].sum().unstack(fill_value=0)

orden = ['América Móvil', 'Telefónica', 'AT&T', 'Otros']
pivot = pivot.reindex(columns=orden, fill_value=0)
years = pivot.index.tolist()

# ── 3. CONFIGURACIÓN DE FIGURA (Estilo B.9) ──
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
C_TEXT = '#3c3c3b'

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

x = np.arange(len(years))
bar_w = 0.45 

bottoms = np.zeros(len(years))
bottoms_dict = {}
colores_list = [COLORES_OPERADORES[g] for g in orden]

for grupo, color in zip(orden, colores_list):
    vals = pivot[grupo].values
    bottoms_dict[grupo] = bottoms.copy()
    ax.bar(x, vals, bar_w, bottom=bottoms, color=color, label=grupo, edgecolor='white', linewidth=0.5, zorder=3)
    bottoms += vals

# ── 4. ETIQUETAS CHIPS Y LÍNEAS CODO ──
chip_style = dict(boxstyle="round,pad=0.3,rounding_size=0.6", fc="white", ec="#D1D1DF", lw=1.2)
min_dist = 4.0 

for i, x_val in enumerate(x):
    last_y = -10
    for j, (grupo, color) in enumerate(zip(orden, colores_list)):
        val = pivot[grupo].values[i]
        
        # Umbral idéntico a B.9
        if val >= 0.1: 
            y_center = bottoms_dict[grupo][i] + val / 2
            
            y_text = max(y_center, last_y + min_dist)
            last_y = y_text
            
            x_text = x_val - (bar_w / 2) - 0.12 
            x_target = x_val - (bar_w / 2)
            
            x_elbow = x_text + 0.02 + (j * 0.008) 
            
            ax.plot([x_text, x_elbow, x_elbow, x_target], 
                    [y_text, y_text, y_center, y_center], 
                    color="#A0A0B0", lw=1.2, zorder=3)
            
            chip_text = f"{val:.2f}%"
            ax.annotate(chip_text, xy=(x_text, y_text),
                        ha="right", va="center",
                        bbox=chip_style, color=color, fontweight='bold', fontsize=8,
                        zorder=4)

# ── 5. EJES Y ESTILO ──
ax.set_xticks(x)
ax.set_xticklabels([str(y) for y in years], fontsize=10, fontweight='bold', color=C_TEXT)
ax.tick_params(axis='x', length=0, pad=8) 

ax.set_ylim(0, 105)
ax.set_yticks([]) 

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['bottom'].set_linewidth(1)

# ── 6. ENCABEZADO Y PIE ──
fig.text(0.08, 0.92, '   ', fontsize=2, va='center', bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))
fig.text(0.095, 0.92, 'Figura C.9.', fontsize=14, fontweight='bold', color=C_TEXT, va='center')
fig.text(0.165, 0.92, 'Participación de mercado del servicio móvil de telefonía (2013-2023)', fontsize=14, fontweight='medium', color=C_TEXT, va='center')

handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.08),
           ncol=4, frameon=False, prop={'weight': 'bold', 'size': 10}, labelcolor=C_TEXT)

fig.text(0.08, 0.05, "Fuente:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.115, 0.05, "IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de cada año.", fontsize=8, color=C_TEXT)
fig.text(0.08, 0.03, "Nota:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.108, 0.03, "Participación de mercado calculada con respecto al número de líneas del servicio móvil de telefonía.", fontsize=8, color=C_TEXT)

plt.subplots_adjust(left=0.10, right=0.92, top=0.85, bottom=0.18)

# ── 7. GUARDAR ──
from pathlib import Path
Path('output').mkdir(exist_ok=True)
plt.savefig('output/Figura_C9.png', dpi=200, bbox_inches='tight', facecolor='white')
print("Guardada: output/Figura_C9.png")