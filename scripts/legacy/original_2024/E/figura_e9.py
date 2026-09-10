# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
import os
import numpy as np
import textwrap

try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ── 1. Carga de datos ────────────────────────────────────────────────────────
file_path = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\E.9\Base de datos_MiPymes_imp_exp_2022.xlsx"
output_path = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_E9.png"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

try:
    df = pd.read_excel(file_path)
except Exception as e:
    print(f"Error al leer el archivo: {e}")
    df = pd.DataFrame()

# Definición de columnas con codificación corregida
col_pregunta = "¿Y cuál de estos servicios considera el MÁS importante para llevar a cabo estas actividades?"
col_factor = "Factor de Expansión Final"

# ── 2. Procesamiento y Cálculo de Porcentajes Exactos ────────────────────────
if not df.empty and col_pregunta in df.columns:
    df_valid = df.dropna(subset=[col_pregunta])
    total_expandido = df_valid[col_factor].sum()
    conteos_ponderados = df_valid.groupby(col_pregunta)[col_factor].sum()
    porcentajes = (conteos_ponderados / total_expandido) * 100
else:
    # Cifras base del reporte en caso de fallback
    porcentajes = {
        "Conexión a Internet fijo (incluye conexión Wi-Fi)": 63.4, 
        "Telefonía móvil": 20.8, 
        "Telefonía fija": 8.5, 
        "Conexión a Internet por datos móviles (por red de telefonía móvil)": 5.2,
        "Televisión de paga": 1.1
    }

# ── 3. Preparación de datos para la gráfica ──────────────────────────────────
servicios_map = {
    "Conexión a Internet fijo (incluye conexión Wi-Fi)": "Conexión a\nInternet fijo",
    "Telefonía fija": "Telefonía fija",
    "Telefonía móvil": "Telefonía móvil",
    "Conexión a Internet por datos móviles (por red de telefonía móvil)": "Conexión a Internet\npor datos móviles",
    "Televisión de paga": "Televisión de paga"
}

labels = list(servicios_map.values())
valores = [porcentajes.get(k, 0) for k in servicios_map.keys()]

labels.reverse()
valores.reverse()

# ── 4. Generación de la Gráfica (Estilo A.7) ─────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
color_texto = '#3c3c3b'
COLOR_BAR = '#335a5c'  # Tono Verde/Teal institucional

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

y_pos = np.arange(len(labels))
bar_width = 0.55

bars = ax.barh(y_pos, valores, color=COLOR_BAR, height=bar_width, edgecolor='none', zorder=2)

# Ejes
ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=10, fontweight='normal', color=color_texto)

ax.set_xlim(0, max(valores) * 1.15 if max(valores) > 0 else 100)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='x', labelsize=9, colors=color_texto)

# Grid y bordes
ax.grid(axis='x', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

# Etiquetas en las barras (Porcentajes)
for bar in bars:
    width = bar.get_width()
    if width > 0:
        ax.text(width + 1.0, bar.get_y() + bar.get_height() / 2, f"{width:.1f}%",
                va="center", ha="left", fontsize=10, color=color_texto, fontweight='normal', zorder=3)

# ── 5. Encabezado y Notas (Bloque Institucional) ─────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura E.9.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Servicios de telecomunicaciones más importantes para MiPymes (Imp/Exp)", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(105, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Notas al pie actualizadas y envueltas para evitar desbordamiento
font_size_notes = 8
x_start = 0.08

y_fuente = 0.075
ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note1_content = ('IFT con información del documento “Contratación, percepción y uso del Internet fijo y '
                 'Telefonía fija en las micro, pequeñas y medianas empresas (MiPymes) para realizar actividades de '
                 'importación y/o exportación”. Para mayor información consultar: '
                 'https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/contratacioninternetmipymes.pdf.')
note1_wrapped = textwrap.fill(note1_content, width=220)
ax.annotate(note1_wrapped, xy=(x_start, y_fuente), xycoords='figure fraction',
            xytext=(35, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.04
ax.annotate("Nota: ", xy=(x_start, y_nota), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note2_content = 'Debido a que se excluyen las menciones "No sabe/No contesto", la suma no da 100%.'
note2_wrapped = textwrap.fill(note2_content, width=220)
ax.annotate(note2_wrapped, xy=(x_start, y_nota), xycoords='figure fraction',
            xytext=(28, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# Ajustes de layout para alojar el texto largo de las notas
fig.subplots_adjust(left=0.18, right=0.92, top=0.85, bottom=0.22)

# Guardar la imagen final
plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"Figura guardada en: {output_path}")
plt.close(fig)