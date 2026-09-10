# -*- coding: utf-8 -*-
"""
Figura A.7 — Porcentaje de hogares con servicios de telecomunicaciones
fijas por decil de ingreso

Gráfica de barras horizontales agrupadas con dos métricas:
  1. % Hogares con telecomunicaciones fijas
  2. % Hogares que disponen y gastan en telecomunicaciones fijas

Fuente: IFT con datos de la ENIGH 2022, del INEGI.
"""

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

# ==============================================================================
# 1. CARGA DE MICRODATOS ENIGH 2022
# ==============================================================================
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", 'datos', 'A.7', 'microdatos')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Cargando concentradohogar...")
concentrado = pd.read_csv(
    os.path.join(BASE, 'concentradohogar.csv'), low_memory=False,
    usecols=['folioviv', 'foliohog', 'ing_cor', 'factor'])
concentrado['ing_cor'] = pd.to_numeric(concentrado['ing_cor'], errors='coerce').fillna(0)

print("Cargando hogares...")
hogares = pd.read_csv(
    os.path.join(BASE, 'hogares.csv'), low_memory=False,
    usecols=['folioviv', 'foliohog', 'telefono', 'tv_paga', 'conex_inte'])

print("Cargando gastoshogar...")
gh = pd.read_csv(os.path.join(BASE, 'gastoshogar.csv'), low_memory=False,
                 usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri', 'gas_nm_tri'])

print("Cargando gastospersona...")
gp = pd.read_csv(os.path.join(BASE, 'gastospersona.csv'), low_memory=False,
                 usecols=['folioviv', 'foliohog', 'clave', 'gasto_tri'])

# ==============================================================================
# 2. GASTO EN TELECOMUNICACIONES FIJAS
# ==============================================================================
FIJAS_CLAVES = ['R005', 'R006', 'R008', 'R009', 'R010', 'R011']

gh['gasto'] = (pd.to_numeric(gh['gasto_tri'], errors='coerce').fillna(0)
               + pd.to_numeric(gh['gas_nm_tri'], errors='coerce').fillna(0))
gp['gasto'] = pd.to_numeric(gp['gasto_tri'], errors='coerce').fillna(0)

all_gastos = pd.concat([
    gh[['folioviv', 'foliohog', 'clave', 'gasto']],
    gp[['folioviv', 'foliohog', 'clave', 'gasto']]
])

gf = (all_gastos[all_gastos['clave'].isin(FIJAS_CLAVES)]
      .groupby(['folioviv', 'foliohog'])['gasto']
      .sum()
      .reset_index())
gf.columns = ['folioviv', 'foliohog', 'gasto_fijas']

# ==============================================================================
# 3. MERGE DE TABLAS Y DECILES
# ==============================================================================
print("Calculando indicadores y deciles...")
df = concentrado.merge(hogares, on=['folioviv', 'foliohog'], how='left')
df = df.merge(gf, on=['folioviv', 'foliohog'], how='left')
df['gasto_fijas'] = df['gasto_fijas'].fillna(0)

# Deciles usando pct_cum ponderado
df = df.sort_values('ing_cor').reset_index(drop=True)
df['pct_cum'] = df['factor'].cumsum() / df['factor'].sum()
df['decil'] = pd.cut(df['pct_cum'], bins=np.linspace(0, 1, 11), labels=range(1, 11), include_lowest=True).astype(int)

# ==============================================================================
# 4. INDICADORES
# ==============================================================================
df['tiene_fijas'] = ((df['telefono'] == 1) | (df['conex_inte'] == 1) | (df['tv_paga'] == 1) | (df['gasto_fijas'] > 0)).astype(int)

df['tiene_eq'] = ((df['telefono'] == 1) | (df['conex_inte'] == 1) | (df['tv_paga'] == 1)).astype(int)
df['dg_fijas'] = ((df['tiene_eq'] == 1) & (df['gasto_fijas'] > 0)).astype(int)

deciles = list(range(1, 11))
pct_tienen = []
pct_disponen_gastan = []

for d in deciles:
    sub = df[df['decil'] == d]
    tot = sub['factor'].sum()
    
    t = sub[sub['tiene_fijas'] == 1]['factor'].sum() / tot * 100
    dg = sub[sub['dg_fijas'] == 1]['factor'].sum() / tot * 100
    
    pct_tienen.append(t)
    pct_disponen_gastan.append(dg)

# ==============================================================================
# 5. GRÁFICA ESTILO A.9
# ==============================================================================
print("\nGenerando figura A.7...")
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Configuración de barras
y = np.arange(len(deciles))
bar_width = 0.38

# Colores replicados de Figura A.9
COLOR_CON_TELECOM = '#335a5c'  # Teal oscuro 
COLOR_DISPONEN = '#86adae'     # Teal claro
color_texto = '#3c3c3b'

# Barras horizontales
bars1 = ax.barh(y - bar_width/2, pct_tienen, bar_width, label='% Hogares con telecomunicaciones fijas', color=COLOR_CON_TELECOM, edgecolor='none', zorder=2)
bars2 = ax.barh(y + bar_width/2, pct_disponen_gastan, bar_width, label='% Hogares que disponen y gastan en telecomunicaciones fijas', color=COLOR_DISPONEN, edgecolor='none', zorder=2)

# Ejes
ax.set_yticks(y)
ax.set_yticklabels(deciles, fontsize=9, fontweight='normal', color=color_texto)
ax.set_ylabel('Decil de ingreso', fontsize=11, fontweight='medium', color=color_texto, labelpad=15)
# Decil 1 abajo, Decil 10 arriba (manteniendo lógica original de lectura)

ax.set_xlim(0, 108) # Mismo límite de holgura que la A9
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='x', labelsize=9, colors=color_texto)

# Grid y bordes A.9
ax.grid(axis='x', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

# Agregar los % al final de las barras (Números normales sin chip)
for i in range(len(deciles)):
    ax.text(pct_tienen[i] + 1.5, y[i] - bar_width/2, f'{pct_tienen[i]:.1f}%',
            va='center', ha='left', fontsize=9, color=color_texto, fontweight='normal', zorder=3)
    ax.text(pct_disponen_gastan[i] + 1.5, y[i] + bar_width/2, f'{pct_disponen_gastan[i]:.1f}%',
            va='center', ha='left', fontsize=9, color=color_texto, fontweight='normal', zorder=3)

# ==============================================================================
# 6. ENCABEZADO Y NOTAS (BLOQUE INSTITUCIONAL A.9)
# ==============================================================================
# Títulos
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura A.7.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Porcentaje de hogares con servicios de telecomunicaciones fijas por decil de ingreso", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(95, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Leyenda
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=2, fontsize=10, frameon=False, handlelength=2.5)

# Notas al pie
font_size_notes = 8
x_start = 0.08

y_fuente = 0.06
ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note1_content = 'IFT con datos de la ENIGH 2022, del INEGI. Datos disponibles en: https://www.inegi.org.mx/programas/enigh/nc/2022/.'
ax.annotate(note1_content, xy=(x_start, y_fuente), xycoords='figure fraction',
            xytext=(35, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.042
ax.annotate("Notas: ", xy=(x_start, y_nota), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note2_content = '¹ El valor de los deciles de ingreso se encuentra disponible en: https://www.inegi.org.mx/temas/ingresoshog/default.html#Informacion_general.'
ax.annotate(note2_content, xy=(x_start, y_nota), xycoords='figure fraction',
            xytext=(32, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# Ajustes de layout estilo A.9
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# Guardar
output_path = os.path.join(OUTPUT_DIR, 'figura_a7.png')
plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"Figura guardada en: {output_path}")
plt.close(fig)