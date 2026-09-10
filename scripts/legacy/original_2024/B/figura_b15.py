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
INPUT  = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\b.15\TD_ACC_BAFXV_ITE_VA.csv"
OUTPUT = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_B15.png"
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# ─── Lectura y filtro ─────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT, encoding="cp1252")
dic = df[df["MES"] == 12].copy()
dic = dic[(dic["ANIO"] >= 2013) & (dic["ANIO"] <= 2023)]

# ─── Agregación por año ───────────────────────────────────────────────────────────
agg = dic.groupby("ANIO")[
    ["A_V1_E", "A_V2_E", "A_V3_E", "A_V4_E", "A_NO_ESPECIFICADO_E", "A_TOTAL_E"]
].sum()

# ─── Porcentajes ──────────────────────────────────────────────────────────────────
tot = agg["A_TOTAL_E"]
pct = pd.DataFrame({
    "v1": agg["A_V1_E"]               / tot * 100,
    "v2": agg["A_V2_E"]               / tot * 100,
    "v3": agg["A_V3_E"]               / tot * 100,
    "v4": agg["A_V4_E"]               / tot * 100,
    "ns": agg["A_NO_ESPECIFICADO_E"]  / tot * 100,
}, index=agg.index)

years  = pct.index.tolist()
n      = len(years)
x      = np.arange(n)
width  = 0.45  # Mismo ancho que B.17

# ─── Colores y Estilo ─────────────────────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
C_TEXT = '#3c3c3b'

C_V1 = "#6cacad"   # verde claro  — 256 Kbps–1.99 Mbps
C_V2 = "#2D7B8A"   # azul-verde   — 2–9.99 Mbps
C_V3 = "#4a7d75"   # verde medio  — 10–100 Mbps
C_V4 = "#1a4043"   # verde oscuro — >100 Mbps
C_NS = "#728781"   # gris         — Sin información

GRUPOS_B15 = ["v3", "v2", "v1", "v4", "ns"]
COLORES_B15 = [C_V3, C_V2, C_V1, C_V4, C_NS]

# ─── Figura ───────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA') # Fondo institucional

bottoms = np.zeros(len(years))
bottoms_dict = {}

# Trazar barras
for grupo, color in zip(GRUPOS_B15, COLORES_B15):
    vals = pct[grupo].values
    bottoms_dict[grupo] = bottoms.copy()
    ax.bar(x, vals, width, bottom=bottoms, color=color, edgecolor='white', linewidth=0.5, zorder=3)
    bottoms += vals

# ─── Chips con Líneas Cuadradas ───────────────────────────────────────────────────
chip_style = dict(boxstyle="round,pad=0.3,rounding_size=0.6", fc="white", ec="#D1D1DF", lw=1.2)
min_dist = 4.5 # Distancia vertical para evitar colisiones en Y (escala de 0 a 100)

for i, x_val in enumerate(x):
    last_y = -10
    
    for j, (grupo, color) in enumerate(zip(GRUPOS_B15, COLORES_B15)):
        val = pct[grupo].values[i]
        
        if val >= 0.1: # Renderizar solo si >= 0.1%
            y_center = bottoms_dict[grupo][i] + val / 2
            
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
            chip_text = f"{val:.0f}%" if val >= 1 else f"{val:.2f}%"
            ax.annotate(chip_text, xy=(x_text, y_text),
                        ha="right", va="center",
                        bbox=chip_style, color=color, fontweight='bold', fontsize=10,
                        zorder=4)

# ─── Ejes y Decoración ────────────────────────────────────────────────────────────
ax.set_xticks(x)
ax.set_xticklabels([str(y) for y in years], fontsize=10, fontweight='bold', color=C_TEXT)
ax.tick_params(axis='x', length=0, pad=8) 
ax.set_ylim(0, 115)
ax.set_yticks([]) 

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['bottom'].set_linewidth(1)

# Total nacional 2023
total_2023 = int(agg.loc[2023, "A_TOTAL_E"])
ax.text(x[-1], 105, f"Total nacional 2023:\n{total_2023:,}", 
        ha="center", va="bottom", fontsize=10, fontweight="bold", color=C_TEXT,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#D1D1DF", lw=1))

# ─── Encabezado ───────────────────────────────────────────────────────────────────
fig.text(0.08, 0.92, '   ', fontsize=2, va='center',
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))
fig.text(0.095, 0.92, 'Figura B.15.', fontsize=14, fontweight='bold', color=C_TEXT, va='center')
fig.text(0.165, 0.92, 'Distribución de los accesos del Servicio Fijo de Internet por rangos de velocidad (2013-2023)', 
           fontsize=14, fontweight='medium', color=C_TEXT, va='center')

# ─── Leyenda ──────────────────────────────────────────────────────────────────────
patches = [
    mpatches.Patch(color=C_V1, label="256 Kbps y 1.99 Mbps"),
    mpatches.Patch(color=C_V2, label="2 Mbps y 9.99 Mbps"),
    mpatches.Patch(color=C_V3, label="10 Mbps y 100 Mbps"),
    mpatches.Patch(color=C_V4, label="Mayores a 100 Mbps"),
    mpatches.Patch(color=C_NS, label="Sin información"),
]
fig.legend(handles=patches, loc='lower center', bbox_to_anchor=(0.5, 0.08),
           ncol=5, frameon=False, prop={'weight': 'bold', 'size': 10}, labelcolor=C_TEXT)

# ─── Pie de página ────────────────────────────────────────────────────────────────
fig.text(0.08, 0.05, "Fuente:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.115, 0.05, "IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de cada año.", fontsize=8, color=C_TEXT)

plt.subplots_adjust(left=0.10, right=0.92, top=0.85, bottom=0.18)

plt.savefig(OUTPUT, dpi=200, bbox_inches='tight', facecolor='white')
print(f"Guardada: {OUTPUT}")