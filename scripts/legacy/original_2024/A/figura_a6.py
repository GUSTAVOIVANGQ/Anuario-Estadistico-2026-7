#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figura A.6 - Ingresos, egresos y margen en el sector de telecomunicaciones.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import sys

# Ajusta la importación del logger según la estructura original
try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

def to_number(value: object) -> float:
    if pd.isna(value):
        return 0.0
    text = str(value).strip().replace(",", "")
    if text in {"", "-", "nan", "None"}:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0

def build_series(data_file: Path) -> pd.DataFrame:
    df = pd.read_csv(data_file, encoding="latin1", low_memory=False)
    df.columns = [c.strip() for c in df.columns]

    df = df[df["I_ANUAL_TRIM"].astype(str).str.strip().eq("Trimestral")].copy()
    df["INGRESOS_TOTAL_E"] = df["INGRESOS_TOTAL_E"].apply(to_number)

    df = df[(df["ANIO"] >= 2017) & (df["ANIO"] <= 2023)].copy()

    ingresos = (
        df.groupby(["ANIO", "TRIM"], as_index=False)["INGRESOS_TOTAL_E"]
        .sum()
        .sort_values(["ANIO", "TRIM"])
    )
    ingresos["ingresos_bn"] = ingresos["INGRESOS_TOTAL_E"] / 1_000_000_000

    # Margen leido de la figura original (2017T1 ... 2023T4).
    margen_pct = [
        20, 17, 15, 13,
        21, 20, 17, 17,
        25, 25, 26, 27,
        22, 15, 17, 17,
        17, 17, 29, 32,
        32, 30, 30, 30,
        31, 30, 33, 29,
    ]

    if len(ingresos) != len(margen_pct):
        raise ValueError(
            f"Esperados 28 trimestres, se encontraron {len(ingresos)} en el archivo."
        )

    ingresos["margen_pct"] = margen_pct
    ingresos["margen_bn"] = ingresos["ingresos_bn"] * ingresos["margen_pct"] / 100.0
    ingresos["egresos_bn"] = ingresos["ingresos_bn"] - ingresos["margen_bn"]

    return ingresos

def make_chart(df: pd.DataFrame, output_png: Path) -> None:
    # ── Colores estándar Guia_colores.md ──
    egresos_color = "#335a5c"   # teal oscuro
    margen_color  = "#86adae"   # teal claro (el verde exacto de las barras de A.1)
    text_color    = "#3c3c3b"   # gris institucional

    plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

    x = np.arange(len(df))
    width = 0.72  # Ajustado a 0.72 como en la referencia canónica A.1

    # Mismo tamaño de figura y fondo que A.1
    fig, ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#F8F8FA')

    bars_egresos = ax.bar(x, df["egresos_bn"], width=width, color=egresos_color, edgecolor='none', label="Egresos", zorder=2)
    bars_margen = ax.bar(
        x,
        df["margen_bn"],
        width=width,
        bottom=df["egresos_bn"],
        color=margen_color,
        edgecolor='none',
        label="Margen",
        zorder=2
    )

    # Etiquetas de porcentaje de margen y valor total de ingresos.
    for i, row in df.iterrows():
        y_margin_center = row["egresos_bn"] + row["margen_bn"] / 2
        # Chip del porcentaje igual a A.1
        ax.text(
            i,
            y_margin_center,
            f"{int(row['margen_pct'])}%",
            ha="center",
            va="center",
            fontsize=8,
            color=text_color,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8",
                      facecolor='white', edgecolor=egresos_color, linewidth=0.8),
            zorder=3
        )

        # Etiqueta de cantidad superior (cambiada de bold a normal)
        ax.text(
            i,
            row["ingresos_bn"] + 1.2,
            f"{row['ingresos_bn'] * 1000:,.0f}",
            rotation=90,
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="normal",
            color=text_color,
        )

    # Ajustamos el límite superior para dar espacio al texto
    ax.set_ylim(0, float(df["ingresos_bn"].max() * 1.25))

    # Eje X: trimestre en cada barra y año centrado por bloque de cuatro trimestres.
    trim_labels = ["I", "II", "III", "IV"] * 7
    ax.set_xticks(x)
    
    # Nivel superior: trimestres
    ax.set_xticklabels(trim_labels, fontsize=8, fontweight='normal', color=text_color)
    ax.tick_params(axis='x', length=3, pad=4, colors=text_color)

    # Nivel inferior: años centrados debajo de los trimestres
    years = sorted(df["ANIO"].unique())
    for idx, year in enumerate(years):
        center = idx * 4 + 1.5
        # Offset relativo al data Y para colocar los años debajo
        ax.text(
            center,
            -9,
            str(year),
            ha="center",
            va="top",
            fontsize=10,
            color=text_color,
            fontweight="bold",
            clip_on=False,
        )

    # Eje Y (Estilo A.1)
    ax.set_ylabel('Miles de millones de pesos', fontsize=11, fontweight='medium',
                  color=text_color, labelpad=15)
    ax.tick_params(axis='y', labelsize=9, colors=text_color)

    # Grid y bordes (Bordes ocultos arriba y derecha, grises abajo e izquierda)
    ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#7c7c7c')
    ax.spines['left'].set_color('#7c7c7c')

    # --- Títulos (Estilo Guia_colores.md como en A.1) ---
    # Cuadrado decorativo (#4a7d75)
    ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
                 xytext=(0, 30), textcoords='offset points',
                 va='center', ha='left', fontsize=2,
                 bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', 
                           facecolor='#4a7d75', edgecolor='none'))

    ax.annotate("Figura A.6.", xy=(0, 1), xycoords='axes fraction', 
                 xytext=(15, 30), textcoords='offset points',
                 fontsize=14, fontweight='bold', color=text_color, ha='left', va='center')

    ax.annotate(" Ingresos, egresos y margen en el sector de telecomunicaciones", 
                 xy=(0, 1), xycoords='axes fraction', 
                 xytext=(100, 30), textcoords='offset points',
                 fontsize=14, fontweight='medium', color=text_color, ha='left', va='center')

    # --- Leyenda centrada en la figura (Estilo A.1) ---
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center',
               bbox_to_anchor=(0.5, 0.08), ncol=2, fontsize=10,
               frameon=False, handlelength=2.5)

    # --- Notas al pie (Mismo esquema riguroso de A.1) ---
    font_size_notes = 8
    color_notes = '#3c3c3b'
    x_start = 0.08
    l_space = 1.5

    # Fuente
    y_fuente = 0.06
    ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction',
                 fontsize=font_size_notes, fontweight='bold', color=color_notes, ha='left', va='top')

    note1_content = 'IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de 2023.'
    ax.annotate(note1_content, xy=(x_start, y_fuente), xycoords='figure fraction',
                 xytext=(35, 0), textcoords='offset points',
                 fontsize=font_size_notes, fontweight='normal', color=color_notes, ha='left', va='top')

    # Notas
    y_notas = 0.042
    ax.annotate("Notas: ", xy=(x_start, y_notas), xycoords='figure fraction',
                 fontsize=font_size_notes, fontweight='bold', color=color_notes, ha='left', va='top')

    note2_content = 'Cifras en miles de millones de pesos (pesos corrientes de cada año).'
    ax.annotate(note2_content, xy=(x_start, y_notas), xycoords='figure fraction',
                 xytext=(32, 0), textcoords='offset points',
                 fontsize=font_size_notes, fontweight='normal', color=color_notes, ha='left', va='top', linespacing=l_space)

    # Ajuste de márgenes (Mismos valores que la referencia canónica A.1)
    fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
    
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=200, facecolor='white', edgecolor='none', bbox_inches="tight")
    plt.close(fig)

def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    data_file = repo_root / "datos" / "A.6" / "TD_INGRESOS_TELECOM_ITE_VA.csv"
    output_png = repo_root / "output" / "Figura_A6.png"

    try:
        series_df = build_series(data_file)
        make_chart(series_df, output_png)
        print("Figura generada:", output_png)
    except FileNotFoundError:
        print("Error: No se encontró el archivo de datos. Verifica la ruta.")

if __name__ == "__main__":
    main()