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
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", 'datos', 'F.6')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

ruta_archivo = os.path.join(BASE, 'mociba2023_tabulados.xlsx')
if not os.path.exists(ruta_archivo):
    ruta_archivo = r'C:\Users\ivan-\Documents\GitHub\anuario\datos\F.6\mociba2023_tabulados.xlsx'

df = pd.read_excel(ruta_archivo, sheet_name='1.25')

col0_limpia = df.iloc[:, 0].fillna('').astype(str).str.strip()
idx_hombres = col0_limpia[col0_limpia == 'Hombres'].index[0]
idx_mujeres = col0_limpia[col0_limpia == 'Mujeres'].index[0]

total_hombres = float(df.iloc[idx_hombres, 1])
total_mujeres = float(df.iloc[idx_mujeres, 1])

absolutos_hombres = df.iloc[idx_hombres+1 : idx_hombres+14, 1].astype(float)
absolutos_mujeres = df.iloc[idx_mujeres+1 : idx_mujeres+14, 1].astype(float)

etiquetas_raw = df.iloc[idx_hombres+1 : idx_hombres+14, 0].astype(str)
etiquetas_limpias = [re.sub(r'\d+$', '', lbl).strip() for lbl in etiquetas_raw]
etiquetas_limpias = [textwrap.fill(lbl, width=45) for lbl in etiquetas_limpias]

pct_hombres = (absolutos_hombres.values / total_hombres) * 100
pct_mujeres = (absolutos_mujeres.values / total_mujeres) * 100

df_res = pd.DataFrame({
    'Situacion': etiquetas_limpias,
    'Hombres': pct_hombres,
    'Mujeres': pct_mujeres
})
# Ordenar de menor a mayor para que los valores más altos queden en la parte superior de la gráfica
df_res = df_res.sort_values(by='Mujeres', ascending=True).reset_index(drop=True)

# ==============================================================================
# 2. GRÁFICA ESTILO A.7
# ==============================================================================
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

y = np.arange(len(df_res))
bar_width = 0.38

# Colores replicados EXACTOS de Figura A.9 / A.7
COLOR_HOMBRES = '#335a5c'  # Teal oscuro
COLOR_MUJERES = '#86adae'  # Teal claro
color_texto = '#3c3c3b'

# Barras horizontales
bars1 = ax.barh(y - bar_width/2, df_res['Hombres'], bar_width, label='Hombres', color=COLOR_HOMBRES, edgecolor='none', zorder=2)
bars2 = ax.barh(y + bar_width/2, df_res['Mujeres'], bar_width, label='Mujeres', color=COLOR_MUJERES, edgecolor='none', zorder=2)

# Ejes
ax.set_yticks(y)
ax.set_yticklabels(df_res['Situacion'], fontsize=9, fontweight='normal', color=color_texto)

ax.set_xlim(0, max(df_res['Hombres'].max(), df_res['Mujeres'].max()) * 1.15) 
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
    ax.text(df_res['Hombres'][i] + 0.5, y[i] - bar_width/2, f"{df_res['Hombres'][i]:.1f}%",
            va='center', ha='left', fontsize=9, color=color_texto, fontweight='normal', zorder=3)
    ax.text(df_res['Mujeres'][i] + 0.5, y[i] + bar_width/2, f"{df_res['Mujeres'][i]:.1f}%",
            va='center', ha='left', fontsize=9, color=color_texto, fontweight='normal', zorder=3)

# ==============================================================================
# 3. ENCABEZADO Y NOTAS (BLOQUE INSTITUCIONAL)
# ==============================================================================
# Títulos
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura F.6.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Distribución porcentual de las situaciones de ciberacoso experimentadas en los últimos 12 meses, por sexo", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(95, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Leyenda
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=2, fontsize=10, frameon=False, handlelength=2.5)

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

# Ajustes de layout (Aumentado el margen 'left' para que quepan las etiquetas largas de texto)
fig.subplots_adjust(left=0.25, right=0.92, top=0.85, bottom=0.22)

# Guardar
output_path = os.path.join(OUTPUT_DIR, 'figura_f6.png')
plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"Figura guardada en: {output_path}")
plt.close(fig)