"""
Figura C.16 — Herfindahl-Hirschman (IHH). Concentración de mercado
              del servicio móvil de acceso a Internet (2013-2023)
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import matplotlib.ticker as mticker
import os

try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ── 1. LECTURA ───────────────────────────────────────────────────────────────
CSV_PATH = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\C.16\TD_IHH_INTMOVIL_ITE_VA.csv"
if not os.path.exists(CSV_PATH):
    print(f"ERROR: No se encontró {CSV_PATH}")
    sys.exit(1)

df = pd.read_csv(CSV_PATH, encoding="latin-1")

# ── 2. LIMPIEZA ──────────────────────────────────────────────────────────────
df["IHH"] = df["IHH_TELFIJA_E"].astype(str).str.replace(",", "").str.strip()
df["IHH"] = pd.to_numeric(df["IHH"], errors="coerce")

# ── 3. FILTRO ────────────────────────────────────────────────────────────────
df_dic = df[(df["MES"] == 12) & (df["ANIO"] >= 2013) & (df["ANIO"] <= 2023)].copy()
df_dic = df_dic.sort_values("ANIO").reset_index(drop=True)

anios = df_dic["ANIO"].tolist()
ihh   = df_dic["IHH"].tolist()

# ── 4. GRÁFICA ESTILO A.9 ────────────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# El tono exacto de figura_a9.py
COLOR_BARRA = '#335a5c'  
color_texto = '#3c3c3b'

anios_inv = anios[::-1]
ihh_inv   = ihh[::-1]

y = range(len(anios_inv))
bar_height = 0.55

bars = ax.barh(list(y), ihh_inv, height=bar_height, color=COLOR_BARRA, edgecolor='none', zorder=2)

# ── 5. ANOTACIONES DE VALOR ──────────────────────────────────────────────────
x_max = max(ihh_inv)
for bar, val in zip(bars, ihh_inv):
    ax.text(val + x_max * 0.01, bar.get_y() + bar.get_height() / 2, 
            f"{val:,.0f}", 
            va='center', ha='left', fontsize=10, color=color_texto, fontweight='normal', zorder=3)

# ── 6. EJES Y CUADRÍCULA ─────────────────────────────────────────────────────
ax.set_yticks(list(y))
ax.set_yticklabels(anios_inv, fontsize=10, fontweight='normal', color=color_texto)
ax.set_xlim(0, x_max * 1.15)

ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:,.0f}'))
ax.tick_params(axis='x', labelsize=10, colors=color_texto)

# Grid y bordes replicados de A.9
ax.grid(axis='x', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

# ── 7. TÍTULOS (Bloque Institucional A.9) ────────────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura C.16.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Herfindahl-Hirschman (IHH). Concentración de mercado del servicio móvil de acceso a Internet", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(105, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# ── 8. NOTAS AL PIE ──────────────────────────────────────────────────────────
font_size_notes = 8
x_start = 0.08

y_fuente = 0.06
ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note1_content = 'IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de cada año.'
ax.annotate(note1_content, xy=(x_start, y_fuente), xycoords='figure fraction',
            xytext=(35, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.035
ax.annotate("Nota: ", xy=(x_start, y_nota), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note2_content = 'Herfindahl-Hirschman (IHH) estimado con respecto al número de líneas del servicio móvil de acceso a Internet.'
ax.annotate(note2_content, xy=(x_start, y_nota), xycoords='figure fraction',
            xytext=(28, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# ── 9. GUARDAR ───────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
os.makedirs("output", exist_ok=True)
OUTPUT = "output/Figura_C16.png"
fig.savefig(OUTPUT, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"Gráfica guardada en: {OUTPUT}")
plt.close(fig)