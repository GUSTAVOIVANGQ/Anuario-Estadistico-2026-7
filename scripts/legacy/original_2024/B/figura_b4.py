import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from pathlib import Path
import sys
import os

sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()

plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

# ── 1. Cargar datos ───────────────────────────────────────────────────────────
df = pd.read_csv(
    r'C:\Users\ivan-\Documents\GitHub\anuario\datos\B.4\TD_LINEAS_HIST_TELFIJA_ITE_VA.csv',
    encoding='latin1'
)

# ── 2. Calcular: sumar líneas totales por año, solo diciembre (MES=12) ────────
df_dic = df[df['MES'] == 12].groupby('ANIO')['L_TOTAL_E'].sum().reset_index()
df_plot = df_dic[(df_dic['ANIO'] >= 2000) & (df_dic['ANIO'] <= 2023)].copy()

# ── 2. Figura ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')
line_color = '#006157'

ax.plot(df_plot['ANIO'], df_plot['L_TOTAL_E'],
        color=line_color, linewidth=1.5, marker='o', markersize=6,
        markerfacecolor=line_color, markeredgecolor='none', zorder=4,
        label='Líneas totales')
ax.fill_between(df_plot['ANIO'], df_plot['L_TOTAL_E'],
                alpha=0.15, color=line_color, zorder=2)

# ── 3. Anotaciones sin chip ───────────────────────────────────────────────────
val_2000 = df_plot.loc[df_plot['ANIO'] == 2000, 'L_TOTAL_E'].values[0]
ax.annotate(f"{int(val_2000):,}",
            xy=(2000, val_2000), xytext=(0, 28), textcoords='offset points',
            ha='center', va='bottom', fontsize=8, fontweight='bold',
            color='#3c3c3b', zorder=5)

val_2023 = df_plot.loc[df_plot['ANIO'] == 2023, 'L_TOTAL_E'].values[0]
ax.annotate(f"{int(val_2023):,}",
            xy=(2023, val_2023), xytext=(0, 12), textcoords='offset points',
            ha='center', va='bottom', fontsize=8, fontweight='bold',
            color='#3c3c3b', zorder=5)

# ── 4. Ejes ───────────────────────────────────────────────────────────────────
ax.set_xlim(1999.5, 2023.5)
ax.set_ylim(10_000_000, 32_000_000)

years = df_plot['ANIO'].tolist()
ax.set_xticks(years)
ax.set_xticklabels([])
ax.tick_params(axis='x', length=0, pad=0)

# Cuadrícula vertical (clipeada al axes automáticamente)
for year in years:
# Cuadrícula vertical (desde el punto de datos hasta la base)
    ax.vlines(x=df_plot['ANIO'], 
            ymin=10_000_000, 
            ymax=df_plot['L_TOTAL_E'], 
            color='#d1d1d1', 
            linewidth=1, 
            zorder=0)
ax.set_axisbelow(True)

# Eje Y cada 2M
ax.yaxis.set_major_locator(mticker.MultipleLocator(2_000_000))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
ax.tick_params(axis='y', labelsize=10, color='#3c3c3b')
for label in ax.get_yticklabels():
    label.set_fontweight('medium')

# ── 5. Bordes ─────────────────────────────────────────────────────────────────
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
for spine in ['bottom', 'left']:
    ax.spines[spine].set_color('#7c7c7c')
    ax.spines[spine].set_linewidth(1)

# ── 6. Título ─────────────────────────────────────────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction',
             xytext=(0, 34), textcoords='offset points',
             va='center', ha='left', fontsize=2,
             bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2',
                       facecolor='#4a7d75', edgecolor='none'))
ax.annotate("Figura B.4.", xy=(0, 1), xycoords='axes fraction',
             xytext=(15, 30), textcoords='offset points',
             fontsize=14, fontweight='bold', color='#3c3c3b', ha='left', va='center')
ax.annotate(" Líneas del Servicio Fijo de Telefonía (2000-2023)",
             xy=(0, 1), xycoords='axes fraction',
             xytext=(100, 30), textcoords='offset points',
             fontsize=14, fontweight='medium', color='#3c3c3b', ha='left', va='center')
ax.set_ylabel('Líneas totales', fontsize=11, color='#3c3c3b', labelpad=15, fontweight='medium')

# ── 7. Leyenda ────────────────────────────────────────────────────────────────
line_patch = plt.Line2D([0], [0], color=line_color, marker='o',
                        markersize=6, markerfacecolor=line_color,
                        markeredgecolor='none', linewidth=1.5, label='Líneas totales')
fig.legend(handles=[line_patch], loc='lower center',
           bbox_to_anchor=(0.5, 0.12), ncol=1, fontsize=10,
           frameon=False, handlelength=2.5,
           prop={'weight': 'bold', 'size': 10}, labelcolor='#3c3c3b')

# ── 8. Fuente — alineada al borde izquierdo del axes ─────────────────────────
ax.annotate("Fuente: ", xy=(0, 0), xycoords='axes fraction',
             xytext=(0, -62), textcoords='offset points',
             fontsize=8, fontweight='bold', color='#3c3c3b', ha='left', va='top',
             annotation_clip=False)
ax.annotate('IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de cada año.',
             xy=(0, 0), xycoords='axes fraction',
             xytext=(35, -62), textcoords='offset points',
             fontsize=8, fontweight='normal', color='#3c3c3b', ha='left', va='top',
             annotation_clip=False)

# ── 9. Layout ─────────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# ── 10. Rectángulo redondeado de años — dibujado DESPUÉS del layout ───────────
# Forzar el render para que las transformaciones estén actualizadas
fig.canvas.draw()

# Coordenadas en display (pixels) del área del axes
ax_bbox = ax.get_window_extent()   # en pixels
fig_bbox = fig.get_window_extent()  # en pixels

# Altura del rectángulo en pixels y posición Y (debajo del spine)
gap_px   = 0    # sin espacio — pegado al spine
rect_h_px = 28  # altura suficiente para el texto
rect_y_px = ax_bbox.y0 - gap_px - rect_h_px

# Convertir a coordenadas de figura (fracción 0-1)
def px_to_fig(x_px, y_px):
    return (x_px / fig_bbox.width, y_px / fig_bbox.height)

rx0, ry0 = px_to_fig(ax_bbox.x0, rect_y_px)
rw  = (ax_bbox.x1 - ax_bbox.x0) / fig_bbox.width
rh  = rect_h_px / fig_bbox.height

# Radio de redondeo en fracción de figura (pequeño para que se vea sutil)
radius = 0.008

rect_patch = FancyBboxPatch(
    (rx0, ry0), rw, rh,
    boxstyle=f'round,pad=0,rounding_size={radius}',
    facecolor='#F8F8FA', edgecolor='#7c7c7c', linewidth=0.9,
    transform=fig.transFigure, clip_on=False, zorder=10
)
fig.add_artist(rect_patch)

# Texto de cada año centrado dentro del rectángulo
y_text_fig = ry0 + rh / 2  # centro vertical del rectángulo en fracción figura

for year in years:
    # X del año en pixels (coordenada de datos → display)
    x_px, _ = ax.transData.transform((year, 0))
    x_fig = x_px / fig_bbox.width
    fig.text(x_fig, y_text_fig, str(year),
             ha='center', va='center',
             fontsize=7.5, fontweight='bold', color='#3c3c3b',
             clip_on=False, zorder=11)

# ── 11. Guardar ───────────────────────────────────────────────────────────────
output_path = r'C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_B4.png'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
fig.savefig(output_path, dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"Figura guardada en: {output_path}")

# ── 12. Imprimir valores calculados ───────────────────────────────────────────
print("\nValores calculados (diciembre de cada año):")
print(df_plot.to_string(index=False))