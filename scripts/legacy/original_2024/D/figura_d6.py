"""
Figura D.6 — Usuarios que han vivido experiencias negativas al utilizar Internet
             y/o realizar actividades en línea, por sexo
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import matplotlib.patches as mpatches
import numpy as np
import matplotlib.ticker as mticker

# ── 1. Rutas ──────────────────────────────────────────────────────────────────
OUT_DIR  = os.path.join(r"C:\Users\ivan-\Documents\GitHub\anuario\output")
CSV_PATH = os.path.join(r"C:\Users\ivan-\Documents\GitHub\anuario\datos\D.6\baseconfianzadigital.csv")

# ── 2. Carga y filtro ─────────────────────────────────────────────────────────
df = pd.read_csv(CSV_PATH, low_memory=False)

# Solo usuarios de Internet
usuarios = df[df["rescate_internet"] == 1].copy()

# ── 3. Variables de experiencias negativas ────────────────────────────────────
VARS = {
    "expp_mensnd": "Recibir mensajes\nno deseados",
    "expp_pubipi": "Han publicado información\npersonal sin su permiso",
    "expp_datpre": "Han usado sus datos para pedir\npréstamos o créditos sin su permiso",
    "expp_robcon": "Han robado sus contraseñas",
}

GRUPOS = {
    "Hombres": usuarios[usuarios["sexo"] == 2],
    "Mujeres": usuarios[usuarios["sexo"] == 1],
    "Total"  : usuarios,
}

# ── 4. Cálculo de porcentajes ponderados ──────────────────────────────────────
resultados = {}
for grupo, sub in GRUPOS.items():
    total_pond = sub["fac_per"].sum()
    resultados[grupo] = {}
    for var in VARS:
        n = sub[sub[var] == 1]["fac_per"].sum()
        resultados[grupo][var] = round(n / total_pond * 100, 1)

# ── 5. Estructura para la gráfica ─────────────────────────────────────────────
categorias = list(VARS.keys())
etiquetas  = list(VARS.values())
n_cat      = len(categorias)

val_general = [resultados["Total"][v]   for v in categorias]
val_mujeres = [resultados["Mujeres"][v] for v in categorias]
val_hombres = [resultados["Hombres"][v] for v in categorias]

# ── 6. Colores y Configuración Gráfica (Estilo F.16) ──────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Colores institucionales alineados a la Paleta Teal
COLOR_GENERAL = '#afafaf'  # Gris verde
COLOR_MUJERES = '#86adae'  # Teal claro
COLOR_HOMBRES = '#335a5c'  # Teal oscuro
color_texto = '#3c3c3b'

# ── 7. Dibujar barras ─────────────────────────────────────────────────────────
x = np.arange(n_cat)
width = 0.25 

rects1 = ax.bar(x - width, val_general, width, label='General', color=COLOR_GENERAL, edgecolor='none', zorder=2)
rects2 = ax.bar(x, val_mujeres, width, label='Mujeres', color=COLOR_MUJERES, edgecolor='none', zorder=2)
rects3 = ax.bar(x + width, val_hombres, width, label='Hombres', color=COLOR_HOMBRES, edgecolor='none', zorder=2)

# ── 8. Etiquetas de datos (Chips estilo F.16) ─────────────────────────────────
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        bar_color = rect.get_facecolor()
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                    bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

autolabel(rects1)
autolabel(rects2)
autolabel(rects3)

# ── 9. Diseño limpio de Ejes ──────────────────────────────────────────────────
ax.set_xticks(x)
ax.set_xticklabels(etiquetas, fontsize=9, fontweight='normal', color=color_texto)

ax.set_ylim(0, max(max(val_general), max(val_mujeres), max(val_hombres)) * 1.25)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# ── 10. Títulos ───────────────────────────────────────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura D.6.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Usuarios que han vivido experiencias negativas al utilizar Internet y/o realizar actividades en línea, por sexo", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# ── 11. Leyenda ───────────────────────────────────────────────────────────────
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=3, fontsize=10, frameon=False, handlelength=2.5)

# ── 12. Notas al pie ──────────────────────────────────────────────────────────
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = ('IFT, con información de la Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.')
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.04
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
nota_text = 'Respuesta múltiple, por lo que la suma no da 100%. La Encuesta fue levantada mediante entrevistas telefónicas realizadas a personas de 18 años y más.'
fig.text(x_start + 0.025, y_nota, nota_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# ── 13. Guardar ───────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
out_path = os.path.join(OUT_DIR, "Figura_D6.png")
plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print(f"¡Figura guardada en: {out_path}")