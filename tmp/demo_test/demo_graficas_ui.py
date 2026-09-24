#!/usr/bin/env python3
"""
demo_graficas_ui.py
===================
Genera ~10 gráficas representativas del Anuario Estadístico 2026
con datos SINTÉTICOS para evaluar y mejorar la UI sin datos reales.

Instala dependencias y ejecuta:
    pip install matplotlib numpy pandas pillow
    python demo_graficas_ui.py

Las imágenes se guardan en:  demo_output/
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paleta institucional (tomada de src/anuario2026/ui_2024.py)
# ---------------------------------------------------------------------------
TEXT       = "#3c3c3b"
AXES_BG    = "#F8F8FA"
AXIS_COLOR = "#7c7c7c"
GRID       = "#d1d1d1"
TEAL_DARK  = "#132b2d"
TEAL_MED   = "#335a5c"
TEAL_LIGHT = "#86adae"
TEAL_MID   = "#4c7d7e"
TEAL_PALE  = "#64a0a1"
MAP_GREEN  = ("#afafaf", "#737f7c", "#63918b", "#2d4f4b", "#012f2a")
ACCENT     = "#4a7d75"   # marcador de título
PURPLE     = "#b35aba"
ORANGE     = "#ed8945"
TEAL_B9    = ("#1e6284", "#ed8945", "#5844a0", "#99b554", "#8e244d", "#368491", "#728781")

OUT_DIR = Path("demo_output")
OUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers reutilizables
# ---------------------------------------------------------------------------

def _configure_fonts() -> str:
    """Intenta cargar Noto Sans desde assets/fonts; si no, usa DejaVu Sans."""
    font_dir = Path(__file__).parent / "assets" / "fonts" / "Noto_Sans"
    for name in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf"):
        path = font_dir / name
        if path.is_file():
            font_manager.fontManager.addfont(str(path))
    available = {item.name for item in font_manager.fontManager.ttflist}
    family = "Noto Sans" if "Noto Sans" in available else "DejaVu Sans"
    plt.rcParams.update({"font.family": family, "axes.unicode_minus": False})
    return family


def _title_marker(fig, label: str, title: str, ff: str) -> None:
    """Añade el marcador verde + título encima de la figura."""
    fig.add_artist(
        mpatches.FancyBboxPatch(
            (0.057, 0.916), 0.007, 0.018,
            transform=fig.transFigure,
            boxstyle="round,pad=0,rounding_size=0.002",
            facecolor=ACCENT, edgecolor="none",
        )
    )
    fig.text(0.071, 0.925, label, fontsize=14, fontweight="bold",
             color=TEXT, va="center", fontfamily=ff)
    fig.text(0.151, 0.925, title, fontsize=14, fontweight="medium",
             color=TEXT, va="center", fontfamily=ff)


def _footer(fig, source: str, note: str, ff: str) -> None:
    fig.text(0.055, 0.084, "Fuente:", fontsize=8.2, fontweight="bold",
             color=TEXT, va="top", fontfamily=ff)
    fig.text(0.094, 0.084, source, fontsize=8.2, color=TEXT, va="top", fontfamily=ff)
    fig.text(0.055, 0.061, "Notas:", fontsize=8.2, fontweight="bold",
             color=TEXT, va="top", fontfamily=ff)
    fig.text(0.091, 0.061, textwrap.fill(note, 210),
             fontsize=8.2, color=TEXT, va="top", linespacing=1.35, fontfamily=ff)


def _save(fig, name: str) -> None:
    path = OUT_DIR / name
    fig.savefig(path, dpi=150, facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"  ✓  {path}")


# ---------------------------------------------------------------------------
# Figura A.1 — PIB y participación TyR  (barras + línea, doble eje)
# ---------------------------------------------------------------------------
def demo_a1(ff: str) -> None:
    years   = list(range(2013, 2027))
    pib_q2  = [14500 + i * 280 + np.random.randint(-100, 100) for i in range(len(years))]
    pib_q4  = [p + 400 for p in pib_q2]
    pct_q2  = [1.05 + i * 0.025 + np.random.uniform(-0.01, 0.01) for i in range(len(years))]
    pct_q4  = [p + 0.02 for p in pct_q2]

    labels  = []
    pib     = []
    pct     = []
    for y, p2, p4, c2, c4 in zip(years, pib_q2, pib_q4, pct_q2, pct_q4):
        labels += [f"{y}-II", f"{y}-IV"]
        pib    += [p2, p4]
        pct    += [c2, c4]

    x = np.arange(len(labels), dtype=float)

    fig, ax1 = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    ax1.set_facecolor(AXES_BG)

    ax1.bar(x, pib, width=0.72, color=TEAL_LIGHT, edgecolor="none", zorder=2)
    ax1.set_ylabel("PIB Nacional en miles de millones de pesos",
                   fontsize=11, color=TEXT, labelpad=14)
    ax1.set_ylim(0, 30_000)
    ax1.yaxis.set_major_locator(mticker.MultipleLocator(5_000))
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax1.tick_params(axis="y", colors=TEXT, labelsize=9)
    ax1.grid(axis="y", color=GRID, linewidth=1, zorder=0)

    quarter_labels = [lbl.split("-")[1] for lbl in labels]
    ax1.set_xticks(x, quarter_labels, fontsize=8, color=TEXT)
    ax1.tick_params(axis="x", length=3, color=TEXT, pad=4)

    # etiquetas de año
    for i, year in enumerate(years):
        center = i * 2 + 0.5
        ax1.text(center, -1_700, str(year), ha="center", va="top",
                 fontsize=10, fontweight="bold", color=TEXT, clip_on=False)

    ax2 = ax1.twinx()
    pct_arr = np.array(pct)
    ax2.plot(x, pct_arr, color=TEAL_DARK, linewidth=1, marker="o",
             markersize=6, zorder=4)
    for xi, yi in zip(x, pct_arr):
        ax2.annotate(f"{yi:.1f}%", xy=(xi, yi), xytext=(0, 12),
                     textcoords="offset points", ha="center", va="bottom",
                     fontsize=8, fontweight="bold", color=TEXT,
                     bbox={"boxstyle": "round,pad=0.3,rounding_size=0.8",
                           "facecolor": "white", "edgecolor": TEAL_DARK,
                           "linewidth": 0.8},
                     zorder=5)
    ax2.set_ylabel("Porcentaje de participación de los subsectores de las TyR",
                   fontsize=11, color=TEXT, labelpad=16)
    ax2.set_ylim(0, 1.8)
    ax2.yaxis.set_major_locator(mticker.MultipleLocator(0.2))
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.1f}%"))
    ax2.tick_params(axis="y", colors=TEXT, labelsize=9)

    for ax in (ax1, ax2):
        ax.spines["top"].set_visible(False)
        for side in ("bottom", "left", "right"):
            ax.spines[side].set_color(AXIS_COLOR)
    ax1.set_xlim(-0.8, len(labels) - 0.2)

    _title_marker(fig, "Figura A.1.", "Producto Interno Bruto (PIB) y contribución del PIB de los subsectores TyR", ff)

    legend_bar  = mpatches.Patch(facecolor=TEAL_LIGHT, edgecolor="none", label="PIB nacional")
    legend_line = plt.Line2D([0], [0], color=TEAL_DARK, marker="o", markersize=5,
                             linewidth=1, label="Participación TyR")
    fig.legend(handles=[legend_bar, legend_line], loc="lower center",
               bbox_to_anchor=(0.5, 0.08), ncol=2, fontsize=10, frameon=False,
               labelcolor=TEXT)

    _footer(fig,
            "Elaborado por CRT con datos del INEGI (datos sintéticos para demo).",
            "PIB a precios constantes de 2018. La participación corresponde al sector 51 SCIAN 2023.",
            ff)
    fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
    _save(fig, "demo_A1_pib_tyr.png")


# ---------------------------------------------------------------------------
# Figura A.2 — Inversión extranjera directa  (barras agrupadas)
# ---------------------------------------------------------------------------
def demo_a2(ff: str) -> None:
    years   = list(range(2015, 2026))
    total   = [18 + i * 0.9 + np.random.uniform(-2, 2) for i in range(len(years))]
    telecom = [t * np.random.uniform(0.10, 0.18) for t in total]

    x = np.arange(len(years), dtype=float)
    w = 0.38

    fig, ax = plt.subplots(figsize=(14, 7.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(AXES_BG)

    ax.bar(x - w / 2, total,   width=w, color=TEAL_MED,   edgecolor="none", label="Total IED", zorder=2)
    ax.bar(x + w / 2, telecom, width=w, color=TEAL_LIGHT, edgecolor="none", label="IED TyR",   zorder=2)
    ax.set_xticks(x, [str(y) for y in years], fontsize=10, color=TEXT)
    ax.tick_params(axis="x", length=0, color=TEXT)
    ax.tick_params(axis="y", colors=TEXT, labelsize=9)
    ax.set_ylabel("Miles de millones de pesos", fontsize=11, color=TEXT, labelpad=12)
    ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color(AXIS_COLOR)

    _title_marker(fig, "Figura A.2.", "Inversión Extranjera Directa (IED) — demo", ff)
    fig.legend(loc="lower center", bbox_to_anchor=(0.5, 0.06),
               ncol=2, fontsize=10, frameon=False, labelcolor=TEXT)
    _footer(fig, "Elaborado por CRT con datos sintéticos para demo.",
            "Datos a precios corrientes.", ff)
    fig.subplots_adjust(left=0.09, right=0.96, top=0.85, bottom=0.20)
    _save(fig, "demo_A2_ied.png")


# ---------------------------------------------------------------------------
# Figura B.9 — Usuarios de Internet móvil por operador  (barras horizontales)
# ---------------------------------------------------------------------------
def demo_b9(ff: str) -> None:
    operadores = ["Telcel", "AT&T", "Movistar", "Bait", "Altán", "Unefon", "Otros"]
    shares     = [52.3, 21.8, 14.1, 6.4, 3.2, 1.5, 0.7]
    colors     = list(TEAL_B9[:len(operadores)])

    fig, ax = plt.subplots(figsize=(13, 6.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(AXES_BG)

    y = np.arange(len(operadores), dtype=float)[::-1]
    ax.barh(y, shares, height=0.6, color=colors, edgecolor="none", zorder=2)

    for yi, s in zip(y, shares):
        ax.text(s + 0.5, yi, f"{s:.1f}%", va="center", fontsize=9,
                color=TEXT, fontweight="bold")

    ax.set_yticks(y, operadores, fontsize=11, color=TEXT)
    ax.set_xlabel("Porcentaje (%)", fontsize=11, color=TEXT)
    ax.set_xlim(0, 62)
    ax.tick_params(axis="x", colors=TEXT, labelsize=9)
    ax.grid(axis="x", color=GRID, linewidth=1, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color(AXIS_COLOR)

    _title_marker(fig, "Figura B.9.", "Participación de mercado en usuarios de Internet móvil — demo", ff)
    _footer(fig, "Elaborado por CRT con datos sintéticos para demo.",
            "Participación a nivel de SIMs activas al cierre del periodo.", ff)
    fig.subplots_adjust(left=0.15, right=0.92, top=0.85, bottom=0.18)
    _save(fig, "demo_B9_internet_movil.png")


# ---------------------------------------------------------------------------
# Figura B.16 — Líneas de telefonía fija  (línea de tiempo con área)
# ---------------------------------------------------------------------------
def demo_b16(ff: str) -> None:
    years  = list(range(2010, 2026))
    groups = {
        "Residencial":   [20000 - i * 300 + np.random.randint(-200, 200) for i in range(len(years))],
        "Empresarial":   [5800  - i * 50  + np.random.randint(-100, 100) for i in range(len(years))],
        "Gobierno":      [400   - i * 5   + np.random.randint(-20, 20)   for i in range(len(years))],
        "Caseta pública":[1200  - i * 60  + np.random.randint(-50, 50)   for i in range(len(years))],
        "Larga distancia":[800  - i * 30  + np.random.randint(-30, 30)   for i in range(len(years))],
    }
    palette = ("#132b2d", "#3b6667", "#64a0a1", "#86adae", "#afafaf")

    fig, ax = plt.subplots(figsize=(14, 7.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(AXES_BG)

    bottom = np.zeros(len(years))
    x      = np.array(years, dtype=float)
    for (label, vals), color in zip(groups.items(), palette):
        arr = np.array(vals, dtype=float)
        ax.fill_between(x, bottom, bottom + arr, alpha=0.9, color=color, label=label, zorder=2)
        bottom += arr

    ax.set_xlim(years[0], years[-1])
    ax.set_ylim(0)
    ax.set_ylabel("Miles de líneas", fontsize=11, color=TEXT, labelpad=12)
    ax.set_xlabel("Año", fontsize=11, color=TEXT, labelpad=10)
    ax.tick_params(axis="both", colors=TEXT, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)
    for sp in ax.spines.values():
        sp.set_color(AXIS_COLOR)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    _title_marker(fig, "Figura B.16.", "Líneas de telefonía fija por segmento — demo", ff)
    fig.legend(loc="lower center", bbox_to_anchor=(0.5, 0.06), ncol=5,
               fontsize=9, frameon=False, labelcolor=TEXT)
    _footer(fig, "Elaborado por CRT con datos sintéticos para demo.",
            "Líneas activas al cierre de cada periodo anual.", ff)
    fig.subplots_adjust(left=0.10, right=0.96, top=0.85, bottom=0.22)
    _save(fig, "demo_B16_telefonia_fija.png")


# ---------------------------------------------------------------------------
# Figura C.5 — Penetración de banda ancha por entidad (mapa de calor simplificado)
# ---------------------------------------------------------------------------
def demo_c5(ff: str) -> None:
    entidades = [
        "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
        "Chiapas", "Chihuahua", "Ciudad de México", "Coahuila",
        "Colima", "Durango", "Guanajuato", "Guerrero",
        "Hidalgo", "Jalisco", "México", "Michoacán",
        "Morelos", "Nayarit", "Nuevo León", "Oaxaca",
        "Puebla", "Querétaro", "Quintana Roo", "San Luis Potosí",
        "Sinaloa", "Sonora", "Tabasco", "Tamaulipas",
        "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas",
    ]
    rng    = np.random.default_rng(42)
    values = rng.uniform(25, 85, size=len(entidades))
    sorted_idx = np.argsort(values)[::-1]
    ent_sorted = [entidades[i] for i in sorted_idx]
    val_sorted = values[sorted_idx]

    palette_cont = ("#86adae", "#64a0a1", "#5c9596", "#4c7d7e", "#3b6667", "#132b2d")

    def _color_for(v: float) -> str:
        idx = min(int((v - 25) / 10), len(palette_cont) - 1)
        return palette_cont[idx]

    colors = [_color_for(v) for v in val_sorted]

    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(AXES_BG)

    y = np.arange(len(ent_sorted), dtype=float)
    ax.barh(y, val_sorted, height=0.7, color=colors, edgecolor="none", zorder=2)
    for yi, v in zip(y, val_sorted):
        ax.text(v + 0.5, yi, f"{v:.1f}%", va="center", fontsize=8, color=TEXT)
    ax.set_yticks(y, ent_sorted, fontsize=8, color=TEXT)
    ax.set_xlabel("Penetración (%)", fontsize=10, color=TEXT)
    ax.set_xlim(0, 95)
    ax.tick_params(axis="x", colors=TEXT, labelsize=9)
    ax.grid(axis="x", color=GRID, linewidth=1, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color(AXIS_COLOR)

    _title_marker(fig, "Figura C.5.", "Penetración de banda ancha fija por entidad federativa — demo", ff)
    _footer(fig, "Elaborado por CRT con datos sintéticos para demo.",
            "Líneas de BA fija por cada 100 hogares.", ff)
    fig.subplots_adjust(left=0.28, right=0.96, top=0.88, bottom=0.12)
    _save(fig, "demo_C5_ba_entidad.png")


# ---------------------------------------------------------------------------
# Figura D.1 — Ingresos del sector  (barras apiladas multi-categoría)
# ---------------------------------------------------------------------------
def demo_d1(ff: str) -> None:
    years    = list(range(2016, 2026))
    cats     = ["Telefonía fija", "Telefonía móvil", "Internet fijo",
                "Internet móvil", "TV de paga"]
    palette  = ("#006157", "#b35aba", "#ed8945", "#368491", "#8e244d")
    rng      = np.random.default_rng(7)
    data     = {c: rng.uniform(30, 120, size=len(years)) for c in cats}

    x      = np.arange(len(years), dtype=float)
    bottom = np.zeros(len(years))

    fig, ax = plt.subplots(figsize=(14, 7.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(AXES_BG)

    for cat, color in zip(cats, palette):
        vals = np.array(data[cat])
        ax.bar(x, vals, width=0.7, bottom=bottom, color=color,
               edgecolor="none", label=cat, zorder=2)
        bottom += vals

    ax.set_xticks(x, [str(y) for y in years], fontsize=10, color=TEXT)
    ax.tick_params(axis="both", colors=TEXT, labelsize=9)
    ax.set_ylabel("Miles de millones de pesos", fontsize=11, color=TEXT, labelpad=12)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color(AXIS_COLOR)

    _title_marker(fig, "Figura D.1.", "Ingresos del sector de telecomunicaciones y radiodifusión — demo", ff)
    fig.legend(loc="lower center", bbox_to_anchor=(0.5, 0.06), ncol=5,
               fontsize=9, frameon=False, labelcolor=TEXT)
    _footer(fig, "Elaborado por CRT con datos sintéticos para demo.",
            "Ingresos a precios corrientes.", ff)
    fig.subplots_adjust(left=0.10, right=0.96, top=0.85, bottom=0.22)
    _save(fig, "demo_D1_ingresos.png")


# ---------------------------------------------------------------------------
# Figura E.3 — Brecha digital (puntos con intervalo de confianza)
# ---------------------------------------------------------------------------
def demo_e3(ff: str) -> None:
    grupos  = ["Rural", "Urbano", "Hombres", "Mujeres",
               "6-11 años", "12-17 años", "18-24 años", "25-44 años",
               "45-54 años", "55+ años"]
    rng     = np.random.default_rng(99)
    medias  = rng.uniform(20, 85, size=len(grupos))
    errores = rng.uniform(1, 4, size=len(grupos))

    palette2 = ("#afafaf", "#86adae")
    colores   = [palette2[i % 2] for i in range(len(grupos))]

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(AXES_BG)

    y = np.arange(len(grupos), dtype=float)[::-1]
    ax.errorbar(medias, y, xerr=errores, fmt="none", ecolor=TEAL_MED,
                elinewidth=1.5, capsize=4, zorder=2)
    ax.scatter(medias, y, s=60, color=colores, edgecolors=TEAL_MED,
               linewidths=0.8, zorder=3)
    for yi, m in zip(y, medias):
        ax.text(m + errores[int(len(grupos) - 1 - yi)] + 0.5, yi,
                f"{m:.1f}%", va="center", fontsize=9, color=TEXT)

    ax.set_yticks(y, grupos, fontsize=10, color=TEXT)
    ax.set_xlabel("Usuarios de Internet (%)", fontsize=11, color=TEXT)
    ax.set_xlim(0, 100)
    ax.tick_params(axis="x", colors=TEXT, labelsize=9)
    ax.grid(axis="x", color=GRID, linewidth=1, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color(AXIS_COLOR)

    _title_marker(fig, "Figura E.3.", "Brecha digital por grupos de población — demo", ff)
    _footer(fig, "Elaborado por CRT con datos sintéticos para demo.",
            "Porcentaje de usuarios de Internet respecto al grupo.", ff)
    fig.subplots_adjust(left=0.22, right=0.92, top=0.85, bottom=0.18)
    _save(fig, "demo_E3_brecha_digital.png")


# ---------------------------------------------------------------------------
# Figura F.2 — Cobertura de red móvil  (líneas múltiples)
# ---------------------------------------------------------------------------
def demo_f2(ff: str) -> None:
    years = list(range(2015, 2026))
    techs = {"2G": 82, "3G": 55, "4G/LTE": 20, "5G": 0}
    final = {"2G": 68, "3G": 71, "4G/LTE": 79, "5G": 35}

    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(AXES_BG)

    palette_f2 = ("#64a0a1", "#132b2d")
    colors_map = {
        "2G": "#afafaf", "3G": "#64a0a1", "4G/LTE": "#132b2d", "5G": "#b35aba"
    }
    rng = np.random.default_rng(11)
    for tech, (start, end) in zip(techs.keys(), [(v, final[k]) for k, v in techs.items()]):
        vals = np.linspace(start, end, len(years)) + rng.uniform(-1, 1, len(years))
        vals = np.clip(vals, 0, 100)
        ax.plot(years, vals, marker="o", markersize=5, linewidth=2,
                color=colors_map[tech], label=tech, zorder=3)

    ax.set_xlim(years[0], years[-1])
    ax.set_ylim(0, 105)
    ax.set_ylabel("% de cobertura poblacional", fontsize=11, color=TEXT, labelpad=12)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.tick_params(axis="both", colors=TEXT, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color(AXIS_COLOR)

    _title_marker(fig, "Figura F.2.", "Cobertura de red móvil por tecnología — demo", ff)
    ax.legend(loc="lower right", fontsize=10, frameon=False, labelcolor=TEXT)
    _footer(fig, "Elaborado por CRT con datos sintéticos para demo.",
            "Cobertura definida como % de la población en zonas cubiertas por la red.", ff)
    fig.subplots_adjust(left=0.10, right=0.96, top=0.85, bottom=0.18)
    _save(fig, "demo_F2_cobertura_movil.png")


# ---------------------------------------------------------------------------
# Figura G.1 — Tarifa de datos móviles vs. ingreso  (scatter con línea de tendencia)
# ---------------------------------------------------------------------------
def demo_g1(ff: str) -> None:
    rng   = np.random.default_rng(21)
    n     = 35
    pib   = rng.uniform(5_000, 50_000, n)     # USD PPA per cápita
    tarif = 8_000 / pib * np.exp(rng.uniform(-0.3, 0.3, n))

    # línea de tendencia
    coef  = np.polyfit(pib, tarif, 1)
    trend = np.poly1d(coef)
    x_fit = np.linspace(pib.min(), pib.max(), 200)

    fig, ax = plt.subplots(figsize=(13, 7.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(AXES_BG)

    ax.scatter(pib, tarif, s=60, color=TEAL_MED, edgecolors=TEAL_DARK,
               linewidths=0.8, alpha=0.85, zorder=3, label="País")
    ax.plot(x_fit, trend(x_fit), color=TEAL_DARK, linewidth=1.5,
            linestyle="--", label="Tendencia", zorder=2)

    ax.set_xlabel("PIB per cápita (USD PPA)", fontsize=11, color=TEXT, labelpad=10)
    ax.set_ylabel("Tarifa por GB (USD)", fontsize=11, color=TEXT, labelpad=12)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.tick_params(axis="both", colors=TEXT, labelsize=9)
    ax.grid(color=GRID, linewidth=1, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color(AXIS_COLOR)

    _title_marker(fig, "Figura G.1.", "Tarifa de datos móviles vs. ingreso per cápita — demo", ff)
    ax.legend(loc="upper right", fontsize=10, frameon=False, labelcolor=TEXT)
    _footer(fig, "Elaborado por CRT con datos sintéticos para demo.",
            "Tarifa mínima de plan mensual con 1 GB, a precios corrientes PPA.", ff)
    fig.subplots_adjust(left=0.10, right=0.96, top=0.85, bottom=0.18)
    _save(fig, "demo_G1_tarifa_pib.png")


# ---------------------------------------------------------------------------
# Panel resumen de paleta institucional
# ---------------------------------------------------------------------------
def demo_paleta(ff: str) -> None:
    colores = [
        ("#132b2d", "TEAL_DARK\n#132b2d"),
        ("#234244", "TEAL\n#234244"),
        ("#335a5c", "TEAL_MED\n#335a5c"),
        ("#3b6667", "#3b6667"),
        ("#4c7d7e", "TEAL_MID\n#4c7d7e"),
        ("#5c9596", "#5c9596"),
        ("#64a0a1", "TEAL_PALE\n#64a0a1"),
        ("#86adae", "TEAL_LIGHT\n#86adae"),
        ("#afafaf", "GRAY\n#afafaf"),
        ("#4a7d75", "ACCENT\n#4a7d75"),
        ("#b35aba", "PURPLE\n#b35aba"),
        ("#ed8945", "ORANGE\n#ed8945"),
        ("#006157", "GREEN\n#006157"),
        ("#8e244d", "WINE\n#8e244d"),
        ("#1e6284", "BLUE\n#1e6284"),
        ("#F8F8FA", "BG\n#F8F8FA"),
    ]

    n  = len(colores)
    nc = 8
    nr = (n + nc - 1) // nc

    fig, axes = plt.subplots(nr, nc, figsize=(16, 2.8 * nr))
    fig.patch.set_facecolor("white")
    axes_flat = axes.flat if nr > 1 else [axes] if nc == 1 else list(axes)

    for ax, (color, label) in zip(axes_flat, colores):
        ax.set_facecolor(color)
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        text_color = "white" if (r * 0.299 + g * 0.587 + b * 0.114) < 128 else TEXT
        ax.text(0.5, 0.5, label, transform=ax.transAxes, ha="center", va="center",
                fontsize=9, color=text_color, fontfamily=ff)
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)

    for ax in list(axes_flat)[n:]:
        ax.set_visible(False)

    fig.suptitle("Paleta institucional — Anuario Estadístico 2026",
                 fontsize=14, fontweight="bold", color=TEXT, y=1.02)
    fig.tight_layout()
    _save(fig, "demo_paleta_institucional.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("Anuario Estadístico 2026 — Demo de gráficas UI")
    print(f"Salida en:  {OUT_DIR.resolve()}")
    print()

    ff = _configure_fonts()
    print(f"Fuente: {ff}")
    print()

    demo_paleta(ff)
    demo_a1(ff)
    demo_a2(ff)
    demo_b9(ff)
    demo_b16(ff)
    demo_c5(ff)
    demo_d1(ff)
    demo_e3(ff)
    demo_f2(ff)
    demo_g1(ff)

    print()
    print(f"✅ {len(list(OUT_DIR.glob('*.png')))} imágenes generadas en {OUT_DIR.resolve()}")
    print()
    print("Para ver las imágenes en Windows:")
    print("    explorer demo_output")


if __name__ == "__main__":
    main()
