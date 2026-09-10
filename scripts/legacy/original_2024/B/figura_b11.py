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
    r"C:\Users\ivan-\Documents\GitHub\anuario\datos\b.11\TD_ACC_INTER_HIS_ITE_VA.csv",
    encoding="latin1"
)
df["MES"] = pd.to_numeric(df["MES"], errors="coerce")
df["ANIO"] = pd.to_numeric(df["ANIO"], errors="coerce")
df["A_TOTAL_E"] = pd.to_numeric(df["A_TOTAL_E"], errors="coerce")

df_dic = df[df["MES"] == 12].groupby("ANIO")["A_TOTAL_E"].sum().reset_index()
df_plot = df_dic[(df_dic["ANIO"] >= 2000) & (df_dic["ANIO"] <= 2023)].reset_index(drop=True)

# ── 2. Figura ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')
line_color = '#006157'  # Tono verde exacto de B.4

ax.plot(df_plot['ANIO'], df_plot['A_TOTAL_E'],
        color=line_color, linewidth=1.5, marker='o', markersize=6,
        markerfacecolor=line_color, markeredgecolor='none', zorder=4,
        label='Accesos totales')
ax.fill_between(df_plot['ANIO'], df_plot['A_TOTAL_E'],
                alpha=0.15, color=line_color, zorder=2)

# ── 3. Anotaciones sin chip ───────────────────────────────────────────────────
year_ini = df_plot['ANIO'].min()
val_ini = df_plot.loc[df_plot['ANIO'] == year_ini, 'A_TOTAL_E'].values[0]
ax.annotate(f"{int(val_ini):,}",
            xy=(year_ini, val_ini), xytext=(0, 12), textcoords='offset points',
            ha='center', va='bottom', fontsize=8, fontweight='bold',
            color='#3c3c3b', zorder=5)

year_fin = df_plot['ANIO'].max()
val_fin = df_plot.loc[df_plot['ANIO'] == year_fin, 'A_TOTAL_E'].values[0]
ax.annotate(f"{int(val_fin):,}",
            xy=(year_fin, val_fin), xytext=(0, 12), textcoords='offset points',
            ha='center', va='bottom', fontsize=8, fontweight='bold',
            color='#3c3c3b', zorder=5)

# ── 4. Ejes ───────────────────────────────────────────────────────────────────
ax.set_xlim(year_ini - 0.5, year_fin + 0.5)
ax.set_ylim(0, 32_000_000)

years = df_plot['ANIO'].tolist()
ax.set_xticks(years)
ax.set_xticklabels([])
ax.tick_params(axis='x', length=0, pad=0)

# Cuadrícula vertical (desde el punto de datos hasta la base)
ax.vlines(x=df_plot['ANIO'], 
          ymin=0, 
          ymax=df_plot['A_TOTAL_E'], 
          color='#d1d1d1', 
          linewidth=1, 
          zorder=0)
ax.set_axisbelow(True)

ax.yaxis.set_major_locator(mticker.MultipleLocator(5_000_000))
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
ax.annotate("Figura B.11.", xy=(0, 1), xycoords='axes fraction',
             xytext=(15, 30), textcoords='offset points',
             fontsize=14, fontweight='bold', color='#3c3c3b', ha='left', va='center')
ax.annotate(" Accesos del Servicio Fijo de Internet (2000-2023)",
             xy=(0, 1), xycoords='axes fraction',
             xytext=(115, 30), textcoords='offset points',
             fontsize=14, fontweight='medium', color='#3c3c3b', ha='left', va='center')
ax.set_ylabel('Accesos totales', fontsize=11, color='#3c3c3b', labelpad=15, fontweight='medium')

# ── 7. Leyenda ────────────────────────────────────────────────────────────────
line_patch = plt.Line2D([0], [0], color=line_color, marker='o',
                        markersize=6, markerfacecolor=line_color,
                        markeredgecolor='none', linewidth=1.5, label='Accesos totales')
fig.legend(handles=[line_patch], loc='lower center',
           bbox_to_anchor=(0.5, 0.12), ncol=1, fontsize=10,
           frameon=False, handlelength=2.5,
           prop={'weight': 'bold', 'size': 10}, labelcolor='#3c3c3b')

# ── 8. Fuente ─────────────────────────────────────────────────────────────────
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

# ── 10. Rectángulo redondeado de años ─────────────────────────────────────────
fig.canvas.draw()
ax_bbox = ax.get_window_extent()
fig_bbox = fig.get_window_extent()

gap_px   = 0
rect_h_px = 28
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
             ha='center', va='center',
             fontsize=7.5, fontweight='bold', color='#3c3c3b',
             clip_on=False, zorder=11)

# ── 11. Guardar ───────────────────────────────────────────────────────────────
output_path = r'C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_B11.png'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
fig.savefig(output_path, dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"Figura guardada en: {output_path}")