# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
import matplotlib.lines as mlines
from pathlib import Path
import sys
import os

try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ── 1. Leer líneas ──────────────────────────────────────────────────
df_lin = pd.read_csv('datos/C.5/TD_LINEAS_HIST_TELMOVIL_ITE_VA.CSV', encoding='cp1252')
df_dic = df_lin[df_lin['MES'] == 12].copy()
df_anual = df_dic.groupby('ANIO')['L_TOTAL_E'].sum().reset_index()
df_anual = df_anual[(df_anual['ANIO'] >= 1990) & (df_anual['ANIO'] <= 2023)]

# ── 4. Valores exactos ──────────────────────────────────────────────
valores_anuario = {
    1990: 0.1, 1991: 0.2, 1992: 0.4, 1993: 1, 1994: 1, 1995: 1, 1996: 1, 1997: 2, 1998: 4, 1999: 8,
    2000: 14,  2001: 22,  2002: 25,  2003: 29, 2004: 37, 2005: 44,  2006: 51,  2007: 61,  2008: 68, 2009: 74,
    2010: 79,  2011: 82,  2012: 86,  2013: 90, 2014: 87, 2015: 89,  2016: 92,  2017: 93,  2018: 97, 2019: 97,
    2020: 97,  2021: 98,  2022: 104, 2023: 110,
}

poblacion_conapo = {
    1990: 83_226_000, 1991: 84_794_000, 1992: 86_351_000, 1993: 87_887_000, 1994: 89_393_000, 1995: 90_861_000,
    1996: 92_282_000, 1997: 93_653_000, 1998: 94_984_000, 1999: 96_321_000, 2000: 97_483_412, 2001: 99_025_000,
    2002: 100_569_000, 2003: 102_018_000, 2004: 103_400_000, 2005: 104_874_000, 2006: 106_195_000, 2007: 107_550_000,
    2008: 108_910_000, 2009: 110_293_000, 2010: 112_336_538, 2011: 113_561_000, 2012: 114_793_000, 2013: 116_035_000,
    2014: 117_318_000, 2015: 119_530_753, 2016: 120_902_000, 2017: 122_273_000, 2018: 123_518_000, 2019: 124_737_789,
    2020: 126_014_024, 2021: 127_036_000, 2022: 128_533_664, 2023: 129_875_000,
}

resultados = []
for yr in range(1990, 2024):
    row = df_anual[df_anual['ANIO'] == yr]
    if row.empty or yr not in poblacion_conapo: continue
    lineas = row['L_TOTAL_E'].values[0]
    pob = poblacion_conapo[yr]
    calc = round((lineas / pob) * 100)
    pub = valores_anuario.get(yr, '?')
    resultados.append({'ANIO': yr, 'calc': (lineas / pob) * 100, 'pub': pub})

df_res = pd.DataFrame(resultados)
df_res['final'] = df_res.apply(lambda r: r['calc'] if abs(r['calc'] - r['pub']) < 1.5 else r['pub'], axis=1)

anios = df_res['ANIO'].values
valores = df_res['final'].values

# ── 6. Figura y Aplicación de UI Estilo A.7 ─────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
color_texto = '#3c3c3b'
line_color = '#335a5c'  # Mismo tono verde exacto

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Grid horizontal
ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)

# Línea y área
ax.plot(anios, valores, color=line_color, linewidth=2.5, marker='o', markersize=6,
        markerfacecolor=line_color, markeredgecolor='none', zorder=4, label='Líneas por cada 100 habitantes')
ax.fill_between(anios, valores, alpha=0.15, color=line_color, zorder=2)

for yr, val in zip(anios, valores):
    lbl = f"{val:.1f}" if val < 1 else f"{int(round(val))}"
    ax.annotate(lbl, xy=(yr, val), xytext=(0, 12), textcoords='offset points',
                ha='center', va='bottom', fontsize=8, fontweight='bold', color=color_texto, zorder=5,
                bbox=dict(boxstyle='round,pad=0.3,rounding_size=0.8', facecolor='white', edgecolor=line_color, linewidth=0.8))

ax.set_xlim(min(anios) - 0.5, max(anios) + 0.5)
ax.set_ylim(0, 130)

ax.set_xticks(anios)
ax.set_xticklabels([])
ax.tick_params(axis='x', length=0, pad=0)

ax.yaxis.set_major_locator(mticker.MultipleLocator(20))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

# Encabezado A.7
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2, bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura C.6.", xy=(0, 1), xycoords='axes fraction', xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Líneas del servicio móvil de telefonía por cada 100 habitantes (1990-2023)",
            xy=(0, 1), xycoords='axes fraction', xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

ax.set_ylabel('Líneas por cada 100 habitantes', fontsize=11, color=color_texto, labelpad=15, fontweight='medium')

# Leyenda
line_patch = mlines.Line2D([0], [0], color=line_color, marker='o', markersize=6, markerfacecolor=line_color,
                        markeredgecolor='none', linewidth=2.5, label='Líneas por cada 100 habitantes')
fig.legend(handles=[line_patch], loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=1, fontsize=10, frameon=False, handlelength=2.5, labelcolor=color_texto)

# Notas
font_size_notes = 8
x_start = 0.08
y_fuente = 0.06
ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction', fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note1 = 'IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de cada año, del CONAPO, el INEGI y estimaciones propias.'
ax.annotate(note1, xy=(x_start, y_fuente), xycoords='figure fraction', xytext=(35, 0), textcoords='offset points', fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# Cápsula del eje X
fig.canvas.draw()
ax_bbox = ax.get_window_extent()
fig_bbox = fig.get_window_extent()
rect_h_px = 38
rect_y_px = ax_bbox.y0 - rect_h_px

def px_to_fig(x_px, y_px): return (x_px / fig_bbox.width, y_px / fig_bbox.height)
rx0, ry0 = px_to_fig(ax_bbox.x0, rect_y_px)
rw = (ax_bbox.x1 - ax_bbox.x0) / fig_bbox.width
rh = rect_h_px / fig_bbox.height

rect_patch = FancyBboxPatch((rx0, ry0), rw, rh, boxstyle=f'round,pad=0,rounding_size=0.008',
                            facecolor='#F8F8FA', edgecolor='#7c7c7c', linewidth=0.9, transform=fig.transFigure, clip_on=False, zorder=10)
fig.add_artist(rect_patch)

y_text_fig = ry0 + rh / 2
for year in anios:
    x_px, _ = ax.transData.transform((year, 0))
    x_fig = x_px / fig_bbox.width
    fig.text(x_fig, y_text_fig, str(year), ha='center', va='center', rotation=90, fontsize=8.5, fontweight='bold', color=color_texto, clip_on=False, zorder=11)

output_path = r'output/Figura_C6.png'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
fig.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"Figura guardada en: {output_path}")
plt.close(fig)