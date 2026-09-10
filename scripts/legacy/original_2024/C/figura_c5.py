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

# ── 1. Lectura ────────────────────────────────────────────────────────────────
df = pd.read_csv('datos/C.5/TD_LINEAS_HIST_TELMOVIL_ITE_VA.csv', encoding='cp1252')
df_dic = df[df['MES'] == 12].copy()

cols = ['L_PREPAGO_E', 'L_POSPAGO_E', 'L_POSPAGOC_E', 'L_POSPAGOL_E', 'L_NO_ESPECIFICADO_E', 'L_TOTAL_E']
df_anual = df_dic.groupby('ANIO')[cols].sum().reset_index()
df_anual = df_anual[(df_anual['ANIO'] >= 1990) & (df_anual['ANIO'] <= 2023)].copy()

for c in cols:
    df_anual[c] = df_anual[c] / 1_000_000

# ── 2. Paleta Monocromática Teal (Mismos verdes estilo F.16) ──────────────────
COLOR_PREPAGO   = '#86adae'
COLOR_POSPAGO   = '#64a0a1'
COLOR_POSPC     = '#5c9596'
COLOR_POSPL     = '#4c7d7e'
COLOR_NOESP     = '#3b6667'
COLOR_TOTAL     = '#132b2d'  # Verde oscuro casi negro para la línea
color_texto     = '#3c3c3b'

anios  = df_anual['ANIO'].values
prepago = df_anual['L_PREPAGO_E'].values
pospc   = df_anual['L_POSPAGOC_E'].values
pospl   = df_anual['L_POSPAGOL_E'].values
pospago = df_anual['L_POSPAGO_E'].values   
noesp   = df_anual['L_NO_ESPECIFICADO_E'].values
total   = df_anual['L_TOTAL_E'].values

# ── 3. Configuración de Gráfica (Estilo F.16) ─────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Área rellena apilada
ax.stackplot(
    anios, prepago, pospago, pospc, pospl, noesp,
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

# ── 4. Etiquetas de datos (Chips estilo F.16 horizontales para todos los puntos) ───
for yr in anios:
    row = df_anual[df_anual['ANIO'] == yr]
    if not row.empty:
        v = row['L_TOTAL_E'].values[0]
        ax.annotate(f"{v:.1f}",
                    xy=(yr, v), xytext=(0, 6), textcoords='offset points',
                    fontsize=8, fontweight='bold', color=color_texto,
                    ha='center', va='bottom', zorder=5,
                    bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=COLOR_TOTAL, linewidth=0.8))

# ── 5. Diseño limpio de Ejes ──────────────────────────────────────────────────
ax.set_ylim(0, 180)
ax.yaxis.set_major_locator(mticker.MultipleLocator(20))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.set_xlim(1989.5, 2023.5)
ax.set_xticks(anios)
ax.set_xticklabels([])
ax.tick_params(axis='x', length=0, pad=0)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# ── 6. Títulos ────────────────────────────────────────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura C.5.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Líneas del servicio móvil de telefonía (1990-2023) [Millones]", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(105, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# ── 7. Leyenda ────────────────────────────────────────────────────────────────
handles, labels_leg = ax.get_legend_handles_labels()
fig.legend(handles, labels_leg, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=6, fontsize=10, frameon=False, handlelength=2.5)

# ── 8. Notas al pie ───────────────────────────────────────────────────────────
font_size_notes = 8
x_start = 0.08
y_fuente = 0.07

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fig.text(x_start + 0.032, y_fuente, 'IFT con datos de los operadores de telecomunicaciones a diciembre de cada año.', fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.045
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fig.text(x_start + 0.025, y_nota, 'A partir del tercer trimestre de 2017, se agregó la desagregación por pospago libre y pospago controlado.', fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

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

for year in anios:
    # X del año en pixels (coordenada de datos → display)
    x_px, _ = ax.transData.transform((year, 0))
    x_fig = x_px / fig_bbox.width
    fig.text(x_fig, y_text_fig, str(year),
             ha='center', va='center',
             fontsize=7.5, fontweight='bold', color='#3c3c3b',
             clip_on=False, zorder=11)

# ── 11. Guardar ───────────────────────────────────────────────────────────────
plt.savefig('output/Figura_C5.png', dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.savefig('output/Figura_C5.pdf', bbox_inches='tight', facecolor='white', edgecolor='none')
print("\nGuardado: output/Figura_C5.png y output/Figura_C5.pdf")
plt.show()