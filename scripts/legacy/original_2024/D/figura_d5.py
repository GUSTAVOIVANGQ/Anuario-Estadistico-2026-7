"""
Figura D.5 — ¿Cómo aprendió a buscar información o usar el Internet?
             (Porcentaje de personas usuarias de Internet)

Fuente : IFT, con información de la Encuesta de Confianza en el Servicio de
         Internet (ECSI) 2024.
"""

import os
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
# 1. Rutas
# ───────────────────────────────────────────────────────────────────────
CSV_PATH = Path(r"C:\Users\ivan-\Documents\GitHub\anuario\datos\D.5\baseconfianzadigital.csv")
OUT_DIR  = Path(r"C:\Users\ivan-\Documents\GitHub\anuario\output")

# ───────────────────────────────────────────────────────────────────────
# 2. Carga y filtro
# ───────────────────────────────────────────────────────────────────────
print("Cargando la base de datos...")
df       = pd.read_csv(CSV_PATH, low_memory=False)
usuarios = df[df["rescate_internet"] == 1].copy()

# ───────────────────────────────────────────────────────────────────────
# 3. Variables en el orden del Anuario
# ───────────────────────────────────────────────────────────────────────
VARS = {
    "apren_uso_int_1": "Por su cuenta",
    "apren_uso_int_2": "Capacitación en\nel trabajo",
    "apren_uso_int_3": "Curso en la escuela",
    "apren_uso_int_4": "Curso en\ncentro comunitario",
    "apren_uso_int_5": "Curso particular",
    "apren_uso_int_6": "Amigos o familiares",
    "apren_uso_int_8": "Otros",
    "apren_uso_int_9": "NS/NR",
}

# ───────────────────────────────────────────────────────────────────────
# 4. Cálculo ponderado
# ───────────────────────────────────────────────────────────────────────
total_pond = usuarios["fac_per"].sum()
resultados = {}
for var, etiqueta in VARS.items():
    n = usuarios[usuarios[var] == 1]["fac_per"].sum()
    resultados[etiqueta] = round(n / total_pond * 100, 1)

print("\nValores calculados:")
for etiqueta, pct in resultados.items():
    print(f"  {etiqueta.replace(chr(10),' '):35s}: {pct:.1f}%")

# ───────────────────────────────────────────────────────────────────────
# 5. Estructura para la gráfica
# ───────────────────────────────────────────────────────────────────────
etiquetas = list(resultados.keys())
valores   = list(resultados.values())
x         = np.arange(len(etiquetas))
width     = 0.55

# ───────────────────────────────────────────────────────────────────────
# 6. Gráficar con el estilo institucional (Ref: Figura D.3)
# ───────────────────────────────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Paleta Teal Monocromática (mismos 8 colores de la Figura D.3)
COLORES_CRT = ['#86adae', '#64a0a1', '#5c9596', '#4c7d7e', '#3b6667', '#335a5c', '#234244', '#132b2d']
color_texto = '#3c3c3b'

# Dibujar las barras con la paleta de colores
bars = ax.bar(x, valores, width, color=COLORES_CRT, edgecolor='none', zorder=2)

# Etiquetas de datos (Chips) con borde dinámico
for rect in bars:
    height = rect.get_height()
    bar_color = rect.get_facecolor() # Extrae el color individual para el borde del chip
    ax.annotate(f'{height:.1f}%',
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 6),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

# Diseño limpio de Ejes conforme a D.3
ax.set_xticks(x)
ax.set_xticklabels([])
ax.tick_params(axis='x', length=0, pad=8)

for idx, (group, color) in enumerate(zip(etiquetas, COLORES_CRT)):
    # Desplazamiento horizontal ligeramente ajustado para centrar mejor textos de múltiples líneas
    offset_x_cuadro = 0.30
    offset_x_texto = 0.20
    
    # Cuadrado de color
    ax.annotate('   ', xy=(idx - offset_x_cuadro, -0.04), xycoords=ax.get_xaxis_transform(),
                bbox=dict(boxstyle="round,pad=0.2,rounding_size=0.4", facecolor=color, edgecolor='none'),
                ha='center', va='center')
    # Etiqueta de texto
    ax.annotate(group, xy=(idx - offset_x_texto, -0.04), xycoords=ax.get_xaxis_transform(),
                fontsize=9, fontweight='bold', color=color_texto, ha='left', va='center', linespacing=1.2)

ax.set_ylim(0, max(valores) * 1.25)
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

ax.annotate("Figura D.5.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" ¿Cómo aprendió a buscar información o usar el Internet?", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Notas al pie
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = ('IFT, con información de la Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.\n'
               'Nota: Los porcentajes reportados consideran el diseño muestral de la encuesta.')
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top', linespacing=1.5)

# Guardar
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
OUT_DIR.mkdir(parents=True, exist_ok=True)
out_path = OUT_DIR / "Figura_D5.png"
plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"\n¡Figura D.5 construida y validada con estilo institucional en {out_path}!")