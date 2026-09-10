import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import sys
import numpy as np
import os

# ─── Configuración del Logger ─────────────────────────────────────────────────────
sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ─── Rutas ────────────────────────────────────────────────────────────────────────
INPUT  = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\C.2\TD_ESPECTRO_BANDA_VA.csv"
OUTPUT = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_C2.png"
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# ─── Leer CSV ─────────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT)
df = df.set_index("OPERADOR")

# ─── Mapeo columnas CSV → etiquetas ───────────────────────────────────────────────
BANDAS_FINAL = {
    "B_700_MHZ": "700 MHZ",
    "B_800_MHZ": "800 MHZ",
    "B_850_MHZ": "850 MHZ",
    "B_PCS":     "1900 MHZ",
    "B_AWS":     "B_PCS",
    "B_2_5_GHZ": "AWS",
    "B_3_3_GHZ": "2500 MHZ",
    "B_3_5_GHZ": "3500 MHZ",
}

OPERADORES = ["TELCEL", "AT&T", "ALTAN"]
cols = list(BANDAS_FINAL.keys())
etiquetas = list(BANDAS_FINAL.values())
data = df.reindex(OPERADORES)[cols].fillna(0)

# ─── Colores y Estilo ─────────────────────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
C_TEXT = '#3c3c3b'

COLORES = {
    "TELCEL": "#753d6a",   
    "AT&T":   "#667489",   
    "ALTAN":  "#8e244d",   
}

# ─── Figura ───────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA') 

x = np.arange(len(etiquetas))
width = 0.45

bottoms = np.zeros(len(etiquetas))
bar_containers = {}

for op in OPERADORES:
    vals = data.loc[op].values.astype(float)
    bars = ax.bar(x, vals, width, bottom=bottoms, color=COLORES[op], label=op, 
                  edgecolor='white', linewidth=0.5, zorder=3)
    bar_containers[op] = (bars, vals, bottoms.copy())
    bottoms += vals

# ─── Chips con Líneas Cuadradas ───────────────────────────────────────────────────
chip_style = dict(boxstyle="round,pad=0.3,rounding_size=0.6", fc="white", ec="#D1D1DF", lw=1.2)
min_dist = 0.05 # 5% en escala de 0.0 a 1.0 para evitar cruces

for i, x_val in enumerate(x):
    last_y = -0.1
    
    for j, op in enumerate(OPERADORES):
        bars, vals, bots = bar_containers[op]
        v = vals[i]
        
        if v >= 0.01: # Renderizar solo si >= 1%
            y_center = bots[i] + (v / 2)
            
            # Apilar hacia arriba si choca con el chip anterior
            y_text = max(y_center, last_y + min_dist)
            last_y = y_text
            
            # Geometría de la línea
            x_text = x_val - (width / 2) - 0.12
            x_target = x_val - (width / 2)
            x_elbow = x_text + 0.02 + (j * 0.008)
            
            # Línea escalonada
            ax.plot([x_text, x_elbow, x_elbow, x_target], 
                    [y_text, y_text, y_center, y_center], 
                    color="#A0A0B0", lw=1.2, zorder=3)
            
            # Caja de texto (Chip)
            pct_val = int(round(v * 100))
            chip_text = f"{pct_val}%"
            ax.annotate(chip_text, xy=(x_text, y_text),
                        ha="right", va="center",
                        bbox=chip_style, color=COLORES[op], fontweight='bold', fontsize=10,
                        zorder=4)

# ─── Ejes y estilo ────────────────────────────────────────────────────────────────
ax.set_xticks(x)
ax.set_xticklabels(etiquetas, fontsize=10, fontweight='bold', color=C_TEXT)
ax.tick_params(axis='x', length=0, pad=8) 

ax.set_ylim(0, 1.15)
ax.set_yticks([]) 

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['bottom'].set_linewidth(1)

# ─── Encabezado ───────────────────────────────────────────────────────────────────
fig.text(0.08, 0.92, '   ', fontsize=2, va='center',
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))
fig.text(0.095, 0.92, 'Figura C.2.', fontsize=14, fontweight='bold', color=C_TEXT, va='center')
fig.text(0.155, 0.92, 'Distribución del espectro radioeléctrico por operador y por banda de frecuencia', 
           fontsize=14, fontweight='medium', color=C_TEXT, va='center')

# ─── Leyenda ──────────────────────────────────────────────────────────────────────
patches = [mpatches.Patch(color=COLORES[op], label="Altán" if op == "ALTAN" else op.title()) for op in OPERADORES]
fig.legend(handles=patches, loc='lower center', bbox_to_anchor=(0.5, 0.08),
           ncol=3, frameon=False, prop={'weight': 'bold', 'size': 10}, labelcolor=C_TEXT)

# ─── Pie de página ────────────────────────────────────────────────────────────────
fig.text(0.08, 0.05, "Fuente:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.115, 0.05, "IFT con datos a agosto de 2024.", fontsize=8, color=C_TEXT)
fig.text(0.08, 0.03, "Nota:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.108, 0.03, "La banda AWS corresponde a las bandas de 1.7/2.1 GHz; la banda PCS corresponde a la banda de 1900 MHz.", fontsize=8, color=C_TEXT)

plt.subplots_adjust(left=0.10, right=0.92, top=0.85, bottom=0.18)

plt.savefig(OUTPUT, dpi=200, bbox_inches='tight', facecolor='white')
print(f"Guardado: {OUTPUT}")