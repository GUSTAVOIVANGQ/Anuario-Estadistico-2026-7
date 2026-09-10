import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
import sys

# Logging setup
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()

# ==========================================
# 1. CÁLCULO DE DATOS EXACTOS
# ==========================================

file_path = r'C:\Users\ivan-\Documents\GitHub\anuario\datos\E.5\Base de datos_Cuarta Encuesta 2023_MiPymes.xlsx'
df = pd.read_excel(file_path)

size_col = 'Clasificación de la empresa por su tamaño'
factor_col = 'Factor de Expansión Final'

# Mapeo de columnas para Internet Fijo
internet_cols = {
    "Más gente conoce la empresa": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? Gracias al Internet, ahora más gente conoce la empresa o negocio.',
    "Están más cerca de sus clientes/consumidores": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? El Internet permite que la empresa o negocio esté más cerca de sus consumidores.',
    "Hay más ventas/clientes": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? Gracias a la conexión a Internet de la empresa o negocio ahora hay más ventas/clientes',
    "Disminución de los costos al poder encontrar más y mejores proveedores": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? La conexión a Internet ha permitido disminuir los costos al poder encontrar más y mejores proveedores',
    "Desarrollar nuevos productos o servicios": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? Contar con Internet ha permitido a la empresa o negocio desarrollar nuevos productos o servicios.',
    "La entrega de productos o servicios es más rápida o menos costosa": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? El Internet de la empresa o negocio ha permitido que la entrega de productos o servicios sea más rápida o menos costosa.',
    "Los empleados hacen más en el mismo tiempo": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? El Internet de la empresa ha permitido que los empleados hagan más en el mismo tiempo.'
}

# Mapeo de columnas para Telefonía Fija
telefonia_cols = {
    "Más gente conoce la empresa": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? Gracias a la línea telefónica fija, ahora más gente conoce la empresa o negocio.',
    "Están más cerca de sus clientes/consumidores": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? La línea telefónica fija permite que la empresa o negocio esté más cerca de sus consumidores.',
    "Hay más ventas/clientes": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? Gracias a la línea telefónica fija de la empresa o negocio ahora hay más ventas / Clientes.',
    "Disminución de los costos al poder encontrar más y mejores proveedores": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? La línea telefónica fija ha permitido disminuir los costos al poder encontrar más y mejores proveedores.',
    "Desarrollar nuevos productos o servicios": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? Contar con una línea telefónica fija ha permitido a la empresa o negocio desarrollar nuevos productos o servicios.',
    "La entrega de productos o servicios es más rápida o menos costosa": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? La línea telefónica de la empresa o negocio ha permitido que la entrega de productos o servicios sea más rápida o menos costosa.',
    "Los empleados hacen más en el mismo tiempo": 'En una escala del 0 al 10, donde 0 es “totalmente en desacuerdo” y 10 es “totalmente de acuerdo”, ¿qué tan de acuerdo está con las siguientes frases? La línea telefónica fija de la empresa o negocio ha permitido que los empleados hagan más en el mismo tiempo.'
}

# Función para promedio ponderado excluyendo Ns/Nc
def promedio_ponderado(df_subset, col_name):
    temp = df_subset[[col_name, factor_col]].copy()
    temp = temp[pd.notna(temp[col_name])]
    temp = temp[temp[col_name] != 'Ns/Nc']
    if len(temp) == 0: return 0.0
    temp[col_name] = pd.to_numeric(temp[col_name])
    suma_ponderada = (temp[col_name] * temp[factor_col]).sum()
    peso_total = temp[factor_col].sum()
    return suma_ponderada / peso_total

beneficios = list(internet_cols.keys())
sizes = ['Micro', 'Pequeña', 'Mediana']

# Se crea el diccionario "data" usando los resultados calculados
data = {}
for s in sizes:
    data[s] = {
        "benefits": beneficios,
        "internet": [round(promedio_ponderado(df[df[size_col] == s], internet_cols[b]), 1) for b in beneficios],
        "telefonia": [round(promedio_ponderado(df[df[size_col] == s], telefonia_cols[b]), 1) for b in beneficios]
    }

# ==========================================
# 2. CONFIGURACIÓN DE LA GRÁFICA (Estilo Original)
# ==========================================

# ── Layout constants ──────────────────────────────────────────────────────────
COLORS = {
    "internet_bar":  "#3a7ca5",   # medium blue
    "internet_bg":   "#c8dcea",   # light blue bg
    "telefonia_bar": "#2d5a6b",   # dark teal
    "telefonia_bg":  "#b0c8d0",   # light teal bg
    "header_bg":     "#f5f5f5",
    "row_alt":       "#fafafa",
    "row_normal":    "#ffffff",
    "section_label": "#e8f0f5",
    "border":        "#d0d8de",
    "text_dark":     "#2c3e50",
    "text_mid":      "#4a5568",
    "red_dot":       "#e53e3e",
    "title_bar":     "#2d5a6b",
}

BAR_MAX   = 10.0
FIG_W     = 16
FIG_H     = 14

# ── Figure ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor="white")

# Outer rounded border (drawn via a tight axes)
border_ax = fig.add_axes([0, 0, 1, 1])
border_ax.set_xlim(0, 1); border_ax.set_ylim(0, 1)
border_ax.axis("off")
fancy = FancyBboxPatch((0.01, 0.01), 0.98, 0.98,
                       boxstyle="round,pad=0.0,rounding_size=0.015",
                       linewidth=1.5, edgecolor="#b0bec5",
                       facecolor="white", zorder=0)
border_ax.add_patch(fancy)

# ── Title ─────────────────────────────────────────────────────────────────────
title_ax = fig.add_axes([0.02, 0.935, 0.96, 0.05])
title_ax.set_xlim(0, 1); title_ax.set_ylim(0, 1); title_ax.axis("off")
# Red bullet
title_ax.plot(0.005, 0.5, "o", color=COLORS["red_dot"], markersize=7, transform=title_ax.transAxes)
title_ax.text(0.018, 0.5,
              "Figura E.5. ",
              fontsize=9, fontweight="bold", color=COLORS["text_dark"],
              va="center", transform=title_ax.transAxes)
title_ax.text(0.105, 0.5,
              "Percepción de las MiPymes sobre los beneficios de contar con servicios de Internet fijo y/o telefonía fija",
              fontsize=9, color=COLORS["text_dark"],
              va="center", transform=title_ax.transAxes)

# ── Main table area ───────────────────────────────────────────────────────────
TABLE_L   = 0.02
TABLE_R   = 0.98
TABLE_TOP = 0.925
TABLE_BOT = 0.095

# Column x-positions (in figure coords)
COL_TYPE_L  = TABLE_L
COL_TYPE_R  = 0.095
COL_BEN_L   = COL_TYPE_R
COL_BEN_R   = 0.52
COL_INT_L   = COL_BEN_R
COL_INT_R   = 0.74
COL_TEL_L   = COL_INT_R
COL_TEL_R   = TABLE_R

# ── Header row ────────────────────────────────────────────────────────────────
HDR_H = 0.085
hdr_ax = fig.add_axes([TABLE_L, TABLE_TOP - HDR_H, TABLE_R - TABLE_L, HDR_H])
hdr_ax.set_xlim(0, 1); hdr_ax.set_ylim(0, 1); hdr_ax.axis("off")
hdr_ax.set_facecolor(COLORS["header_bg"])

# Convert global col positions to local (0‥1) for this axes
def to_local(gx, left=TABLE_L, width=TABLE_R - TABLE_L):
    return (gx - left) / width

type_c  = to_local((COL_TYPE_L + COL_TYPE_R) / 2)
ben_c   = to_local((COL_BEN_L  + COL_BEN_R)  / 2)
int_c   = to_local((COL_INT_L  + COL_INT_R)  / 2)
tel_c   = to_local((COL_TEL_L  + COL_TEL_R)  / 2)

hdr_ax.text(type_c, 0.52, "Tipo de\nempresa",
            ha="center", va="center", fontsize=8.5,
            color=COLORS["text_mid"], style="italic")
hdr_ax.text(ben_c,  0.52, "Beneficios de contar con los servicios",
            ha="center", va="center", fontsize=8.5,
            color=COLORS["text_mid"], style="italic")
hdr_ax.text(int_c,  0.52, "Internet fijo",
            ha="center", va="center", fontsize=8.5,
            color=COLORS["text_mid"], style="italic")
hdr_ax.text(tel_c,  0.52, "Telefonía fija",
            ha="center", va="center", fontsize=8.5,
            color=COLORS["text_mid"], style="italic")

# Divider lines inside header
for gx in [COL_TYPE_R, COL_BEN_R, COL_INT_R]:
    lx = to_local(gx)
    hdr_ax.axvline(lx, color=COLORS["border"], linewidth=0.8)

hdr_ax.add_patch(FancyBboxPatch((0, 0), 1, 1,
                                boxstyle="square,pad=0",
                                linewidth=0.8, edgecolor=COLORS["border"],
                                facecolor=COLORS["header_bg"], zorder=0))

# ── Data rows ─────────────────────────────────────────────────────────────────
sections = list(data.keys())
ROWS_PER = 7

total_rows  = len(sections) * ROWS_PER
body_height = TABLE_TOP - HDR_H - TABLE_BOT
row_height  = body_height / total_rows

BAR_PAD  = 0.08   # fraction of row height as padding top/bottom for bar
VAL_PAD  = 0.02   # extra padding after value label

for s_idx, section in enumerate(sections):
    sec_data   = data[section]
    benefits   = sec_data["benefits"]
    internet   = sec_data["internet"]
    telefonia  = sec_data["telefonia"]
    n_rows     = len(benefits)

    sec_top_fig = TABLE_TOP - HDR_H - s_idx * ROWS_PER * row_height
    sec_bot_fig = sec_top_fig - ROWS_PER * row_height
    sec_h_fig   = sec_top_fig - sec_bot_fig

    # Section label background (left column)
    sec_label_ax = fig.add_axes([COL_TYPE_L, sec_bot_fig,
                                 COL_TYPE_R - COL_TYPE_L, sec_h_fig])
    sec_label_ax.set_xlim(0, 1); sec_label_ax.set_ylim(0, 1)
    sec_label_ax.axis("off")
    sec_label_ax.set_facecolor(COLORS["section_label"])
    sec_label_ax.add_patch(FancyBboxPatch((0, 0), 1, 1,
                                          boxstyle="square,pad=0",
                                          linewidth=0.5,
                                          edgecolor=COLORS["border"],
                                          facecolor=COLORS["section_label"],
                                          zorder=0))
    sec_label_ax.text(0.5, 0.55, section,
                      ha="center", va="center",
                      fontsize=9, fontweight="bold",
                      color=COLORS["text_dark"])

    # Individual data rows
    for r_idx, (benefit, iv, tv) in enumerate(zip(benefits, internet, telefonia)):
        row_top = sec_top_fig - r_idx * row_height
        row_bot = row_top - row_height

        bg_color = COLORS["row_alt"] if r_idx % 2 == 0 else COLORS["row_normal"]

        # Benefit text column
        ben_w = COL_BEN_R - COL_BEN_L
        ben_ax = fig.add_axes([COL_BEN_L, row_bot, ben_w, row_height])
        ben_ax.set_xlim(0, 1); ben_ax.set_ylim(0, 1); ben_ax.axis("off")
        ben_ax.set_facecolor(bg_color)
        ben_ax.add_patch(FancyBboxPatch((0, 0), 1, 1,
                                        boxstyle="square,pad=0",
                                        linewidth=0.4,
                                        edgecolor=COLORS["border"],
                                        facecolor=bg_color, zorder=0))
        ben_ax.text(0.03, 0.5, benefit,
                    ha="left", va="center", fontsize=7.3,
                    color=COLORS["text_dark"])

        # ── Internet bar column ──
        int_w = COL_INT_R - COL_INT_L
        int_ax = fig.add_axes([COL_INT_L, row_bot, int_w, row_height])
        int_ax.set_xlim(0, 1); int_ax.set_ylim(0, 1); int_ax.axis("off")
        int_ax.set_facecolor(bg_color)
        int_ax.add_patch(FancyBboxPatch((0, 0), 1, 1,
                                        boxstyle="square,pad=0",
                                        linewidth=0.4,
                                        edgecolor=COLORS["border"],
                                        facecolor=bg_color, zorder=0))

        # value label width (reserved on the left)
        val_label_frac = 0.18
        bar_left  = val_label_frac + VAL_PAD
        bar_avail = 0.95 - bar_left

        bar_frac  = iv / BAR_MAX
        bar_h     = 1.0 - 2 * BAR_PAD

        # background bar
        int_ax.add_patch(FancyBboxPatch((bar_left, BAR_PAD),
                                        bar_avail, bar_h,
                                        boxstyle="square,pad=0",
                                        facecolor=COLORS["internet_bg"],
                                        edgecolor="none", zorder=1))
        # filled bar
        int_ax.add_patch(FancyBboxPatch((bar_left, BAR_PAD),
                                        bar_avail * bar_frac, bar_h,
                                        boxstyle="square,pad=0",
                                        facecolor=COLORS["internet_bar"],
                                        edgecolor="none", zorder=2))
        # value
        int_ax.text(val_label_frac * 0.55, 0.5, f"{iv:.1f}",
                    ha="center", va="center", fontsize=8,
                    fontweight="bold", color=COLORS["text_dark"], zorder=3)

        # ── Telefonía bar column ──
        tel_w = COL_TEL_R - COL_TEL_L
        tel_ax = fig.add_axes([COL_TEL_L, row_bot, tel_w, row_height])
        tel_ax.set_xlim(0, 1); tel_ax.set_ylim(0, 1); tel_ax.axis("off")
        tel_ax.set_facecolor(bg_color)
        tel_ax.add_patch(FancyBboxPatch((0, 0), 1, 1,
                                        boxstyle="square,pad=0",
                                        linewidth=0.4,
                                        edgecolor=COLORS["border"],
                                        facecolor=bg_color, zorder=0))

        bar_frac2 = tv / BAR_MAX
        # background bar
        tel_ax.add_patch(FancyBboxPatch((bar_left, BAR_PAD),
                                        bar_avail, bar_h,
                                        boxstyle="square,pad=0",
                                        facecolor=COLORS["telefonia_bg"],
                                        edgecolor="none", zorder=1))
        # filled bar
        tel_ax.add_patch(FancyBboxPatch((bar_left, BAR_PAD),
                                        bar_avail * bar_frac2, bar_h,
                                        boxstyle="square,pad=0",
                                        facecolor=COLORS["telefonia_bar"],
                                        edgecolor="none", zorder=2))
        # value
        tel_ax.text(val_label_frac * 0.55, 0.5, f"{tv:.1f}",
                    ha="center", va="center", fontsize=8,
                    fontweight="bold", color=COLORS["text_dark"], zorder=3)

# ── Footer ────────────────────────────────────────────────────────────────────
footer_ax = fig.add_axes([TABLE_L, 0.01, TABLE_R - TABLE_L, TABLE_BOT - 0.015])
footer_ax.set_xlim(0, 1); footer_ax.set_ylim(0, 1); footer_ax.axis("off")

footer_lines = [
    ("bold",   "Fuente: ", "IFT con información de la Cuarta Encuesta 2023, Usuarios de Servicios de Telecomunicaciones (micro, pequeñas y medianas empresas)."),
    ("normal", "Para más información consultar: ", "https://www.ift.org.mx/usuarios-y-audiencias/encuestas-trimestrales."),
    ("bold",   "Nota: ",
     "La información presentada corresponde a los promedios obtenidos de cada una de las menciones por tamaño de empresa. La escala se tomó de 0 a 10, donde 0 es totalmente en desacuerdo\n"
     "y 10 es totalmente de acuerdo. El cálculo para el promedio se realizó con la suma de la multiplicación de las respuestas de las empresas por su respectivo factor de ponderación, dividida entre la suma\n"
     "total del citado factor; donde Ip = Es la importancia promedio que le dan las empresas a cada una de las preguntas, Wi es el factor de ponderación de cada empresa encuestada\n"
     "i, (Ii) es la respuesta de la empresa encuestada i, este cálculo excluye a las empresas con respuesta 'No sabe/No contestó'."),
]

y_positions = [0.82, 0.62, 0.38]
for i, (style, label, text) in enumerate(footer_lines):
    yp = y_positions[i]
    footer_ax.text(0.0, yp, label,
                   fontsize=6.5, fontweight="bold" if style == "bold" else "normal",
                   color=COLORS["text_dark"], va="top")
    # Estimate label width in axes fraction (rough)
    offset = len(label) * 0.006
    footer_ax.text(offset, yp, text,
                   fontsize=6.5, color=COLORS["text_mid"], va="top", wrap=True)

# ── Save ──────────────────────────────────────────────────────────────────────
import os
os.makedirs("output", exist_ok=True)
out_path = "output/figura_e5.png"
plt.savefig(out_path, dpi=180, bbox_inches="tight",
            facecolor="white", edgecolor="none")
plt.close()
print(f"Saved -> {out_path}")