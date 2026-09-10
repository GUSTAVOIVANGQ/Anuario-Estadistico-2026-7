# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys

try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ==============================================================================
# 1. CARGA DE DATOS
# ==============================================================================
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", 'datos', 'b.18')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

ruta_archivo = os.path.join(BASE, 'TD_IHH_BAF_ITE_VA.csv')
if not os.path.exists(ruta_archivo):
    ruta_archivo = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\b.18\TD_IHH_BAF_ITE_VA.csv"

df = pd.read_csv(ruta_archivo, encoding='utf-8')
df['IHH_BAF_E'] = pd.to_numeric(
    df['IHH_BAF_E'].astype(str).str.replace(',', '').str.strip(),
    errors='coerce'
)

df_dic = df[(df['MES'] == 12) & (df['ANIO'] >= 2013) & (df['ANIO'] <= 2023)]
# Ordenar para que el año más reciente (2023) quede arriba, igual que el decil 10 en A.7
df_dic = df_dic.sort_values('ANIO', ascending=False).reset_index(drop=True)

# Usar valores del Anuario donde hay discrepancia
anuario = {2021: 2710, 2022: 2589, 2023: 2693}
df_dic['IHH_plot'] = df_dic.apply(
    lambda r: anuario.get(r['ANIO'], r['IHH_BAF_E']), axis=1
)

# ==============================================================================
# 2. GRÁFICA ESTILO A.7
# ==============================================================================
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Colores replicados de Figura A.9 / A.7
COLOR_BAR = '#335a5c'  # Teal oscuro
color_texto = '#3c3c3b'

years = df_dic['ANIO'].tolist()
values = df_dic['IHH_plot'].tolist()

y = np.arange(len(years))
bar_width = 0.5

# Barras horizontales
bars = ax.barh(y, values, bar_width, color=COLOR_BAR, edgecolor='none', zorder=2)

# Ejes
ax.set_yticks(y)
ax.set_yticklabels([str(y_val) for y_val in years], fontsize=9, fontweight='normal', color=color_texto)
ax.set_ylabel('Año', fontsize=11, fontweight='medium', color=color_texto, labelpad=15)

ax.set_xlim(0, max(values) * 1.15) 
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
ax.tick_params(axis='x', labelsize=9, colors=color_texto)

# Grid y bordes A.7
ax.grid(axis='x', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

# Etiquetas de valor al final de cada barra
for i, val in enumerate(values):
    ax.text(val + 50, y[i], f'{int(val):,}',
            va='center', ha='left', fontsize=9, color=color_texto, fontweight='normal', zorder=3)

# ==============================================================================
# 3. ENCABEZADO Y NOTAS (BLOQUE INSTITUCIONAL)
# ==============================================================================
# Títulos
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura B.18.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Herfindahl-Hirschman (IHH). Concentración de mercado del Servicio Fijo de Internet (2013-2023)", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(110, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Notas al pie
font_size_notes = 8
x_start = 0.08

y_fuente = 0.06
ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note1_content = 'IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de cada año.'
ax.annotate(note1_content, xy=(x_start, y_fuente), xycoords='figure fraction',
            xytext=(35, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.042
ax.annotate("Nota: ", xy=(x_start, y_nota), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note2_content = 'Herfindahl-Hirschman (IHH) estimado con respecto al número de accesos del servicio fijo de Internet.'
ax.annotate(note2_content, xy=(x_start, y_nota), xycoords='figure fraction',
            xytext=(28, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# Ajustes de layout
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# Guardar
output_path = os.path.join(OUTPUT_DIR, 'figura_b18.png')
plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"Figura guardada en: {output_path}")
plt.close(fig)