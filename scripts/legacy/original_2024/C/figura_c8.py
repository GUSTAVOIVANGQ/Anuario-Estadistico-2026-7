import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
import matplotlib.lines as mlines
from pathlib import Path
import sys
import os

sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()

# ── 1. Leer y limpiar ─────────────────────────────────────────────────────────
df = pd.read_csv(r'datos/C.8/TD_TRAF_HIST_TELMOVIL_ITE_VA.csv', encoding='latin1')

df['TRAF_SALIDA'] = (df['TRAF_SALIDA']
                     .astype(str)
                     .str.replace(',', '')
                     .str.strip())
df['TRAF_SALIDA'] = pd.to_numeric(df['TRAF_SALIDA'], errors='coerce')

# ── 2. Agregar por año y convertir a millones de minutos ──────────────────────
trafico = df.groupby('ANIO')['TRAF_SALIDA'].sum() / 1_000_000
trafico = trafico.loc[1997:2023]

years  = trafico.index.astype(int).tolist()
values = trafico.values.tolist()

# ── 3. Figura y Aplicación de UI (Estilo C.6) ─────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')
line_color = '#006157'  # Verde institucional exacto

# GRID: Solo líneas horizontales
ax.grid(axis='y', color='#d1d1d1', linewidth=1, linestyle='-', zorder=0)

# Línea y área
ax.plot(years, values, color=line_color, linewidth=2.5, marker='o', markersize=6,
        markerfacecolor=line_color, markeredgecolor='none', zorder=4,
        label='Tráfico de salida')
ax.fill_between(years, values, alpha=0.15, color=line_color, zorder=2)

# Anotaciones con chip en todos los puntos
for yr, val in zip(years, values):
    lbl = f"{int(round(val)):,}"
    ax.annotate(lbl,
                xy=(yr, val), xytext=(0, 12), textcoords='offset points',
                ha='center', va='bottom', fontsize=8, fontweight='bold',
                color='#3c3c3b', zorder=5,
                bbox=dict(boxstyle='round,pad=0.3,rounding_size=0.8',
                          facecolor='white', edgecolor=line_color, linewidth=0.8))

# Ejes
ax.set_xlim(min(years) - 0.5, max(years) + 0.5)
ax.set_ylim(0, max(values) * 1.2)

ax.set_xticks(years)
ax.set_xticklabels([])  # Ocultamos etiquetas originales para usar la cápsula
ax.tick_params(axis='x', length=0, pad=0)

ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True, prune='lower', nbins=6))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
ax.tick_params(axis='y', labelsize=10, color='#3c3c3b')
for label in ax.get_yticklabels():
    label.set_fontweight('medium')

# Bordes
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
for spine in ['bottom', 'left']:
    ax.spines[spine].set_color('#7c7c7c')
    ax.spines[spine].set_linewidth(1)

# Título
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction',
             xytext=(0, 34), textcoords='offset points',
             va='center', ha='left', fontsize=2,
             bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2',
                       facecolor='#4a7d75', edgecolor='none'))
ax.annotate("Figura C.8.", xy=(0, 1), xycoords='axes fraction',
             xytext=(15, 30), textcoords='offset points',
             fontsize=14, fontweight='bold', color='#3c3c3b', ha='left', va='center')
ax.annotate(" Tráfico de salida del servicio móvil de telefonía (1997-2023)",
             xy=(0, 1), xycoords='axes fraction',
             xytext=(115, 30), textcoords='offset points',
             fontsize=14, fontweight='medium', color='#3c3c3b', ha='left', va='center')
ax.set_ylabel('Millones de minutos', fontsize=11, color='#3c3c3b', labelpad=15, fontweight='medium')

# Leyenda
line_patch = mlines.Line2D([0], [0], color=line_color, marker='o',
                        markersize=6, markerfacecolor=line_color,
                        markeredgecolor='none', linewidth=2.5, label='Millones de minutos')
fig.legend(handles=[line_patch], loc='lower center',
           bbox_to_anchor=(0.5, 0.12), ncol=1, fontsize=10,
           frameon=False, handlelength=2.5,
           prop={'weight': 'bold', 'size': 10}, labelcolor='#3c3c3b')

# Fuente
ax.annotate("Fuente: ", xy=(0, 0), xycoords='axes fraction',
             xytext=(0, -78), textcoords='offset points',
             fontsize=8, fontweight='bold', color='#3c3c3b', ha='left', va='top',
             annotation_clip=False)
ax.annotate('IFT con datos de los operadores de telecomunicaciones. Para cada año los datos se presentan acumulados al mes de diciembre.',
             xy=(0, 0), xycoords='axes fraction',
             xytext=(35, -78), textcoords='offset points',
             fontsize=8, fontweight='normal', color='#3c3c3b', ha='left', va='top',
             annotation_clip=False)

# Layout
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# ── 4. Rectángulo redondeado de años (Cápsula) ────────────────────────────────
fig.canvas.draw()
ax_bbox = ax.get_window_extent()
fig_bbox = fig.get_window_extent()

gap_px   = 0
rect_h_px = 38
rect_y_px = ax_bbox.y0 - gap_px - rect_h_px

def px_to_fig(x_px, y_px):
    return (x_px / fig_bbox.width, y_px / fig_bbox.height)

rx0, ry0 = px_to_fig(ax_bbox.x0, rect_y_px)
rw  = (ax_bbox.x1 - ax_bbox.x0) / fig_bbox.width
rh  = rect_h_px / fig_bbox.height

rect_patch = FancyBboxPatch(
    (rx0, ry0), rw, rh,
    boxstyle=f'round,pad=0,rounding_size=0.008',
    facecolor='#F8F8FA', edgecolor='#7c7c7c', linewidth=0.9,
    transform=fig.transFigure, clip_on=False, zorder=10
)
fig.add_artist(rect_patch)

y_text_fig = ry0 + rh / 2
for year in years:
    x_px, _ = ax.transData.transform((year, 0))
    x_fig = x_px / fig_bbox.width
    fig.text(x_fig, y_text_fig, str(year),
             ha='center', va='center', rotation=90,
             fontsize=8.5, fontweight='bold', color='#3c3c3b',
             clip_on=False, zorder=11)

# Guardar
output_path = r'output/Figura_C8.png'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
fig.savefig(output_path, dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"Figura guardada en: {output_path}")