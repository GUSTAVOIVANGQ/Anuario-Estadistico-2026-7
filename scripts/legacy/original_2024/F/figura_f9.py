# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
import re
import textwrap

try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ==============================================================================
# 1. CARGA DE DATOS MOCIBA 2023
# ==============================================================================
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", 'datos', 'F.9')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

ruta_archivo = os.path.join(BASE, 'mociba2023_tabulados.xlsx')
if not os.path.exists(ruta_archivo):
    ruta_archivo = r'C:\Users\ivan-\Documents\GitHub\anuario\datos\F.9\mociba2023_tabulados.xlsx'

df = pd.read_excel(ruta_archivo, sheet_name='1.50')

medidas = []
porcentajes = []

for col in range(len(df.columns)):
    if str(df.iloc[15, col]).strip() == 'Relativos':
        nombre = str(df.iloc[14, col-1]).strip()
        if nombre.lower() == 'nan':
            nombre = str(df.iloc[14, col-2]).strip()
            
        nombre = re.sub(r'\d+$', '', nombre).strip()
        valor = df.iloc[17, col]
        
        if pd.notna(valor) and str(valor).strip() != 'NS':
            nombre_wrap = textwrap.fill(nombre, width=45) 
            medidas.append(nombre_wrap)
            porcentajes.append(float(valor))

df_res = pd.DataFrame({'Medida': medidas, 'Porcentaje': porcentajes})
df_res = df_res.sort_values(by='Porcentaje', ascending=True).reset_index(drop=True)

# ==============================================================================
# 2. GRÁFICA ESTILO A.7
# ==============================================================================
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Color institucional replicado
COLOR_BAR = '#335a5c'  # Teal oscuro (mismo que Hombres/Total en A.7)
color_texto = '#3c3c3b'

y = np.arange(len(df_res))
bar_width = 0.5

# Barras horizontales
bars = ax.barh(y, df_res['Porcentaje'], bar_width, color=COLOR_BAR, edgecolor='none', zorder=2)

# Ejes
ax.set_yticks(y)
ax.set_yticklabels(df_res['Medida'], fontsize=9, fontweight='normal', color=color_texto)

ax.set_xlim(0, df_res['Porcentaje'].max() * 1.15) 
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='x', labelsize=9, colors=color_texto)

# Grid y bordes A.7
ax.grid(axis='x', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

# Agregar los % al final de las barras
for i in range(len(df_res)):
    ax.text(df_res['Porcentaje'][i] + 0.5, y[i], f"{df_res['Porcentaje'][i]:.1f}%",
            va='center', ha='left', fontsize=9, color=color_texto, fontweight='normal', zorder=3)

# ==============================================================================
# 3. ENCABEZADO Y NOTAS (BLOQUE INSTITUCIONAL)
# ==============================================================================
# Títulos
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura F.9.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Medidas tomadas contra el ciberacoso experimentado", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(95, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Notas al pie
font_size_notes = 8
x_start = 0.08

y_fuente = 0.06
ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note1_content = 'INEGI. Módulo sobre Ciberacoso (MOCIBA) 2023.'
ax.annotate(note1_content, xy=(x_start, y_fuente), xycoords='figure fraction',
            xytext=(35, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# Ajustes de layout (Aumentado el margen 'left' para los textos largos del eje Y)
fig.subplots_adjust(left=0.28, right=0.92, top=0.85, bottom=0.15)

# Guardar
output_path = os.path.join(OUTPUT_DIR, 'figura_f9.png')
plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"Figura guardada en: {output_path}")
plt.close(fig)