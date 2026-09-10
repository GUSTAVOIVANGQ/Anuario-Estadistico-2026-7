"""
Figura A.3 – Índices de precios (INPC e IPCOM)

Reproduce la gráfica del Anuario Estadístico 2024 del IFT (p. 13) 
adaptada a la Guía de Estilos de la CRT (versión solo gráfica, sin banner).
"""

import csv
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# Configuración global de tipografía requerida por la CRT
plt.rcParams['font.family'] = 'Noto Sans'

# ── 1. Leer datos ─────────────────────────────────────────────────────────────
base = os.path.join(os.path.dirname(__file__), "..", "..", 'datos', 'A.3')
csv_path = os.path.join(base, 'INP_INP20260310133506.CSV')

rows_data = []
with open(csv_path, 'r', encoding='latin-1') as f:
    reader = csv.reader(f)
    months = ('Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
              'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic')
    for row in reader:
        if len(row) == 14 and row[0].strip()[:3] in months:
            rows_data.append(row)

# ── 2. Filtrar: diciembre 2010-2023 + julio 2024 ─────────────────────────────
selected = []
for row in rows_data:
    fecha = row[0].strip()
    if fecha.startswith('Dic'):
        year = int(fecha.split()[1])
        if 2010 <= year <= 2023:
            selected.append((str(year), float(row[1]), float(row[9])))
    elif fecha == 'Jul 2024':
        selected.append(('2024*', float(row[1]), float(row[9])))

# Ordenar por año
selected.sort(key=lambda t: int(t[0].replace('*', '')))

years = [s[0] for s in selected]
inpc = [s[1] for s in selected]
ipcom = [s[2] for s in selected]

# ── 3. Generar gráfica estilo CRT ──────────────────────────────────────────────
# Tamaño estándar para la gráfica limpia
fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

x = np.arange(len(years))

# Colores sugeridos por la guía
color_inpc = '#006157'   # Verde institucional
color_ipcom = '#b35aba'  # Morado

# Líneas (Corregidas: sin borde blanco en los marcadores)
ax.plot(x, inpc, color=color_inpc, linewidth=2.5, zorder=4,
        marker='o', markersize=6, markerfacecolor=color_inpc,
        markeredgecolor=color_inpc, markeredgewidth=0,
        label='Índice Nacional de Precios al Consumidor (INPC)')

ax.plot(x, ipcom, color=color_ipcom, linewidth=2.5, zorder=4,
        marker='o', markersize=6, markerfacecolor=color_ipcom,
        markeredgecolor=color_ipcom, markeredgewidth=0,
        label='Índice de Precios de Comunicaciones (IPCOM)')

# Etiquetas de datos (Evitando colisiones y con estilo chip/cuadrado redondeado)
for i_idx in range(len(years)):
    # Lógica para invertir posiciones después del cruce de líneas
    if inpc[i_idx] >= ipcom[i_idx]:
        offset_inpc, va_inpc = 12, 'bottom'   # INPC arriba
        offset_ipcom, va_ipcom = -16, 'top'   # IPCOM abajo
    else:
        offset_inpc, va_inpc = -16, 'top'     # INPC abajo
        offset_ipcom, va_ipcom = 12, 'bottom' # IPCOM arriba

    bbox_inpc = dict(boxstyle='round,pad=0.3,rounding_size=0.8',
                     facecolor='white', edgecolor=color_inpc, linewidth=0.8)
    bbox_ipcom = dict(boxstyle='round,pad=0.3,rounding_size=0.8',
                      facecolor='white', edgecolor=color_ipcom, linewidth=0.8)

    # Etiqueta INPC
    ax.annotate(f'{round(inpc[i_idx])}', xy=(x[i_idx], inpc[i_idx]),
                xytext=(0, offset_inpc), textcoords='offset points',
                ha='center', va=va_inpc, fontsize=8, fontweight='bold',
                color='#3c3c3b', bbox=bbox_inpc)
    # Etiqueta IPCOM
    ax.annotate(f'{round(ipcom[i_idx])}', xy=(x[i_idx], ipcom[i_idx]),
                xytext=(0, offset_ipcom), textcoords='offset points',
                ha='center', va=va_ipcom, fontsize=8, fontweight='bold',
                color='#3c3c3b', bbox=bbox_ipcom)

# Ejes (Color de texto general #3c3c3b)
ax.set_ylim(60, 170)
ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
ax.tick_params(axis='y', labelsize=10, colors='#3c3c3b') 

# Forzar Medium en el eje Y
for label in ax.get_yticklabels():
    label.set_fontweight('medium')

ax.set_xticks(x)
ax.set_xticklabels(years, fontsize=10, color='#3c3c3b', fontweight='bold')

# Eliminar los ticks sobresalientes en X y separar ligeramente el texto
ax.tick_params(axis='x', length=0, color='#7c7c7c', pad=8)

# Cuadrícula (Línea auxiliar ejes: 1 pt #d1d1d1)
ax.grid(axis='y', color='#d1d1d1', linewidth=1, zorder=0)

# Bordes (Línea base y ejes principales: 1 pt #7c7c7c)
for spine in ax.spines.values():
    spine.set_color('#7c7c7c')
    spine.set_linewidth(1)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# ── 4. Título ────────────────────────────────────────────────────────────────
# Cuadrado decorativo
ax.annotate(' ', xy=(0, 1), xycoords='axes fraction',
            xytext=(0, 34), textcoords='offset points',
            fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

# Número de figura
ax.annotate('Figura A.3.', xy=(0, 1), xycoords='axes fraction',
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color='#3c3c3b')

# Título
ax.annotate('Índices de precios (INPC e IPCOM)', xy=(0, 1), xycoords='axes fraction',
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color='#3c3c3b')

# ── 5. Leyenda ───────────────────────────────────────────────────────────────
fig.legend(loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=2,
           frameon=False, handlelength=2.5, labelcolor='#3c3c3b',
           prop={'weight': 'bold', 'size': 10})

# ── 6. Notas al pie ──────────────────────────────────────────────────────────
ax.annotate('Fuente:', xy=(0.08, 0.06), xycoords='figure fraction',
            fontsize=8, fontweight='bold', color='#3c3c3b')
ax.annotate('IFT con datos del INEGI a julio de 2024. Datos disponibles en: '
            'https://www.inegi.org.mx/app/indicesdeprecios/',
            xy=(0.08, 0.06), xycoords='figure fraction',
            xytext=(35, 0), textcoords='offset points',
            fontsize=8, fontweight='normal', color='#3c3c3b')

ax.annotate('Notas:', xy=(0.08, 0.042), xycoords='figure fraction',
            fontsize=8, fontweight='bold', color='#3c3c3b')
ax.annotate('Base julio 2018 = 100. Los índices de 2010 a 2023 corresponden '
            'a diciembre de cada año, mientras que para el año 2024 a julio.',
            xy=(0.08, 0.042), xycoords='figure fraction',
            xytext=(32, 0), textcoords='offset points',
            fontsize=8, fontweight='normal', color='#3c3c3b')

# ── 7. Guardar ───────────────────────────────────────────────────────────────
# Ajustes de márgenes para la versión sin banner
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

output_path = os.path.join(os.path.dirname(__file__), "..", "..", 'output', 'Figura_A3.png')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
fig.savefig(output_path, dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"\nGráfica guardada en: {output_path}")
plt.close(fig)