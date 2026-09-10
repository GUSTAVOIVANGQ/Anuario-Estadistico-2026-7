"""
Figura C.1 — Espectro radioeléctrico (MHz) asignado por banda de frecuencia
Fuente: IFT con datos a agosto de 2024.
Archivo de entrada: datos/C.1/TD_DIST_ESPECTRO_VA.csv
Salida: output/Figura_C1.png
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
# from _plot_data_logger import enable_plot_data_logging
# enable_plot_data_logging()
from matplotlib.patches import Rectangle
import numpy as np
import os

# Importar estilos centralizados
from estilos import PALETAS, CONFIG_GRAFICA

# ── Configuración de Tipografía y Colores Globales ────────────────────
# Se fuerza el uso de Noto Sans y el color general oscuro de la guía
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

# ── Rutas ─────────────────────────────────────────────────────────────
INPUT  = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\C.1\TD_DIST_ESPECTRO_VA.csv"
OUTPUT = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_C1.png"
os.makedirs(r"C:\Users\ivan-\Documents\GitHub\anuario\output", exist_ok=True)

# ── Leer CSV y filtrar ago-24 ─────────────────────────────────────────
try:
    df = pd.read_csv(INPUT)
    row = df[df["ESTADO"] == "ago-24"].iloc[0]
    total = int(row["B_700_MHZ"] + row["B_800_MHZ"] + row["B_850_MHZ"] +
                row["B_PCS"] + row["B_AWS"] + row["B_2_5_GHZ"] +
                row["B_3_3_GHZ"] + row["B_3_5_GHZ"])
except FileNotFoundError:
    print("CSV no encontrado en esta ruta. Usando total de 645 para renderizar el gráfico.")
    total = 645

# ── Layout manual del treemap (posiciones relativas al PDF) ───────────
fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor(CONFIG_GRAFICA["facecolor_figure"])
ax.set_facecolor(CONFIG_GRAFICA["facecolor_axes"])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

PAD = 0.005 # Espacio fino entre cuadros (gap)

# Paleta monocromática teal de la guía, asignada de mayor a menor MHz
teal = PALETAS["teal"]

celdas = [
    # (nombre, x0, y0, w, h, color)
    ("Banda de\n2500 MHz\n140",  0.00,  0.00, 0.210, 1.00, teal[0]),
    ("Banda AWS\n130",           0.215, 0.00, 0.195, 1.00, teal[1]),
    ("Banda de\n3500 MHz\n100",  0.415, 0.53, 0.245, 0.47, teal[2]),
    ("Banda de\n700 MHz\n90",    0.415, 0.00, 0.245, 0.52, teal[3]),
    ("Banda PCS\n68",            0.665, 0.40, 0.195, 0.60, teal[4]),
    ("Banda de\n850 MHz\n47",    0.665, 0.00, 0.195, 0.39, teal[6]),
    ("Banda de\n3300 MHz\n50",   0.865, 0.40, 0.135, 0.60, teal[5]),
    ("Banda de\n800 MHz\n20",    0.865, 0.00, 0.135, 0.39, teal[7]),
]

for (label, x0, y0, w, h, color) in celdas:
    # Rectángulo con esquinas rectas como el treemap original
    rect = Rectangle(
        (x0 + PAD, y0 + PAD),
        w - 2*PAD, h - 2*PAD,
        linewidth=0,
        facecolor=color,
        zorder=2
    )
    ax.add_patch(rect)

    # Texto centrado en la celda
    cx = x0 + w / 2
    cy = y0 + h / 2

    lines = label.strip().split("\n")
    nombre = "\n".join(lines[:-1])
    mhz    = lines[-1]

    # Etiquetas de datos: Ambas en negritas para cumplir con la legibilidad y la guía
    ax.text(cx, cy + h * 0.10, nombre,
            ha="center", va="center", fontsize=10,
            color="white", fontweight="bold",
            multialignment="center", zorder=3)
    ax.text(cx, cy - h * 0.14, mhz,
            ha="center", va="center", fontsize=16,
            color="white", fontweight="bold", zorder=3)

# ── Título y fuente ───────────────────────────────────────────────────
# Cuadrado decorativo
ax.annotate(' ', xy=(0, 1), xycoords='axes fraction',
            xytext=(0, 30), textcoords='offset points',
            fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

# Número de figura
ax.annotate('Figura C.1.', xy=(0, 1), xycoords='axes fraction',
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color='#3c3c3b')

# Título
ax.annotate('Espectro radioeléctrico (MHz) asignado por banda de frecuencia', xy=(0, 1), xycoords='axes fraction',
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color='#3c3c3b')

# ── Notas al pie ──────────────────────────────────────────────────────────
ax.annotate('Fuente:', xy=(0.08, 0.06), xycoords='figure fraction',
            fontsize=8, fontweight='bold', color='#3c3c3b', va='top')
ax.annotate('IFT con datos a agosto de 2024.',
            xy=(0.08, 0.06), xycoords='figure fraction',
            xytext=(38, 0), textcoords='offset points',
            fontsize=8, fontweight='normal', color='#3c3c3b', va='top')

ax.annotate('Nota:', xy=(0.08, 0.038), xycoords='figure fraction',
            fontsize=8, fontweight='bold', color='#3c3c3b', va='top')
ax.annotate('El tamaño de los cuadros corresponde a los Megahertz asignados por banda de frecuencia. La banda AWS, Advanced Wireless Systems, por sus siglas en inglés corresponde a las bandas\n'
            'de 1.7/2.1 GHz, mientras que la banda PCS, Personal Communications Service, corresponde a la banda de 1900 MHz.',
            xy=(0.08, 0.038), xycoords='figure fraction',
            xytext=(28, 0), textcoords='offset points',
            fontsize=8, fontweight='normal', color='#3c3c3b', va='top')

fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
fig.savefig(OUTPUT, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close(fig)
print(f"Guardado: {OUTPUT}")
print(f"Total MHz (ago-24): {total}")