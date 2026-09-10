# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
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
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", 'datos', 'F.7')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

ruta_archivo = os.path.join(BASE, 'mociba2023_tabulados.xlsx')
if not os.path.exists(ruta_archivo):
    ruta_archivo = r'C:\Users\ivan-\Documents\GitHub\anuario\datos\F.7\mociba2023_tabulados.xlsx'

df_hombres = pd.read_excel(ruta_archivo, sheet_name='1.11')
df_mujeres = pd.read_excel(ruta_archivo, sheet_name='1.12')

etiquetas_raw = df_mujeres.iloc[18:26, 0].astype(str)

etiquetas_limpias = []
for lbl in etiquetas_raw:
    lbl_clean = lbl.strip()
    lbl_wrapped = textwrap.fill(lbl_clean, width=35) 
    etiquetas_limpias.append(lbl_wrapped)

pct_hombres = df_hombres.iloc[18:26, 4].astype(float).values
pct_mujeres = df_mujeres.iloc[18:26, 4].astype(float).values

# Invertir el orden para que la medida principal quede hasta arriba
etiquetas_limpias = etiquetas_limpias[::-1]
pct_hombres = pct_hombres[::-1]
pct_mujeres = pct_mujeres[::-1]

# ==============================================================================
# 2. GRÁFICA ESTILO A.7 (Paneles divididos, manteniendo tu tipo de gráfica)
# ==============================================================================
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8.5), sharey=True)
fig.patch.set_facecolor('white')

# Colores institucionales replicados de A.7
COLOR_HOMBRES = '#335a5c' # Teal oscuro
COLOR_MUJERES = '#86adae' # Teal claro
color_texto = '#3c3c3b'

y = np.arange(len(etiquetas_limpias))
bar_width = 0.5 

for ax in (ax1, ax2):
    ax.set_facecolor('#F8F8FA')
    ax.set_xlim(0, 105)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax.tick_params(axis='x', labelsize=9, colors=color_texto)
    ax.grid(axis='x', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#7c7c7c')
    ax.spines['left'].set_color('#7c7c7c')

# --- Panel Izquierdo (Hombres) ---
bars1 = ax1.barh(y, pct_hombres, bar_width, color=COLOR_HOMBRES, edgecolor='none', zorder=2)
ax1.set_title('Hombres', fontsize=11, fontweight='bold', color=color_texto, pad=15)
ax1.set_yticks(y)
ax1.set_yticklabels(etiquetas_limpias, fontsize=9, fontweight='normal', color=color_texto)

for i in range(len(pct_hombres)):
    ax1.text(pct_hombres[i] + 1.5, y[i], f"{pct_hombres[i]:.1f}%",
             va='center', ha='left', fontsize=9, color=color_texto, fontweight='normal', zorder=3)

# --- Panel Derecho (Mujeres) ---
bars2 = ax2.barh(y, pct_mujeres, bar_width, color=COLOR_MUJERES, edgecolor='none', zorder=2)
ax2.set_title('Mujeres', fontsize=11, fontweight='bold', color=color_texto, pad=15)
ax2.tick_params(axis='y', length=0) # Ocultar ticks del eje Y en el panel derecho

for i in range(len(pct_mujeres)):
    ax2.text(pct_mujeres[i] + 1.5, y[i], f"{pct_mujeres[i]:.1f}%",
             va='center', ha='left', fontsize=9, color=color_texto, fontweight='normal', zorder=3)

# ==============================================================================
# 3. ENCABEZADO Y NOTAS (BLOQUE INSTITUCIONAL)
# ==============================================================================
# El título se ancla a ax1 pero como no tiene clip_on se extenderá sobre toda la figura
ax1.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 45), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax1.annotate("Figura F.7.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 45), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax1.annotate(" Medidas de seguridad utilizadas en los dispositivos y/o cuentas, por sexo", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(95, 45), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Notas al pie
font_size_notes = 8
x_start = 0.08

y_fuente = 0.06
fig.text(x_start, y_fuente, "Fuente: ", 
         fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note1_content = 'INEGI. Módulo sobre Ciberacoso (MOCIBA) 2023.'
fig.text(x_start + 0.038, y_fuente, note1_content, 
         fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# Ajustes de layout
fig.subplots_adjust(left=0.22, right=0.92, top=0.82, bottom=0.15, wspace=0.1)

# Guardar
output_path = os.path.join(OUTPUT_DIR, 'figura_f7.png')
plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"Figura guardada en: {output_path}")
plt.close(fig)