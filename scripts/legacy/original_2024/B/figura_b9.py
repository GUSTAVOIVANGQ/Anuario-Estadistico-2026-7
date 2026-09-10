#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figura B.9 — Participación de mercado del Servicio Fijo de Telefonía (2013-2023)
Replicando el estilo UI institucional de B.17
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os
import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ── 1. LECTURA Y LIMPIEZA ──
base_path = Path(__file__).parent.parent
repo_root = base_path.parent
data_file = repo_root / "datos" / "b.9" / "TD_MARKET_SHARE_TELFIJA_ITE_VA.csv"
output_dir = repo_root / "output"
output_dir.mkdir(exist_ok=True, parents=True)

df = pd.read_csv(data_file, encoding="latin1")
df["MARKET_SHARE"] = df["MARKET_SHARE"].str.replace("%", "").str.strip().astype(float)

# ── 2. FILTRO ──
df_dic = df[(df["MES"] == 12) & (df["ANIO"].between(2013, 2023))].copy()

# ── 3. MAPEO ──
mapeo = {
    "AMÉRICA MÓVIL":  "América Móvil",
    "GRUPO TELEVISA": "Grupo Televisa",
    "MEGACABLE-MCM":  "Megacable-MCM",
    "GRUPO SALINAS":  "Grupo Salinas",
    "AXTEL":          "Axtel",
    "TELEFÓNICA":     "Telefónica",
}
df_dic["GRUPO_FIGURA"] = df_dic["GRUPO"].map(mapeo).fillna("Otros")

# ── 4. PIVOTE ──
pivot = df_dic.groupby(["ANIO", "GRUPO_FIGURA"])["MARKET_SHARE"].sum().unstack(fill_value=0)

orden = [
    "América Móvil", "Grupo Televisa", "Megacable-MCM",
    "Grupo Salinas", "Axtel", "Telefónica", "Otros"
]
pivot = pivot.reindex(columns=orden, fill_value=0)
years = pivot.index.astype(int).tolist()

# Colores Institucionales
COLORES_DICT = {
    "América Móvil":  "#1e6284",
    "Grupo Televisa": "#ed8945",
    "Megacable-MCM":  "#5844a0",
    "Grupo Salinas":  "#99b554",
    "Axtel":          "#8e244d",
    "Telefónica":     "#368491",
    "Otros":          "#728781",
}
colores_list = [COLORES_DICT[g] for g in orden]

# ── 5. CONFIGURACIÓN DE FIGURA ──
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
C_TEXT = '#3c3c3b'

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

x = np.arange(len(years))
width = 0.45 

bottoms = np.zeros(len(years))
bottoms_dict = {}

for grupo, color in zip(orden, colores_list):
    vals = pivot[grupo].values
    bottoms_dict[grupo] = bottoms.copy()
    ax.bar(x, vals, width, bottom=bottoms, color=color, label=grupo, edgecolor='white', linewidth=0.5, zorder=3)
    bottoms += vals

# ── 6. ETIQUETAS (Chips y Líneas Cuadradas idéntico a B.17) ──
chip_style = dict(boxstyle="round,pad=0.3,rounding_size=0.6", fc="white", ec="#D1D1DF", lw=1.2)
min_dist = 4.0 

for i, x_val in enumerate(x):
    last_y = -10
    
    for j, (grupo, color) in enumerate(zip(orden, colores_list)):
        val = pivot[grupo].values[i]
        if val >= 0.1: 
            y_center = bottoms_dict[grupo][i] + val / 2
            
            y_text = max(y_center, last_y + min_dist)
            last_y = y_text
            
            x_text = x_val - (width / 2) - 0.12 
            x_target = x_val - (width / 2)
            
            x_elbow = x_text + 0.02 + (j * 0.008) 
            
            ax.plot([x_text, x_elbow, x_elbow, x_target], 
                    [y_text, y_text, y_center, y_center], 
                    color="#A0A0B0", lw=1.2, zorder=3)
            
            chip_text = f"{val:.2f}%"
            ax.annotate(chip_text, xy=(x_text, y_text),
                        ha="right", va="center",
                        bbox=chip_style, color=color, fontweight='bold', fontsize=8,
                        zorder=4)

# ── 7. EJES Y ESTILO ──
ax.set_xticks(x)
ax.set_xticklabels([str(y) for y in years], fontsize=10, fontweight='bold', color=C_TEXT)
ax.tick_params(axis='x', length=0, pad=8) 

ax.set_ylim(0, 105)
ax.set_yticks([]) 

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['bottom'].set_linewidth(1)

# ── 8. ENCABEZADO Y PIE ──
fig.text(0.08, 0.92, '   ', fontsize=2, va='center',
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))
fig.text(0.095, 0.92, 'Figura B.9.', fontsize=14, fontweight='bold', color=C_TEXT, va='center')
fig.text(0.165, 0.92, 'Participación de mercado del Servicio Fijo de Telefonía (2013-2023)', 
           fontsize=14, fontweight='medium', color=C_TEXT, va='center')

handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.08),
           ncol=7, frameon=False, prop={'weight': 'bold', 'size': 10}, labelcolor=C_TEXT)

fig.text(0.08, 0.05, "Fuente:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.115, 0.05, "IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de cada año.", fontsize=8, color=C_TEXT)
fig.text(0.08, 0.03, "Nota:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.108, 0.03, "Participación de mercado estimada con respecto al número de líneas del servicio fijo de telefonía.", fontsize=8, color=C_TEXT)

plt.subplots_adjust(left=0.10, right=0.92, top=0.85, bottom=0.18)

# ── 9. GUARDAR FIGURA ──
output_file = output_dir / "figura_B9.png"
plt.savefig(output_file, dpi=200, bbox_inches='tight', facecolor='white')
print(f"Guardada: {output_file}")
plt.close(fig)