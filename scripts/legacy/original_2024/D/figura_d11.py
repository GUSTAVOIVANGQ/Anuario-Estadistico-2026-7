# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path
import os
import sys

try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

DATA_PATH = Path(r"C:\Users\ivan-\Documents\GitHub\anuario\datos\D.11\baseconfianzadigital.csv")
try:
    df = pd.read_csv(DATA_PATH, low_memory=False)
except:
    pass

usuarios = df[df["rescate_internet"] == 1].copy()
usuarios = usuarios[usuarios["sexo"].isin([1, 2])]

GRUPOS_SEXO = {1: "Mujeres", 2: "Hombres"}
CATEGORIAS = {1: "Muy seguro", 2: "Seguro", 3: "Ni seguro / Ni inseguro", 4: "Inseguro", 9: "NS/NR"}

denominador_sexo = usuarios.groupby("sexo")["fac_per"].sum()
denominador_total = usuarios["fac_per"].sum()

usuarios['seg_redes'] = usuarios['seg_redes'].fillna(9.0)
numerador_sexo = usuarios.groupby(["sexo", "seg_redes"])["fac_per"].sum().unstack(fill_value=0)

porcentajes_sexo = numerador_sexo.div(denominador_sexo, axis=0) * 100
porcentajes_sexo.index = porcentajes_sexo.index.map(GRUPOS_SEXO)

numerador_total = usuarios.groupby("seg_redes")["fac_per"].sum()
porcentajes_total = (numerador_total / denominador_total) * 100

df_plot = porcentajes_sexo.copy()
df_plot.loc["Total"] = porcentajes_total
df_plot.rename(columns=CATEGORIAS, inplace=True)
df_plot.rename(columns={"Ni seguro / Ni inseguro": "Ni seguro/\nNi inseguro"}, inplace=True)

df_plot = df_plot.reindex(["Hombres", "Mujeres", "Total"]).T

orden_y = ["NS/NR", "Inseguro", "Ni seguro/\nNi inseguro", "Seguro", "Muy seguro"]
orden_y = [y for y in orden_y if y in df_plot.index]
df_plot = df_plot.reindex(orden_y)
df_plot = df_plot[["Total", "Mujeres", "Hombres"]]

# ── Configuración de Gráfica Estilo A.7 ─────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
color_texto = '#3c3c3b'

# Degradado usando el mismo tono exacto (Teal)
COLORES = {
    "Total": "#335a5c",     # Teal oscuro (mismo de a7)
    "Mujeres": "#4a7d75",   # Teal medio
    "Hombres": "#86adae"    # Teal claro (mismo de a7)
}

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

n_grupos = len(df_plot.index)
bar_width = 0.22
indices = np.arange(n_grupos)

for i, col in enumerate(df_plot.columns):
    offset = (i - 1) * bar_width
    posiciones = indices + offset
    valores = df_plot[col]
    
    barras = ax.barh(posiciones, valores, height=bar_width * 0.9, label=col, color=COLORES[col], edgecolor='none', zorder=2)
    
    for barra in barras:
        ancho = barra.get_width()
        if ancho > 0:  
            ax.text(ancho + 1.0, barra.get_y() + barra.get_height()/2, f"{ancho:.1f}%",
                    va='center', ha='left', fontsize=9, fontweight='normal', color=color_texto, zorder=3)

ax.set_xlim(0, 68)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{int(v)}%'))
ax.tick_params(axis='x', labelsize=9, colors=color_texto)
ax.tick_params(axis='y', labelsize=9, colors=color_texto)
ax.invert_yaxis()

ax.set_yticks(indices)
ax.set_yticklabels(df_plot.index, fontsize=9, fontweight='normal', color=color_texto)

ax.grid(axis='x', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

# Encabezado A.7
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2, bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura D.11.", xy=(0, 1), xycoords='axes fraction', xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Porcentaje de la población usuaria de Internet, qué tan seguro es compartir información en redes sociales",
            xy=(0, 1), xycoords='axes fraction', xytext=(105, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Leyenda A.7
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=3, fontsize=10, frameon=False, handlelength=2.5, labelcolor=color_texto)

# Notas A.7
font_size_notes = 8
x_start = 0.08
y_fuente = 0.06
ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction', fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note1 = 'IFT, con información de la Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.'
ax.annotate(note1, xy=(x_start, y_fuente), xycoords='figure fraction', xytext=(35, 0), textcoords='offset points', fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.042
ax.annotate("Nota: ", xy=(x_start, y_nota), xycoords='figure fraction', fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note2 = 'Respuesta múltiple, por lo que la suma no da 100%. Resultados presentan variaciones por error teórico de la encuesta.'
ax.annotate(note2, xy=(x_start, y_nota), xycoords='figure fraction', xytext=(28, 0), textcoords='offset points', fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

fig.subplots_adjust(left=0.12, right=0.92, top=0.85, bottom=0.22)

output_path = r'output/Figura_D11.png'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"Figura guardada en: {output_path}")
plt.close(fig)