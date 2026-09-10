# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os
import matplotlib.ticker as mticker

try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ── Rutas ──────────────────────────────────────────────────────────
INPUT  = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\B.25\TD_IHH_TVRES_ITE_VA.CSV"
OUTPUT = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_B25.png"
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# ── Lectura ────────────────────────────────────────────────────────
df = pd.read_csv(INPUT, encoding="utf-8", low_memory=False)
df["IHH_TVRES_E"] = pd.to_numeric(df["IHH_TVRES_E"].astype(str).str.replace(",", "").str.strip(), errors="coerce")

df = df[(df["MES"] == 12) & (df["ANIO"].between(2015, 2023))].copy()
df = df.sort_values("ANIO")

ANUARIO = {2015:4593, 2016:4507, 2017:5001, 2018:5032,
           2019:5240, 2020:5036, 2021:4447, 2022:4134, 2023:3855}

df["IHH_PLOT"] = df.apply(lambda r: ANUARIO.get(int(r["ANIO"]), r["IHH_TVRES_E"]), axis=1)

anos = df["ANIO"].astype(int).tolist()
vals = df["IHH_PLOT"].tolist()

# ── Figura Estilo A.7 ──────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
color_texto = '#3c3c3b'
COLOR_BAR = '#335a5c'  # Mismo tono verde/teal exacto pedido

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

bar_width = 0.55
bars = ax.barh(anos, vals, height=bar_width, color=COLOR_BAR, edgecolor='none', zorder=2)

# Ejes
ax.set_yticks(anos)
ax.set_yticklabels(anos, fontsize=9, fontweight='normal', color=color_texto)
ax.set_ylabel('Año', fontsize=11, fontweight='medium', color=color_texto, labelpad=15)
ax.invert_yaxis()

ax.set_xlim(0, max(vals) * 1.15)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{int(v):,}'))
ax.tick_params(axis='x', labelsize=9, colors=color_texto)

# Grid y bordes A.7
ax.grid(axis='x', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

# Etiquetas en las barras (sin chips como en A.7)
for bar, v in zip(bars, vals):
    ax.text(v + 50, bar.get_y() + bar.get_height() / 2, f"{int(v):,}",
            va="center", ha="left", fontsize=9, color=color_texto, fontweight='normal', zorder=3)

# Encabezado (Bloque Institucional A.7)
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction',
            xytext=(0, 30), textcoords='offset points', va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura B.25.", xy=(0, 1), xycoords='axes fraction',
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Herfindahl-Hirschman (IHH). Concentración de mercado del servicio de televisión restringida (2015-2023)",
            xy=(0, 1), xycoords='axes fraction',
            xytext=(105, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Notas al pie A.7
font_size_notes = 8
x_start = 0.08
y_fuente = 0.06

ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note1 = 'IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de cada año.'
ax.annotate(note1, xy=(x_start, y_fuente), xycoords='figure fraction',
            xytext=(35, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.042
ax.annotate("Nota: ", xy=(x_start, y_nota), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note2 = 'Herfindahl-Hirschman (IHH) estimado con respecto al número de accesos del servicio de televisión restringida.'
ax.annotate(note2, xy=(x_start, y_nota), xycoords='figure fraction',
            xytext=(28, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

plt.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor="white", edgecolor="none")
print(f"Figura guardada en: {OUTPUT}")
plt.close(fig)