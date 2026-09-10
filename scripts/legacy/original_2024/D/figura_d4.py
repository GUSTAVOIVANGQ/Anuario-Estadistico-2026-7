"""
Figura D.4 — Uso de dispositivos inteligentes conectados a Internet
Fuente: IFT con datos de la ENDUTIH 2023, del INEGI.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()

# ───────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ───────────────────────────────────────────────────────────────────────
RUTA_CSV = Path(r"C:\Users\ivan-\Documents\GitHub\anuario\datos\D.4\tr_endutih_usuarios2_anual_2023.csv")
SALIDA   = Path(r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_D4.png")

# ───────────────────────────────────────────────────────────────────────
# 1. LEER DATOS
# ───────────────────────────────────────────────────────────────────────
print("Leyendo datos…")
df = pd.read_csv(RUTA_CSV, low_memory=False)
df["FAC_PER"] = pd.to_numeric(df["FAC_PER"], errors="coerce")
print(f"  Registros totales : {len(df):>10,}")
print(f"  Población ponderada: {df['FAC_PER'].sum():>15,.0f}")

# ───────────────────────────────────────────────────────────────────────
# 2. DEFINIR VARIABLES Y ORDEN
# ───────────────────────────────────────────────────────────────────────
VARS_IOT = [
    "P9_1_1","P9_1_2","P9_1_3","P9_1_4","P9_1_5",
    "P9_1_6","P9_1_7","P9_1_8","P9_1_9","P9_1_10",
]

ORDEN = [
    ("P9_1_8",  "Dispositivos de\nentretenimiento"),
    ("P9_1_1",  "Bocina o\nasistente del\nhogar"),
    ("P9_1_2",  "Sistemas de\nvideovigilancia"),
    ("P9_1_5",  "Luces o\ninterruptores"),
    ("P9_1_7",  "Electro-\ndomésticos"),
    ("P9_1_6",  "Conexión\neléctrica"),
    ("P9_1_3",  "Puertas o\nventanas con\ncerrado digital"),
    ("P9_1_9",  "Automóvil\no camioneta"),
    ("P9_1_4",  "Dispositivos\nde ahorro de\nenergía eléctrica"),
    ("P9_1_10", "Otros\ndispositivos"),
]

# ───────────────────────────────────────────────────────────────────────
# 3. CALCULAR DENOMINADOR
# ───────────────────────────────────────────────────────────────────────
usa_alguno = (
    df[VARS_IOT]
    .apply(lambda col: col.astype(str).str.strip() == "1")
    .any(axis=1)
)
total_iot = df.loc[usa_alguno, "FAC_PER"].sum()

# ───────────────────────────────────────────────────────────────────────
# 4. CALCULAR PORCENTAJES
# ───────────────────────────────────────────────────────────────────────
variables, etiquetas, porcentajes = [], [], []
for var, etiq in ORDEN:
    mascara = df[var].astype(str).str.strip() == "1"
    pct     = df.loc[mascara, "FAC_PER"].sum() / total_iot * 100
    variables.append(var)
    etiquetas.append(etiq)
    porcentajes.append(pct) # Se guarda sin redondear para mayor precisión gráfica

# ───────────────────────────────────────────────────────────────────────
# 5. GRAFICAR CON ESTILO INSTITUCIONAL (Ref: Figura F.16)
# ───────────────────────────────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

COLOR_BARRA = '#86adae' # Mismo tono verde/teal claro que F.16
color_texto = '#3c3c3b'

x = np.arange(len(etiquetas))
width = 0.55

# Dibujar las barras
bars = ax.bar(x, porcentajes, width, color=COLOR_BARRA, edgecolor='none', zorder=2)

# Etiquetas de datos (Chips estilo F.16)
for rect in bars:
    height = rect.get_height()
    ax.annotate(f'{height:.1f}%',
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 6),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=COLOR_BARRA, linewidth=0.8))

# Diseño limpio de Ejes
ax.set_xticks(x)
ax.set_xticklabels(etiquetas, fontsize=9, fontweight='normal', color=color_texto, linespacing=1.3)
ax.tick_params(axis='x', length=0, pad=8)

ax.set_ylim(0, max(porcentajes) * 1.25)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# Títulos
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura D.4.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Uso de dispositivos inteligentes conectados a Internet", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Notas al pie
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = ('IFT con datos de la ENDUTIH 2023, del INEGI.\n'
               'Datos disponibles en: https://www.inegi.org.mx/programas/endutih/2023/')
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# Guardar
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
SALIDA.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(SALIDA, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"¡Figura D.4 construida y validada con estilo institucional en {SALIDA}!")