import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches

try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# Configuración de fuente general basada en Guia_colores.md
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

# ── 1. Preparar rutas de entrada y salida ────────────────────────────────────
base_dir = os.path.dirname(__file__)
output_dir = os.path.join(base_dir, "..", "..", 'output')
os.makedirs(output_dir, exist_ok=True)

data_path = os.path.join(base_dir, "..", "..", 'datos', 'A.2', 'datos_a2_extracted.csv')

# ── 2. Leer y procesar datos ──────────────────────────────────────────────────
try:
    df = pd.read_csv(data_path)
except FileNotFoundError:
    print(f"Error: No se encontró el archivo en {data_path}. Asegúrate de que la ruta sea correcta.")
    sys.exit(1)

# Calcular porcentajes
df['total'] = df['telecom'] + df['radio']
df['pct_telecom'] = (df['telecom'] / df['total']) * 100
df['pct_radio'] = (df['radio'] / df['total']) * 100

# ── 3. Configuración de colores (Idénticos a figura_a6.py) ──────────────────
color_tel = '#335a5c'  # Teal oscuro (Egresos en A.6)
color_rad = '#86adae'  # Teal claro (Margen en A.6)
color_texto = '#3c3c3b'

# ── 4. Generar gráfica estilo IFT/CRT ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

n = len(df)
x = np.arange(n)
bar_width = 0.72

# --- Barras apiladas sólidas ---
ax.bar(x, df['pct_telecom'], width=bar_width, color=color_tel, 
       edgecolor='none', zorder=2, label='Telecomunicaciones')
ax.bar(x, df['pct_radio'], bottom=df['pct_telecom'], width=bar_width, 
       color=color_rad, edgecolor='none', zorder=2, label='Radiodifusión')

# --- Etiquetas de datos (Chips estilo A.6) y Totales ---
for i, row in df.iterrows():
    p_tel = row['pct_telecom']
    p_rad = row['pct_radio']
    total_val = row['total']

    # Chip Telecomunicaciones (inferior)
    ax.text(
        x[i], p_tel / 2, f"{int(round(p_tel))}%",
        ha="center", va="center", fontsize=8, color=color_texto, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=color_tel, linewidth=0.8),
        zorder=3
    )

    # Chip Radiodifusión (superior)
    ax.text(
        x[i], p_tel + (p_rad / 2), f"{int(round(p_rad))}%",
        ha="center", va="center", fontsize=8, color=color_texto, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=color_tel, linewidth=0.8),
        zorder=3
    )

    # Población Total Ocupada (sobre la barra, estilo cantidad superior A.6)
    ax.text(
        x[i], 102, f"{int(round(total_val)):,}",
        rotation=90, ha="center", va="bottom", fontsize=9, fontweight="normal", color=color_texto
    )

# --- Eje Y: Configuración y estilos ---
ax.set_ylabel('Distribución porcentual del empleo', fontsize=11, fontweight='medium', color=color_texto, labelpad=15)
ax.set_ylim(0, 125)  # Margen superior ajustado para el texto rotado
ax.yaxis.set_major_locator(mticker.MultipleLocator(20))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{int(v)}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

# --- Eje X: Etiquetas trimestre y año (Estilo A.6) ---
quarter_labels = []
for q in df['quarter']:
    if q == 1: quarter_labels.append('I')
    elif q == 2: quarter_labels.append('II')
    elif q == 3: quarter_labels.append('III')
    elif q == 4: quarter_labels.append('IV')
    else: quarter_labels.append('')

ax.set_xticks(x)
ax.set_xticklabels(quarter_labels, fontsize=8, fontweight='normal', color=color_texto)
ax.tick_params(axis='x', length=3, pad=4, colors=color_texto)

# Nivel inferior: años centrados debajo de los trimestres
prev_year = None
year_positions = []
for i, row in df.iterrows():
    yr = int(row['year'])
    if yr != prev_year:
        year_start = i
        prev_year = yr
    next_yr = int(df.iloc[i + 1]['year']) if i + 1 < n else -1
    if next_yr != yr:
        center = (year_start + i) / 2
        year_positions.append((center, yr))

for cx, yr in year_positions:
    ax.text(cx, -9, str(yr), ha='center', va='top', fontsize=10, fontweight='bold', color=color_texto, clip_on=False)

# --- Títulos (Bloque Institucional A.6) ---
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura A.2.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Empleo en los sectores de telecomunicaciones y radiodifusión", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(95, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# --- Leyenda centrada en la figura ---
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.08), ncol=2, fontsize=10, frameon=False, handlelength=2.5)

# --- Notas al pie (Riguroso estilo A.6) ---
font_size_notes = 8
color_notes = '#3c3c3b'
x_start = 0.08
l_space = 1.5

# Fuente
y_fuente = 0.06
ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_notes, ha='left', va='top')

note1_content = ('IFT con datos de la Encuesta Nacional de Ocupación y Empleo (ENOE) del INEGI, con cifras a junio 2024. '
                 'Datos disponibles en: https://www.inegi.org.mx/programas/enoe/15ymas/default.html#Microdatos')
ax.annotate(note1_content, xy=(x_start, y_fuente), xycoords='figure fraction',
            xytext=(35, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_notes, ha='left', va='top')

# Notas
y_notas = 0.042
ax.annotate("Notas: ", xy=(x_start, y_notas), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_notes, ha='left', va='top')

note2_content = 'Para el año 2020 se considera la información al primer y cuarto trimestre.'
ax.annotate(note2_content, xy=(x_start, y_notas), xycoords='figure fraction',
            xytext=(32, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_notes, ha='left', va='top', linespacing=l_space)

# --- Ajustes visuales de Ejes y Grid ---
ax.set_xlim(-0.8, n - 0.2)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)

# Ajuste de márgenes A.6
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# --- Guardar ---
output_path = os.path.join(output_dir, 'Figura_A2.png')
fig.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"\nGráfica guardada en: {output_path}")
plt.close(fig)