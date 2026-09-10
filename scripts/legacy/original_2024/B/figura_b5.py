import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import numpy as np

# ── 1. Cargar datos ────────────────────────────────────────────────────────
df = pd.read_csv(r'C:\Users\ivan-\Documents\GitHub\anuario\datos\B.5\TD_PENETRACION_H_TELFIJA_ITE_VA.csv', encoding='latin1')

# ── 2. Filtrar: solo diciembre (MES=12), rango 1971-2023 ───────────────────
# La columna P_H_TELFIJA_E ya contiene el cálculo: líneas / 100 hogares
df_plot = df[(df['MES'] == 12) & (df['ANIO'] >= 1971) & (df['ANIO'] <= 2023)].copy()

anios = df_plot['ANIO'].values
valores = df_plot['P_H_TELFIJA_E'].values

# ── 3. Configuración de Gráfica (Estilo F.16) ───────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(18, 7.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Colores institucionales alineados a la Paleta Teal
COLOR_BARRA = '#335a5c'  # Teal oscuro (mismo tono base utilizado en F.16)
color_texto = '#3c3c3b'

# Dibujar las barras
rects = ax.bar(anios, valores, width=0.7, color=COLOR_BARRA, edgecolor='none', zorder=2)

# ── 4. Etiquetas de datos (Chips estilo F.16) ──────────────────────────────
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        bar_color = rect.get_facecolor()
        # Se formatea a entero tal como en el script original
        ax.annotate(f'{int(height)}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3, rotation=0,
                    bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

autolabel(rects)

# ── 5. Diseño limpio de Ejes ───────────────────────────────────────────────
ax.set_xlim(1970, 2024)
# Margen extra arriba
ax.set_ylim(0, max(valores) * 1.15)

ax.set_xticks(anios)
ax.set_xticklabels(anios, rotation=90, fontsize=9, fontweight='normal', color=color_texto)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.set_ylabel('Líneas por cada 100 hogares', fontsize=10, color=color_texto, labelpad=10)

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# ── 6. Títulos (Estilo Institucional F.16) ──────────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura B.5.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Líneas del Servicio Fijo de Telefonía por cada 100 hogares (1971-2023)", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# ── 7. Notas al pie ─────────────────────────────────────────────────────────
font_size_notes = 8
x_start = 0.04
y_fuente = 0.04

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = ('IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de cada año, del CONAPO y el INEGI.')
fig.text(x_start + 0.035, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# ── 8. Guardar ──────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.04, right=0.98, top=0.85, bottom=0.20)
plt.savefig(r'C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_B5.png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("¡Figura B.5 construida y validada con estilo institucional F.16!")

# ── 9. Imprimir valores calculados ──────────────────────────────────────────
print("\nValores calculados (líneas por cada 100 hogares, diciembre):")
print(df_plot[['ANIO', 'P_H_TELFIJA_E']].to_string(index=False))