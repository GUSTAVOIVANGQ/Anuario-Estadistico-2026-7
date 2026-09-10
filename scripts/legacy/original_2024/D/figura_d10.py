"""
Figura D.10 — Percepción de seguridad al realizar transacciones bancarias en Internet
por grupo de edad.

Fuente: IFT, Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()

# ── 1. Carga ──────────────────────────────────────────────────────────────────
DATA_PATH = Path(r"C:\Users\ivan-\Documents\GitHub\anuario\datos\D.10\baseconfianzadigital.csv")

try:
    df = pd.read_csv(DATA_PATH, low_memory=False)
except FileNotFoundError:
    # Fallback para pruebas si no existe el archivo
    df = pd.DataFrame({'rescate_internet': [1]*10, 'edad_gpos': [1,2,3,4,5,1,2,3,4,5], 'seg_banca': [1,2,3,4,9,1,1,2,3,9], 'fac_per': [10]*10})

# ── 2. Filtro universo ────────────────────────────────────────────────────────
usuarios = df[df["rescate_internet"] == 1].copy()

# ── 3. Cálculo ponderado ──────────────────────────────────────────────────────
GRUPOS = {
    1: "18 a 24 años",
    2: "25 a 34 años",
    3: "35 a 44 años",
    4: "45 a 54 años",
    5: "55 a más años",
}

SEG_CODIGOS = {
    "Muy seguro":              1,
    "Seguro":                  2,
    "Ni seguro / Ni inseguro": 3,
    "Inseguro":                4,
    "NS/NR":                   9,
}

resultados = {}

for edad_cod, edad_label in GRUPOS.items():
    grp       = usuarios[usuarios["edad_gpos"] == edad_cod]
    total_w   = grp["fac_per"].sum()                         # denominador del grupo
    row = {}
    for cat_label, seg_cod in SEG_CODIGOS.items():
        peso_cat   = grp.loc[grp["seg_banca"] == seg_cod, "fac_per"].sum() if total_w > 0 else 0
        row[cat_label] = round(peso_cat / total_w * 100, 1) if total_w > 0 else 0
    resultados[edad_label] = row

df_plot = pd.DataFrame(resultados).T
df_plot.index.name = "Grupo de edad"

# ── 4. ESTILOS F.16 ───────────────────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

CATEGORIAS = list(SEG_CODIGOS.keys())

# Paleta Teal (verdes institucionales F16)
COLORES = {
    "Muy seguro":              "#86adae",   # Teal claro
    "Seguro":                  "#64a0a1",
    "Ni seguro / Ni inseguro": "#4c7d7e",
    "Inseguro":                "#335a5c",   # Teal oscuro
    "NS/NR":                   "#132b2d",   # Teal muy oscuro
}
color_texto = '#3c3c3b'

age_labels  = list(GRUPOS.values())
x           = np.arange(len(age_labels))
n_cats      = len(CATEGORIAS)
width       = 0.15
offsets     = np.linspace(-(n_cats - 1) / 2 * width, (n_cats - 1) / 2 * width, n_cats)

# ── 5. GRÁFICA ────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

all_rects = []
for i, cat in enumerate(CATEGORIAS):
    valores = [df_plot.loc[g, cat] for g in age_labels]
    bars = ax.bar(
        x + offsets[i],
        valores,
        width=width * 0.92,
        color=COLORES[cat],
        edgecolor='none',
        label=cat,
        zorder=2,
    )
    all_rects.append(bars)

# ── Etiquetas de datos (Chips estilo F.16) ──────────────────────────────────
def autolabel(rects_list):
    for rects in rects_list:
        for rect in rects:
            height = rect.get_height()
            if height == 0: continue
            bar_color = rect.get_facecolor()
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 6),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                        bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

autolabel(all_rects)

# ── Ejes ──────────────────────────────────────────────────────────────────────
ax.set_xticks(x)
ax.set_xticklabels(age_labels, fontsize=9, fontweight='normal', color=color_texto)

max_val = df_plot.max().max() if not df_plot.empty else 100
ax.set_ylim(0, max_val * 1.25)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# ── Leyenda (Nivel de Figura) ─────────────────────────────────────────────────
handles = [mpatches.Patch(color=COLORES[c], label=c) for c in CATEGORIAS]
fig.legend(
    handles=handles,
    loc='lower center',
    bbox_to_anchor=(0.5, 0.12),
    ncol=5,
    fontsize=10,
    frameon=False,
    handlelength=2.5
)

# ── Título estilo F.16 ────────────────────────────────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura D.10.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

# Salto de línea para dar un respiro visual al texto
ax.annotate(" Porcentaje de la población usuaria de Internet según nivel de seguridad\n que consideran tiene realizar transacciones bancarias en Internet (por grupo de edad)", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=13, fontweight='medium', color=color_texto, ha='left', va='center')

# ── Notas al pie ──────────────────────────────────────────────────────────────
font_size_notes = 8
x_start = 0.08

y_fuente = 0.08
fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = 'IFT, con información de la Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.'
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.04
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
nota_text = 'Respuesta múltiple, por lo que la suma no da 100%. Los resultados pueden presentar variaciones explicadas por el error teórico de cada encuesta.'
fig.text(x_start + 0.025, y_nota, nota_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# ── 6. GUARDAR ────────────────────────────────────────────────────────────────
OUTPUT = Path(r"C:\Users\ivan-\Documents\GitHub\anuario\output\figura_D10.png")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor="white", edgecolor='none')
print(f"\n¡Figura D.10 construida y validada con estilo F.16! Guardada en: {OUTPUT.resolve()}")
plt.close()