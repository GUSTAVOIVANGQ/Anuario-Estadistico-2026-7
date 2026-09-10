"""
Figura D.7 — Anuario Estadístico IFT 2024
Usuarios que han vivido experiencias negativas al utilizar Internet
y/o realizar actividades en línea, por grupo de edad.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import matplotlib.ticker as mticker

# ── Rutas ─────────────────────────────────────────────────────────────────────
CSV_PATH = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\D.7\baseconfianzadigital.csv"
OUT_PATH = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_D7.png"

# ── Carga y filtro ────────────────────────────────────────────────────────────
df = pd.read_csv(CSV_PATH, low_memory=False)
df_usr = df[df['rescate_internet'] == 1].copy()   # solo usuarios de internet

# ── Grupos de edad y Variables ────────────────────────────────────────────────
GRUPOS = {
    1: '18 a 24 años',
    2: '25 a 34 años',
    3: '35 a 44 años',
    4: '45 a 54 años',
    5: '55 a más años',
}

EXPERIENCIAS = {
    'Recibir mensajes\nno deseados':              'expp_mensnd',
    'Han publicado información\npersonal sin su permiso': 'expp_pubipi',
    'Han usado sus datos para pedir\npréstamos o créditos sin su permiso': 'expp_datpre',
    'Han robado sus contraseñas':                 'expp_robcon',
}

# ── Cálculo ponderado ─────────────────────────────────────────────────────────
def pct_pond(df_sub, col):
    total = df_sub['fac_per'].sum()
    if total == 0:
        return np.nan
    si = df_sub[df_sub[col] == 1]['fac_per'].sum()
    return si / total * 100

resultados = {}
for g, label in GRUPOS.items():
    sub = df_usr[df_usr['edad_gpos'] == g]
    resultados[label] = {nombre: pct_pond(sub, col) for nombre, col in EXPERIENCIAS.items()}

GRUPOS_LABEL = list(GRUPOS.values())          
EXP_KEYS     = list(EXPERIENCIAS.keys())      

# ── Colores institucionales y Configuración Gráfica (Estilo F.16) ─────────────
# Adaptado con 4 colores de la "Paleta Teal" de la guía para combinar con el tono principal de la F16.
COLORES = {
    'Recibir mensajes\nno deseados':              '#86adae',   # Teal claro (como en Mujeres de F16)
    'Han publicado información\npersonal sin su permiso': '#64a0a1',  # Teal medio
    'Han usado sus datos para pedir\npréstamos o créditos sin su permiso': '#335a5c',  # Teal oscuro (como Hombres F16)
    'Han robado sus contraseñas':                 '#132b2d',   # Teal muy oscuro
}
color_texto = '#3c3c3b'

plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

n_grupos = len(GRUPOS_LABEL)
n_series = len(EXP_KEYS)
barra_w  = 0.18
x_base = np.arange(n_grupos)           

# ── Dibujar barras ────────────────────────────────────────────────────────────
all_rects = []
for i, exp in enumerate(EXP_KEYS):
    color = COLORES[exp]
    offset = (i - (n_series - 1) / 2) * barra_w

    valores = [resultados[g][exp] for g in GRUPOS_LABEL]
    xs = x_base + offset

    rects = ax.bar(xs, valores, width=barra_w * 0.88, color=color, edgecolor='none', zorder=2, label=exp.replace('\n', ' '))
    all_rects.append(rects)

# ── Etiquetas de datos (Chips estilo F.16) ────────────────────────────────────
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        bar_color = rect.get_facecolor()
        if height >= 5: # Ocultar menores a 5% por limpieza, igual que original
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 6),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                        bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

for rects in all_rects:
    autolabel(rects)

# ── Diseño limpio de Ejes ─────────────────────────────────────────────────────
ax.set_xlim(-0.55, n_grupos - 0.45)
ax.set_ylim(0, 85)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))

ax.set_xticks(x_base)
ax.set_xticklabels(GRUPOS_LABEL, fontsize=9, fontweight='normal', color=color_texto)
ax.tick_params(axis='y', labelsize=9, colors=color_texto)
ax.tick_params(axis='x', length=0)

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# ── Títulos ───────────────────────────────────────────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura D.7.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Usuarios que han vivido experiencias negativas al utilizar Internet y/o realizar actividades en línea, por grupo de edad", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# ── Leyenda ───────────────────────────────────────────────────────────────────
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=2, fontsize=10, frameon=False, handlelength=2.5)

# ── Notas al pie ──────────────────────────────────────────────────────────────
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = ('IFT, con información de la Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.')
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.04
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
nota_text = ('Respuesta múltiple, por lo que la suma no da 100%. Es importante señalar que los resultados pueden presentar variaciones\n'
             'que pueden ser explicadas por el error teórico de cada encuesta.')
fig.text(x_start + 0.025, y_nota, nota_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# ── Guardar ───────────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
plt.savefig(OUT_PATH, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()

print(f"✅  Figura guardada en: {OUT_PATH}")