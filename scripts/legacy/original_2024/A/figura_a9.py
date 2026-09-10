import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

import matplotlib.ticker as mticker

# ── 1. Carga de microdatos ENIGH 2022 ─────────────────────────────────────────
BASE = os.path.join(os.path.dirname(__file__), "..", "..", 'datos', 'A.7', 'microdatos')

concentrado = pd.read_csv(
    os.path.join(BASE, 'concentradohogar.csv'), low_memory=False,
    usecols=['folioviv', 'foliohog', 'ing_cor', 'factor', 'comunica'])
concentrado['ing_cor'] = pd.to_numeric(concentrado['ing_cor'], errors='coerce').fillna(0)
concentrado['comunica'] = pd.to_numeric(concentrado['comunica'], errors='coerce').fillna(0)

hogares = pd.read_csv(
    os.path.join(BASE, 'hogares.csv'), low_memory=False,
    usecols=['folioviv', 'foliohog', 'telefono', 'celular', 'tv_paga', 'conex_inte'])

df = concentrado.merge(hogares, on=['folioviv', 'foliohog'], how='left')

# ── 1b. Deciles de ingreso corriente ──────────────────────────────────────────
df = df.sort_values('ing_cor').reset_index(drop=True)
df['cum_factor'] = df['factor'].cumsum()
total_factor = df['factor'].sum()
df['pct_cum'] = df['cum_factor'] / total_factor
df['decil'] = pd.cut(
    df['pct_cum'], bins=np.linspace(0, 1, 11),
    labels=range(1, 11), include_lowest=True
).astype(int)

# ── 1c. Indicadores ───────────────────────────────────────────────────────────
df['tiene_moviles'] = (df['celular'] == 1).astype(int)
df['dg_moviles'] = ((df['tiene_moviles'] == 1) & (df['comunica'] > 0)).astype(int)

# ── 1d. Cálculo por decil ─────────────────────────────────────────────────────
deciles = list(range(1, 11))
pct_con_telecom = []
pct_disponen_gastan = []

for d in deciles:
    sub = df[df['decil'] == d]
    w = sub['factor']
    pct_con_telecom.append(round((sub['tiene_moviles'] * w).sum() / w.sum() * 100, 1))
    pct_disponen_gastan.append(round((sub['dg_moviles'] * w).sum() / w.sum() * 100, 1))

# ── 2. Gráfica estilo A.6 ─────────────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

y_pos = np.arange(len(deciles))
bar_height = 0.38

# Colores extraídos de figura_a6.py
COLOR_CON_TELECOM = '#335a5c'  # Teal oscuro 
COLOR_DISPONEN = '#86adae'     # Teal claro
color_texto = '#3c3c3b'

# Barras horizontales
bars_con = ax.barh(y_pos - bar_height / 2, pct_con_telecom, height=bar_height,
                   color=COLOR_CON_TELECOM, edgecolor='none', zorder=2,
                   label='% Hogares con telecomunicaciones móviles')

bars_dg = ax.barh(y_pos + bar_height / 2, pct_disponen_gastan, height=bar_height,
                  color=COLOR_DISPONEN, edgecolor='none', zorder=2,
                  label='% Hogares que disponen y gastan en telecomunicaciones móviles')

# ── 3. Anotaciones de valor (Números normales sin chip) ───────────────────────
for i in range(len(deciles)):
    # Disponen y gastan (superior)
    ax.text(pct_disponen_gastan[i] + 1.5, y_pos[i] + bar_height / 2, f'{pct_disponen_gastan[i]:.1f}%',
            va='center', ha='left', fontsize=9, color=color_texto, fontweight='normal',
            zorder=3)
            
    # Con telecomunicaciones (inferior)
    ax.text(pct_con_telecom[i] + 1.5, y_pos[i] - bar_height / 2, f'{pct_con_telecom[i]:.1f}%',
            va='center', ha='left', fontsize=9, color=color_texto, fontweight='normal',
            zorder=3)

# ── 4. Ejes ───────────────────────────────────────────────────────────────────
ax.set_yticks(y_pos)
ax.set_yticklabels(deciles, fontsize=9, fontweight='normal', color=color_texto)
ax.set_ylabel('Decil de ingreso', fontsize=11, fontweight='medium', color=color_texto, labelpad=15)

ax.set_xlim(0, 108)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='x', labelsize=9, colors=color_texto)

# Grid y bordes A.6
ax.grid(axis='x', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

# ── 5. Títulos (Bloque Institucional A.6) ─────────────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura A.9.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Porcentaje de hogares con Servicios de Telecomunicaciones Móviles por decil de ingreso", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(95, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# ── 6. Leyenda ────────────────────────────────────────────────────────────────
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=2, fontsize=10, frameon=False, handlelength=2.5)

# ── 7. Notas al pie (Riguroso estilo A.6) ─────────────────────────────────────
font_size_notes = 8
x_start = 0.08

# Fuente
y_fuente = 0.06
ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')

note1_content = 'IFT con datos de la ENIGH 2022, del INEGI. Datos disponibles en: https://www.inegi.org.mx/programas/enigh/nc/2022/.'
ax.annotate(note1_content, xy=(x_start, y_fuente), xycoords='figure fraction',
            xytext=(35, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# ── 8. Guardar ────────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
output_path = os.path.join(os.path.dirname(__file__), "..", "..", 'output', 'Figura_A9.png')
fig.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"Gráfica guardada en: {output_path}")
plt.close(fig)