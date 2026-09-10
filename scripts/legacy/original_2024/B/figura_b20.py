import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import matplotlib.ticker as mticker

# ── 1. Leer datos ─────────────────────────────────────────────────────────────
df = pd.read_csv(r"C:\Users\ivan-\Documents\GitHub\anuario\datos\b.20\TD_PENETRACION_H_TVRES_ITE_VA.csv")

# ── 2. Filtrar diciembre, rango 1998-2023 ─────────────────────────────────────
df_plot = (df[(df['MES'] == 12) &
              (df['ANIO'] >= 1998) &
              (df['ANIO'] <= 2023)]
           .sort_values('ANIO')
           .reset_index(drop=True))

anios  = df_plot['ANIO'].tolist()
valores = df_plot['P_H_TVRES_E'].tolist()

# ── 3. Configuración de Gráfica (Estilo F.16) ─────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Colores institucionales alineados a la Paleta Teal (mismo verde de F.16)
COLOR_BARRA = '#86adae'  # Teal claro de F.16
color_texto = '#3c3c3b'

# Dibujar las barras
bars = ax.bar(anios, valores, color=COLOR_BARRA, edgecolor='none', width=0.7, zorder=2)

# ── 4. Etiquetas de datos (Chips estilo F.16 rotados a 90°) ───────────────────
for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 6),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=COLOR_BARRA, linewidth=0.8))

# ── 5. Diseño limpio de Ejes ──────────────────────────────────────────────────
ax.set_xticks(anios)
ax.set_xticklabels([str(a) for a in anios], rotation=90, fontsize=9, fontweight='normal', color=color_texto)

ax.set_ylim(0, max(valores) * 1.35)
ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:,.0f}'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# ── 6. Títulos ────────────────────────────────────────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura B.20.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Accesos del Servicio de Televisión Restringida por cada 100 hogares (1998-2023)", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(115, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# ── 7. Notas al pie ───────────────────────────────────────────────────────────
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = ('IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de cada año, del CONAPO y el INEGI.')
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# ── 8. Guardar ────────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
plt.savefig(r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_B20.png", dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.show()
print("Guardado en output/Figura_B20.png")