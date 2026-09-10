import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import os
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ── 1. LECTURA Y LIMPIEZA ──
CSV_PATH = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\C.15\TD_MARKET_SHARE_INTMOVIL_ITE_VA.csv"
if not os.path.exists(CSV_PATH):
    print(f"ERROR: No se encontró {CSV_PATH}")
    sys.exit(1)

df = pd.read_csv(CSV_PATH, encoding="latin-1")
df["MS"] = df["MARKET_SHARE"].astype(str).str.replace("%", "").astype(float)

# ── 2. FILTRO ──
df_dic = df[(df["MES"] == 12) & (df["ANIO"] >= 2013) & (df["ANIO"] <= 2023)].copy()

# ── 3. MAPEO ──
def mapear_grupo(k_grupo):
    if k_grupo == "G006":
        return "América Móvil"
    if k_grupo == "G007":
        return "AT&T"
    if k_grupo == "C804":
        return "Grupo Walmart"
    if k_grupo == "G003":
        return "Telefónica"
    return "Otros"

df_dic["GRUPO_FIG"] = df_dic["K_GRUPO"].apply(mapear_grupo)

ORDEN = ["América Móvil", "AT&T", "Grupo Walmart", "Telefónica", "Otros"]

pivot = (
    df_dic.groupby(["ANIO", "GRUPO_FIG"])["MS"]
    .sum()
    .unstack(fill_value=0)
    .reindex(columns=ORDEN, fill_value=0)
)
anios = pivot.index.tolist()

# ── 4. COLORES INSTITUCIONALES (Basado en Guia_colores.md) ──
COLORES = {
    "América Móvil": "#1e6284",
    "AT&T":          "#667489",
    "Grupo Walmart": "#1b4044",  # Mapeado a "Bait" en la guía
    "Telefónica":    "#368491",
    "Otros":         "#728781",
}

# ── 5. CONFIGURACIÓN DE FIGURA (Estilo B.9) ──
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
C_TEXT = '#3c3c3b'

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

x = np.arange(len(anios))
bar_w = 0.45 

bottoms = np.zeros(len(anios))
bottoms_dict = {}
colores_list = [COLORES[g] for g in ORDEN]

# ── 6. DIBUJAR BARRAS ──
for grupo, color in zip(ORDEN, colores_list):
    vals = pivot[grupo].values
    bottoms_dict[grupo] = bottoms.copy()
    ax.bar(x, vals, bar_w, bottom=bottoms, color=color, label=grupo, edgecolor='white', linewidth=0.5, zorder=3)
    bottoms += vals

# ── 7. ETIQUETAS CHIPS Y LÍNEAS CODO ──
chip_style = dict(boxstyle="round,pad=0.3,rounding_size=0.6", fc="white", ec="#D1D1DF", lw=1.2)
min_dist = 4.0 

for i, x_val in enumerate(x):
    last_y = -10
    for j, (grupo, color) in enumerate(zip(ORDEN, colores_list)):
        val = pivot[grupo].values[i]
        
        if val >= 0.1: 
            y_center = bottoms_dict[grupo][i] + val / 2
            
            # Anti-colisión
            y_text = max(y_center, last_y + min_dist)
            last_y = y_text
            
            x_text = x_val - (bar_w / 2) - 0.12 
            x_target = x_val - (bar_w / 2)
            x_elbow = x_text + 0.02 + (j * 0.008) 
            
            # Línea conectora
            ax.plot([x_text, x_elbow, x_elbow, x_target], 
                    [y_text, y_text, y_center, y_center], 
                    color="#A0A0B0", lw=1.2, zorder=3)
            
            # Etiqueta
            chip_text = f"{val:.2f}%"
            ax.annotate(chip_text, xy=(x_text, y_text),
                        ha="right", va="center",
                        bbox=chip_style, color=color, fontweight='bold', fontsize=8,
                        zorder=4)

# ── 8. EJES Y ESTILO ──
ax.set_xticks(x)
ax.set_xticklabels([str(a) for a in anios], fontsize=10, fontweight='bold', color=C_TEXT)
ax.tick_params(axis='x', length=0, pad=8) 

ax.set_ylim(0, 105)
ax.set_yticks([]) 

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)

# ── 9. ENCABEZADO Y PIE ──
fig.text(0.08, 0.92, '   ', fontsize=2, va='center', bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))
fig.text(0.095, 0.92, 'Figura C.15.', fontsize=14, fontweight='bold', color=C_TEXT, va='center')
fig.text(0.165, 0.92, 'Participación de mercado del servicio móvil de acceso a Internet (2013-2023)', fontsize=14, fontweight='medium', color=C_TEXT, va='center')

handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.08),
           ncol=5, frameon=False, prop={'weight': 'bold', 'size': 10}, labelcolor=C_TEXT)

fig.text(0.08, 0.05, "Fuente:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.115, 0.05, "IFT con datos de los operadores de telecomunicaciones a diciembre de cada año.", fontsize=8, color=C_TEXT)
fig.text(0.08, 0.03, "Nota:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.108, 0.03, "Participación de mercado calculada con respecto al número de líneas del servicio móvil de Internet.", fontsize=8, color=C_TEXT)

plt.subplots_adjust(left=0.10, right=0.92, top=0.85, bottom=0.18)

# ── 10. GUARDAR ──
os.makedirs("output", exist_ok=True)
OUTPUT = "output/Figura_C15.png"
plt.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor="white")
plt.savefig("output/Figura_C15.pdf", bbox_inches="tight", facecolor="white")
print(f"Guardada: {OUTPUT}")