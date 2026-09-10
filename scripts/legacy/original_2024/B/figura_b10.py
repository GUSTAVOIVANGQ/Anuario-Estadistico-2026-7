"""
Figura B.10 (BAF) — Índice Herfindahl-Hirschman. Concentración de mercado
del Servicio Fijo de Acceso a Internet (2013-2023)
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys

try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ── 1. Carga y cálculo ────────────────────────────────────────────────────────
df = pd.read_csv(r"C:\Users\ivan-\Documents\GitHub\anuario\datos\b.10\TD_IHH_BAF_ITE_VA.csv", encoding="latin1")
df["IHH_BAF_E"] = (
    df["IHH_BAF_E"].astype(str)
    .str.replace(",", "").str.strip()
    .astype(float)
)
df["MES"]  = pd.to_numeric(df["MES"],  errors="coerce")
df["ANIO"] = pd.to_numeric(df["ANIO"], errors="coerce")

data = (
    df[df["MES"] == 12]
    .sort_values("ANIO")
    [["ANIO","IHH_BAF_E"]]
    .rename(columns={"ANIO":"anio","IHH_BAF_E":"ihh"})
)
data = data[(data["anio"] >= 2013) & (data["anio"] <= 2023)].reset_index(drop=True)

print("Valores calculados IHH BAF:")
print(data.to_string(index=False))

# ── 2. Figura estilo A.9 ──────────────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

COLOR_BAR = '#335a5c'  # Teal oscuro (Extraído de figura_a9)
color_texto = '#3c3c3b'

años = data["anio"].values
valores = data["ihh"].values
y_pos = range(len(años))
bar_height = 0.55

# Barras horizontales
bars = ax.barh(
    y_pos,
    valores,
    color=COLOR_BAR,
    height=bar_height,
    edgecolor='none',
    zorder=2
)

# ── 3. Anotaciones de valor ───────────────────────────────────────────────────
for i, val in enumerate(valores):
    ax.text(
        val + 50, i,
        f"{int(val):,}",
        va="center", ha="left",
        fontsize=9, color=color_texto, fontweight="normal",
        zorder=3
    )

# ── 4. Ejes y Cuadrícula ──────────────────────────────────────────────────────
ax.set_yticks(y_pos)
ax.set_yticklabels([str(a) for a in años], fontsize=9, fontweight='normal', color=color_texto)
ax.set_xlim(0, max(valores) * 1.15)
ax.invert_yaxis()

ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{int(v):,}'))
ax.tick_params(axis='x', labelsize=9, colors=color_texto)
ax.tick_params(axis='y', length=0)

# Grid y bordes A.9
ax.grid(axis='x', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

# ── 5. Títulos (Bloque Institucional A.9) ─────────────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura B.10.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Índice Herfindahl-Hirschman (IHH). Concentración de mercado del Servicio Fijo de Internet (2013-2023)", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(115, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# ── 6. Notas al pie (Riguroso estilo A.9) ─────────────────────────────────────
font_size_notes = 8
x_start = 0.08
y_fuente = 0.06
y_nota = 0.04

ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')

ax.annotate("IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de cada año.", 
            xy=(x_start, y_fuente), xycoords='figure fraction',
            xytext=(35, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

ax.annotate("Nota: ", xy=(x_start, y_nota), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')

ax.annotate("IHH estimado con respecto al número de accesos del servicio fijo de internet.", 
            xy=(x_start, y_nota), xycoords='figure fraction',
            xytext=(26, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# ── 7. Guardar ────────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "Figura_B10.png")
fig.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"Gráfica guardada en: {output_path}")
plt.close(fig)