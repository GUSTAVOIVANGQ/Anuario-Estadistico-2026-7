"""
Figura D.2 — Uso de Smartphone e Internet por grupos de edad (2023)
Fuente: INEGI, ENDUTIH 2023

Archivo de entrada:
  tr_endutih_usuarios_anual_2023.csv
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import os
import numpy as np

# ── Rutas ───────────────────────────────────────────────────────────────────────
CSV_PATH = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\D.2\tr_endutih_usuarios_anual_2023.csv"
OUTPUT   = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_D2.png"

# ── 1. Lectura ────────────────────────────────────────────────────────────────
print("Leyendo CSV...")
df = pd.read_csv(
    CSV_PATH,
    usecols=['EDAD', 'P6_3', 'P6_4', 'P7_3', 'FAC_PER'],
    dtype=str
)
df['EDAD']    = pd.to_numeric(df['EDAD'],    errors='coerce')
df['FAC_PER'] = pd.to_numeric(df['FAC_PER'], errors='coerce')
print(f"  Registros leídos : {len(df):,}")
print(f"  Suma FAC_PER     : {df['FAC_PER'].sum():,.0f}")

# ── 2. Filtro: personas de 6 años o más ──────────────────────────────────────
df = df[df['EDAD'] >= 6].copy()

# ── 3. Indicadores binarios ──────────────────────────────────────────────────
df['internet']   = (df['P6_3'].str.strip() != '2').astype(int)
df['smartphone'] = (df['P7_3'].str.strip() == '1').astype(int)

# ── 4. Grupos de edad ────────────────────────────────────────────────────────
bins   = [5, 11, 17, 24, 34, 44, 54, 200]
labels = ['6 a 11\naños', '12 a 17\naños', '18 a 24\naños',
          '25 a 34\naños', '35 a 44\naños', '45 a 54\naños', '55 o\nmás']
df['grupo'] = pd.cut(df['EDAD'], bins=bins, labels=labels)

# ── 5. Cálculo ponderado por FAC_PER ─────────────────────────────────────────
def calcular_pct(g):
    total_fac = g['FAC_PER'].sum()
    return pd.Series({
        'pct_internet':   g['internet'].mul(g['FAC_PER']).sum()   / total_fac * 100,
        'pct_smartphone': g['smartphone'].mul(g['FAC_PER']).sum() / total_fac * 100,
    })

resultado = (
    df.groupby('grupo', observed=True)
    .apply(calcular_pct)
    .reset_index()
)

print("\nValores calculados:")
print(resultado.round(1).to_string(index=False))

grupos  = resultado['grupo'].tolist()
pct_smt = resultado['pct_smartphone'].tolist()
pct_int = resultado['pct_internet'].tolist()

# ── 6. Configuración de Gráfica UI (Estilo A.9/F.16) ──────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Colores institucionales alineados a la Paleta Teal
COLOR_SMT = '#86adae'  # Teal claro
COLOR_INT = '#335a5c'  # Teal oscuro
color_texto = '#3c3c3b'

n = len(grupos)
x = np.arange(n)
width = 0.25 
gap = 0.02

# Dibujar las barras
pos_smt = x - width/2 - gap/2
pos_int = x + width/2 + gap/2

rects_smt = ax.bar(pos_smt, pct_smt, width, label='Usuarios de Smartphone', color=COLOR_SMT, edgecolor='none', zorder=2)
rects_int = ax.bar(pos_int, pct_int, width, label='Usuarios de Internet', color=COLOR_INT, edgecolor='none', zorder=2)

# 7. Etiquetas de datos (Chips estilo F.16)
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        bar_color = rect.get_facecolor()
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                    bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

autolabel(rects_smt)
autolabel(rects_int)

# 8. Diseño limpio de Ejes
ax.set_xticks(x)
ax.set_xticklabels(grupos, fontsize=9, fontweight='normal', color=color_texto)

ax.set_ylim(0, max(max(pct_smt), max(pct_int)) * 1.25)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# 9. Títulos con cuadrado decorativo
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura D.2.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Uso de Smartphone e Internet por grupos de edad", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(95, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# 10. Leyenda
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=2, fontsize=10, frameon=False, handlelength=2.5)

# 11. Notas al pie
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = 'IFT con datos de la ENDUTIH 2023, del INEGI.'
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# 12. Guardar
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
plt.savefig(OUTPUT, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"¡Figura D.2 construida y validada con la nueva UI!")