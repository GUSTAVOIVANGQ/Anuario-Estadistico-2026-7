"""
Figura C.11 — Líneas del servicio móvil de acceso a Internet (2010-2023)
Refactorizado para coincidir con la UI y paleta de colores de Figura C.5.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.patches import FancyBboxPatch

# ── 1. Lectura y limpieza ─────────────────────────────────────────────────────
CSV_PATH = 'datos/C.11/TD_LINEAS_HIST_INTMOVIL_ITE_VA.csv'
df = pd.read_csv(CSV_PATH, encoding="latin1")

cols_num = ["L_PREPAGO_E", "L_POSPAGO_E", "L_POSPAGOC_E",
            "L_POSPAGOL_E", "L_NO_ESPECIFICADO_E", "L_TOTAL_E"]
for col in cols_num:
    df[col] = (pd.to_numeric(df[col].astype(str)
               .str.replace(",", "").str.strip(), errors="coerce")
               .fillna(0))

# ── 2. Filtrar diciembre 2010-2023 y agregar por año ──────────────────────────
dic = df[(df["MES"] == 12) & (df["ANIO"] >= 2010) & (df["ANIO"] <= 2023)]
g   = dic.groupby("ANIO")[cols_num].sum() / 1_000_000   # millones de líneas

anios    = g.index.values
prepago  = g["L_PREPAGO_E"].values
pospago  = g["L_POSPAGO_E"].values        
pospagoc = g["L_POSPAGOC_E"].values       
pospagol = g["L_POSPAGOL_E"].values       
sin_seg  = g["L_NO_ESPECIFICADO_E"].values
total    = g["L_TOTAL_E"].values

# ── 3. Paleta Monocromática Teal (Mismos verdes estilo C.5) ───────────────────
COLOR_PREPAGO   = '#86adae'
COLOR_POSPAGO   = '#64a0a1'
COLOR_POSPC     = '#5c9596'
COLOR_POSPL     = '#4c7d7e'
COLOR_NOESP     = '#3b6667'
COLOR_TOTAL     = '#132b2d'  # Verde oscuro casi negro para la línea
color_texto     = '#3c3c3b'

# ── 4. Configuración de Gráfica ───────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Área rellena apilada (Mismo orden y opacidad que C.5)
ax.stackplot(
    anios, prepago, pospago, pospagoc, pospagol, sin_seg,
    labels=[
        'Líneas Prepago', 'Líneas Pospago', 'Líneas Pospago controlado',
        'Líneas Pospago libre', 'Líneas sin segmento especificado'
    ],
    colors=[COLOR_PREPAGO, COLOR_POSPAGO, COLOR_POSPC, COLOR_POSPL, COLOR_NOESP],
    alpha=0.85, zorder=2
)

# Línea de totales encima
ax.plot(anios, total, color=COLOR_TOTAL, linewidth=2.5, marker='o', markersize=6, 
        markeredgewidth=0, label='Líneas totales', zorder=4)

# ── 5. Etiquetas de datos (Chips estilo C.5 horizontales) ─────────────────────
for yr, t in zip(anios, total):
    ax.annotate(f"{t:.1f}",
                xy=(yr, t), xytext=(0, 6), textcoords='offset points',
                fontsize=8, fontweight='bold', color=color_texto,
                ha='center', va='bottom', zorder=5,
                bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=COLOR_TOTAL, linewidth=0.8))

# ── 6. Diseño limpio de Ejes ──────────────────────────────────────────────────
ax.set_ylim(0, 140)
ax.yaxis.set_major_locator(mticker.MultipleLocator(20))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.set_xlim(2009.5, 2023.5)
ax.set_xticks(anios)
ax.set_xticklabels([])
ax.tick_params(axis='x', length=0, pad=0)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# ── 7. Títulos ────────────────────────────────────────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura C.11.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Líneas del servicio móvil de acceso a Internet (2010-2023) [Millones]", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(115, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# ── 8. Leyenda ────────────────────────────────────────────────────────────────
handles, labels_leg = ax.get_legend_handles_labels()
fig.legend(handles, labels_leg, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=6, fontsize=10, frameon=False, handlelength=2.5)

# ── 9. Notas al pie ───────────────────────────────────────────────────────────
font_size_notes = 8
x_start = 0.08
y_fuente = 0.07

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fig.text(x_start + 0.032, y_fuente, 'IFT con datos de los operadores de telecomunicaciones a diciembre de cada año.', fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.045
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fig.text(x_start + 0.025, y_nota, 'A partir de 2017, se comenzó a solicitar la desagregación por pospago libre y pospago controlado.', fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# ── 10. Layout ────────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# ── 11. Rectángulo redondeado de años — dibujado DESPUÉS del layout ───────────
# Forzar el render para que las transformaciones estén actualizadas
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

radius = 0.008

rect_patch = FancyBboxPatch(
    (rx0, ry0), rw, rh,
    boxstyle=f'round,pad=0,rounding_size={radius}',
    facecolor='#F8F8FA', edgecolor='#7c7c7c', linewidth=0.9,
    transform=fig.transFigure, clip_on=False, zorder=10
)
fig.add_artist(rect_patch)

y_text_fig = ry0 + rh / 2  

for year in anios:
    x_px, _ = ax.transData.transform((year, 0))
    x_fig = x_px / fig_bbox.width
    fig.text(x_fig, y_text_fig, str(year),
             ha='center', va='center',
             fontsize=7.5, fontweight='bold', color='#3c3c3b',
             clip_on=False, zorder=11)

# ── 12. Guardar ───────────────────────────────────────────────────────────────
plt.savefig('output/Figura_C11.png', dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.savefig('output/Figura_C11.pdf', bbox_inches='tight', facecolor='white', edgecolor='none')
print("\nGuardado: output/Figura_C11.png y output/Figura_C11.pdf")
plt.show()