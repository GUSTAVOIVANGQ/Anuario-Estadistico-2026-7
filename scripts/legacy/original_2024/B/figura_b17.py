import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
import sys
import os
import numpy as np

# ─── Configuración del Logger ─────────────────────────────────────────────────────
sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ─── Rutas ────────────────────────────────────────────────────────────────────────
INPUT = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\b.17\TD_MARKET_SHARE_BAF_ITE_VA.csv"
OUTPUT = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_B17.png"
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# --- Cargar y limpiar ---
try:
    df = pd.read_csv(INPUT, encoding='cp1252')
except FileNotFoundError:
    print(f"No se encontró el archivo: {INPUT}")
    sys.exit(1)

df['MS'] = pd.to_numeric(
    df['MARKET_SHARE'].astype(str).str.replace('%', '').str.strip(),
    errors='coerce'
)

df_dic = df[(df['MES'] == 12) & (df['ANIO'] >= 2013) & (df['ANIO'] <= 2023)].copy()

# --- Mapeo a Grupos Institucionales ---
def asignar_grupo(nombre):
    n = str(nombre).upper()
    if 'MÓVIL' in n or 'MOVIL' in n or 'MÃ“VIL' in n or 'TELMEX' in n or 'CABLEMAS' in n or 'TELNOR' in n:
        return 'América Móvil'
    if 'TELEVISA' in n or 'CABLEVISION' in n:
        return 'Grupo Televisa'
    if 'MEGACABLE' in n:
        return 'Megacable-MCM'
    if 'SALINAS' in n or 'TOTALPLAY' in n:
        return 'Grupo Salinas'
    if 'AXTEL' in n:
        return 'Axtel'
    if 'MAXCOM' in n:
        return 'Maxcom'
    if 'CABLECOM' in n:
        return 'Cablecom'
    if nombre == 'IST':
        return 'IST'
    return 'Otros'

df_dic['GRUPO_AGR'] = df_dic['GRUPO'].apply(asignar_grupo)

pivot = df_dic.groupby(['ANIO', 'GRUPO_AGR'])['MS'].sum().unstack(fill_value=0)
pivot.index = pivot.index.astype(int)

# --- Colores Institucionales y Estilo ---
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
C_TEXT = '#3c3c3b'

GRUPOS = ['América Móvil', 'Grupo Televisa', 'Megacable-MCM',
          'Grupo Salinas', 'Axtel', 'Maxcom', 'Cablecom', 'IST', 'Otros']

# Colores definidos extraídos de Guia_colores.md y estilos.py
COLORES_DICT = {
    "América Móvil":  "#1e6284",
    "Grupo Televisa": "#ed8945",
    "Megacable-MCM":  "#5844a0",
    "Grupo Salinas":  "#99b554",
    "Axtel":          "#8e244d",
    "Otros":          "#728781",
    "Maxcom":         "#64a0a1",
    "Cablecom":       "#2d4f4b",
    "IST":            "#b18193",
}
COLORES = [COLORES_DICT[g] for g in GRUPOS]

# --- Configuración de Figura ---
fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA') # Fondo institucional del área del gráfico

years = pivot.index.tolist()
x = np.arange(len(years))
width = 0.45 # Barras más delgadas para dar espacio a los chips

bottoms = np.zeros(len(years))
bottoms_dict = {}

for grupo, color in zip(GRUPOS, COLORES):
    if grupo not in pivot.columns:
        vals = np.zeros(len(years))
    else:
        vals = pivot[grupo].values
    
    bottoms_dict[grupo] = bottoms.copy()
    ax.bar(x, vals, width, bottom=bottoms, color=color, label=grupo, edgecolor='white', linewidth=0.5, zorder=3)
    bottoms += vals

# --- Chips con Líneas Cuadradas ---
chip_style = dict(boxstyle="round,pad=0.3,rounding_size=0.6", fc="white", ec="#D1D1DF", lw=1.2)
min_dist = 4.0 # Distancia vertical mínima en % para evitar solapamiento de chips

for i, x_val in enumerate(x):
    last_y = -10
    
    for j, (grupo, color) in enumerate(zip(GRUPOS, COLORES)):
        if grupo not in pivot.columns:
            continue
        
        val = pivot[grupo].values[i]
        if val >= 0.1: # Mostrar chip solo si es >= 0.1%
            y_center = bottoms_dict[grupo][i] + val / 2
            
            # Prevención de colisiones (apilar visualmente hacia arriba)
            y_text = max(y_center, last_y + min_dist)
            last_y = y_text
            
            # Posicionamiento: alejamos el chip para dar espacio a la línea escalonada
            x_text = x_val - (width / 2) - 0.12  # El chip está pegado a la barra
            x_target = x_val - (width / 2)
            
            # Cálculo del codo (escalonamos por grupo 'j' para que las líneas verticales no se mezclen en un solo bloque sólido)
            x_elbow = x_text + 0.02 + (j * 0.008) # Escalonado apretado
            
            # Trazo manual de la línea cuadrada: Horizontal -> Vertical -> Horizontal
            ax.plot([x_text, x_elbow, x_elbow, x_target], 
                    [y_text, y_text, y_center, y_center], 
                    color="#A0A0B0", lw=1.2, zorder=3)
            
            # Anotación (Solo renderiza la caja, el "arrowprops" ha sido eliminado)
            chip_text = f"{val:.2f}%"
            ax.annotate(chip_text, xy=(x_text, y_text),
                        ha="right", va="center",
                        bbox=chip_style, color=color, fontweight='bold', fontsize=8,
                        zorder=4)

# --- Ejes ---
ax.set_xticks(x)
ax.set_xticklabels([str(y) for y in years], fontsize=10, fontweight='bold', color=C_TEXT)
ax.tick_params(axis='x', length=0, pad=8) # Ticks invisibles

ax.set_ylim(0, 105)
ax.set_yticks([]) # Ocultar eje Y numérico

# Bordes
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['bottom'].set_linewidth(1)

# --- Encabezado ---
fig.text(0.08, 0.92, '   ', fontsize=2, va='center',
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))
fig.text(0.095, 0.92, 'Figura B.17.', fontsize=14, fontweight='bold', color=C_TEXT, va='center')
fig.text(0.165, 0.92, 'Participación de mercado del servicio fijo de Internet (2013-2023)', 
           fontsize=14, fontweight='medium', color=C_TEXT, va='center')

# --- Leyenda ---
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.08),
           ncol=5, frameon=False, prop={'weight': 'bold', 'size': 10}, labelcolor=C_TEXT)

# --- Pie de página ---
fig.text(0.08, 0.05, "Fuente:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.115, 0.05, "Participación de mercado calculada con respecto al número de accesos del servicio fijo de Internet.", fontsize=8, color=C_TEXT)
fig.text(0.08, 0.03, "Nota:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.108, 0.03, "IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de cada año.", fontsize=8, color=C_TEXT)

plt.subplots_adjust(left=0.10, right=0.92, top=0.85, bottom=0.18)

# Guardar figura
plt.savefig(OUTPUT, dpi=200, bbox_inches='tight', facecolor='white')
print(f"Guardada: {OUTPUT}")