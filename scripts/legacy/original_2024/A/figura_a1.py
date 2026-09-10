"""
Figura A.1 - Producto Interno Bruto (PIB) y contribución del PIB
de los subsectores de telecomunicaciones y radiodifusión.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os
import numpy as np
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import textwrap

# Configuración de fuente
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

# ── 1. Leer datos ─────────────────────────────────────────────────────────────
base = os.path.join(os.path.dirname(__file__), "..", "..", 'datos', 'A.1', 'tabulados_PIBT')
path = os.path.join(base, 'PIBT_2.xlsx')

try:
    df = pd.read_excel(path, sheet_name='Tabulado', header=None)
except FileNotFoundError:
    print(f"Error: No se encontró el archivo en {path}. Asegúrate de que la ruta sea correcta.")
    sys.exit(1)

# Filas clave (bloque 1: "Millones de pesos a precios de 2018")
ROW_PIB = 7          # Producto interno bruto
ROW_TELECOM = 155    # 517 - Telecomunicaciones
ROW_RADIO_TV = 154   # 515 - Radio y televisión

# ── 2. Extraer datos trimestrales 2013-2024 ──────────────────────────────
quarters_data = []

for year in range(2013, 2025):
    col_start = 1 + (year - 1993) * 7
    max_q = 4 if year < 2024 else 2  # Solo Q1-Q2 para 2024
    for q in range(max_q):
        col = col_start + q
        if col >= df.shape[1]:
            break
        pib_val = df.iloc[ROW_PIB, col]
        tel_val = df.iloc[ROW_TELECOM, col]
        rtv_val = df.iloc[ROW_RADIO_TV, col]
        if pd.notna(pib_val):
            label = f"{year}-T{q+1}"
            quarters_data.append({
                'label': label,
                'year': year,
                'quarter': q + 1,
                'pib': float(pib_val),
                'telecom': float(tel_val) if pd.notna(tel_val) else 0,
                'radio_tv': float(rtv_val) if pd.notna(rtv_val) else 0,
            })

qdf = pd.DataFrame(quarters_data)
qdf['pib_mmdp'] = qdf['pib'] / 1_000
qdf['tyr'] = qdf['telecom'] + qdf['radio_tv']
qdf['pct_tyr'] = qdf['tyr'] / qdf['pib'] * 100

# ── 3. Imprimir tabla ─────────────────────────────────────────────────────────────
print(f"{'Trim':<12} {'PIB (MDP)':>14} {'Telecom':>12} {'Radio/TV':>12} "
      f"{'TyR':>12} {'% TyR':>8}")
print("-" * 75)
for _, r in qdf.iterrows():
    print(f"{r['label']:<12} {r['pib']:>14,.0f} {r['telecom']:>12,.0f} "
          f"{r['radio_tv']:>12,.0f} {r['tyr']:>12,.0f} {r['pct_tyr']:>8.2f}%")

# ── 4. Generar gráfica estilo IFT ────────────────────────────────────────────
fig, ax1 = plt.subplots(figsize=(16, 8.5)) 
fig.patch.set_facecolor('white')
ax1.set_facecolor('#F8F8FA')

n = len(qdf)
x = np.arange(n)

# --- Barras con color claro ---
bar_width = 0.72
for i, (_, row) in enumerate(qdf.iterrows()):
    h = row['pib_mmdp']
    ax1.bar(x[i], h, width=bar_width, color='#86adae', edgecolor='none', zorder=2)

# --- Eje Y izquierdo: PIB (Noto Sans Medium) ---
ax1.set_ylabel("PIB Nacional en miles de millones de pesos", fontsize=11, color='#3c3c3b', labelpad=15)
ax1.set_ylim(0, 30000)
ax1.yaxis.set_major_locator(mticker.MultipleLocator(5000))
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda v, _: f'{int(v):,}'.replace(',', ',')))
ax1.tick_params(axis='y', colors='#3c3c3b', labelsize=9)

# --- Eje X: etiquetas trimestre II y IV debajo, años centrados (Noto Sans Bold) ---
ax1.set_xticks(x)
xlabels = []
for _, row in qdf.iterrows():
    q = int(row['quarter'])
    if q == 2:
        xlabels.append('II')
    elif q == 4:
        xlabels.append('IV')
    else:
        xlabels.append('')
ax1.set_xticklabels(xlabels, fontsize=8, fontweight='normal', color='#3c3c3b')
ax1.tick_params(axis='x', length=3, color='#3c3c3b')

# Etiquetas de año centradas debajo (Noto Sans Bold)
prev_year = None
year_positions = []
for i, (_, row) in enumerate(qdf.iterrows()):
    yr = int(row['year'])
    if yr != prev_year:
        year_start = i
        prev_year = yr
    next_yr = int(qdf.iloc[i + 1]['year']) if i + 1 < n else -1
    if next_yr != yr:
        center = (year_start + i) / 2
        year_positions.append((center, yr))

for cx, yr in year_positions:
    ax1.text(cx, -1700, str(yr), ha='center', va='top',
             fontsize=10, fontweight='bold', color='#3c3c3b')

# --- Eje Y derecho: Participación TyR (Noto Sans Medium) ---
ax2 = ax1.twinx()
pct_vals = qdf['pct_tyr'].values

# Línea oscura
line_color = '#2c3e40'
ax2.plot(x, pct_vals, color=line_color, linewidth=1, zorder=4,
         marker='o', markersize=6, markerfacecolor=line_color, 
         markeredgecolor='none')

ax2.set_ylabel("Porcentaje de participación de los subsectores de las TyR", 
               fontsize=11, color='#3c3c3b', labelpad=20, rotation=90)
ax2.set_ylim(0, 1.8)
ax2.yaxis.set_major_locator(mticker.MultipleLocator(0.2))
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda v, _: f'{v:.1f}%'))
ax2.tick_params(axis='y', colors='#3c3c3b', labelsize=9)

# --- Anotaciones de porcentaje (Chips ovalados en Q2 y Q4) ---
for i, (_, row) in enumerate(qdf.iterrows()):
    q = int(row['quarter'])
    if q == 2 or q == 4:
        pct = row['pct_tyr']
        ax2.annotate(f'{pct:.1f}%', xy=(x[i], pct),
                     xytext=(0, 12), textcoords='offset points',
                     ha='center', va='bottom', fontsize=8,
                     fontweight='bold', color='#3c3c3b',
                     bbox=dict(boxstyle='round,pad=0.3,rounding_size=0.8',
                               facecolor='white', edgecolor=line_color, linewidth=0.8))

# --- Títulos (Estilo Guia_colores.md) ---
# Cuadrado decorativo (#4a7d75)
ax1.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
             xytext=(0, 30), textcoords='offset points',
             va='center', ha='left', fontsize=2,
             bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', 
                       facecolor='#4a7d75', edgecolor='none'))

ax1.annotate("Figura A.1.", xy=(0, 1), xycoords='axes fraction', 
             xytext=(15, 30), textcoords='offset points',
             fontsize=14, fontweight='bold', color='#3c3c3b', ha='left', va='center')

ax1.annotate(" Producto Interno Bruto (PIB) y contribución del PIB de los subsectores de telecomunicaciones y radiodifusión", 
             xy=(0, 1), xycoords='axes fraction', 
             xytext=(95, 30), textcoords='offset points',
             fontsize=14, fontweight='medium', color='#3c3c3b', ha='left', va='center')

# --- Leyenda centrada en la figura ---
bar_patch = mpatches.Patch(facecolor='#86adae', edgecolor='none',
                           label='PIB nacional')
line_patch = plt.Line2D([0], [0], color=line_color, marker='o',
                        markersize=6, markerfacecolor=line_color, 
                        markeredgecolor='none', linewidth=1,
                        label='Participación TyR')

# Centrada horizontalmente usando fig.legend en lugar de ax1.legend
fig.legend(handles=[bar_patch, line_patch], loc='lower center',
           bbox_to_anchor=(0.5, 0.08), ncol=2, fontsize=10,
           frameon=False, handlelength=2.5)

# --- Notas al pie ajustadas para rellenar el largo ---
font_size_notes = 8
color_notes = '#3c3c3b'
x_start = 0.08
l_space = 1.5

# Fuente
y_fuente = 0.06
ax1.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction',
             fontsize=font_size_notes, fontweight='bold', color=color_notes, ha='left', va='top')

# Ajustamos el ancho a 225 para que abarque casi hasta el margen derecho (0.92)
note1_content = ('IFT con datos del INEGI a junio de 2024. '
                 'Datos disponibles en: https://www.inegi.org.mx/temas/pib/.')
note1_wrapped = textwrap.fill(note1_content, width=225)

ax1.annotate(note1_wrapped, xy=(x_start, y_fuente), xycoords='figure fraction',
             xytext=(35, 0), textcoords='offset points',
             fontsize=font_size_notes, fontweight='normal', color=color_notes, ha='left', va='top')

# Notas
y_notas = 0.042
ax1.annotate("Notas: ", xy=(x_start, y_notas), xycoords='figure fraction',
             fontsize=font_size_notes, fontweight='bold', color=color_notes, ha='left', va='top')

note2_content = ('PIB a precios constantes de 2018. La participación de los subsectores de TyR corresponde a la contribución del sector 51 (Información en medios masivos) de acuerdo con el Sistema de Clasificación Industrial de América del Norte, México SCIAN 2023, el cual puede consultarse en Clasificadores - Catálogo SCIAN.')

note2_wrapped = textwrap.fill(note2_content, width=225)

ax1.annotate(note2_wrapped, xy=(x_start, y_notas), xycoords='figure fraction',
             xytext=(32, 0), textcoords='offset points',
             fontsize=font_size_notes, fontweight='normal', color=color_notes, ha='left', va='top', linespacing=l_space)

# --- Ajustes finales de ejes (Color #7c7c7c) ---
ax1.set_xlim(-0.8, n - 0.2)
ax1.spines['top'].set_visible(False)
ax2.spines['top'].set_visible(False)

ax1.spines['bottom'].set_color('#7c7c7c')
ax1.spines['left'].set_color('#7c7c7c')
ax1.spines['right'].set_color('#7c7c7c')
ax2.spines['bottom'].set_color('#7c7c7c')
ax2.spines['left'].set_color('#7c7c7c')
ax2.spines['right'].set_color('#7c7c7c')

# Grid auxiliar solo en el eje Y (Color #d1d1d1, 1pt)
ax1.grid(axis='y', alpha=1.0, color='#d1d1d1', zorder=0, linewidth=1)

# Ajuste de márgenes para dar espacio a la leyenda y footnotes
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# Guardar
output_path = os.path.join(os.path.dirname(__file__), "..", "..", 'output', 'Figura_A1.png')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
fig.savefig(output_path, dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"\nGráfica guardada en: {output_path}")
plt.close(fig)