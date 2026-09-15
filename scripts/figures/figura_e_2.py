"""Figura E.2: principales hallazgos del estudio cualitativo sobre IA y ChatGPT."""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import patches
from matplotlib.lines import Line2D


FIGURE_ID = "E.2"
SOURCE_ID = "ift_estudio_ia_chatgpt_2023"
SOURCE_YEAR = 2023
SOURCE_URL = (
    "https://www.ift.org.mx/usuarios-y-audiencias/"
    "estudio-cualitativo-conocimiento-y-percepcion-sobre-la-inteligencia-artificial-ia-y-chatgpt-2023"
)

BG = "#FBFBF7"
CORAL = "#F05A5D"
BLUE = "#2C789F"
NAVY = "#47477E"
TEXT = "#40405E"
WHITE = "#FFFFFF"
MINT = "#B9E1E2"
AQUA = "#9FD2D4"
PEACH = "#F4A38D"
SHADOW = "#D8D8D3"

FINDINGS = [
    ("Inteligencia Artificial (IA)", 1, "Es accesible, amigable y aporta beneficios en áreas laborales, escolares, de salud y del hogar."),
    ("Inteligencia Artificial (IA)", 2, "Los programas se reconocen en categorías de texto, creación de presentaciones o contenido, y aplicaciones especializadas."),
    ("Inteligencia Artificial (IA)", 3, "Las principales preocupaciones son la privacidad, los ciberdelitos y la necesidad de regulación."),
    ("ChatGPT", 1, "Es el programa de Inteligencia Artificial más conocido y utilizado por las personas participantes."),
    ("ChatGPT", 2, "Destaca por resolver dudas y redactar información concreta, organizada y sintetizada con rapidez."),
    ("ChatGPT", 3, "Resulta atractivo para consultas laborales, escolares, de investigación y de la vida cotidiana."),
    ("ChatGPT", 4, "Entre las desventajas se mencionan respuestas incompletas o imprecisas, hackeo, privacidad, fraude y ciberdelitos."),
]


def build_findings() -> pd.DataFrame:
    return pd.DataFrame(FINDINGS, columns=["tema", "orden", "hallazgo"]).assign(
        anio_estudio=SOURCE_YEAR,
        tipo_resultado="cualitativo",
    )


def _font(root: Path) -> str:
    for name in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf"):
        path = root / "assets" / "fonts" / "Noto_Sans" / name
        if path.is_file():
            fm.fontManager.addfont(path)
    return "Noto Sans" if any(item.name == "Noto Sans" for item in fm.fontManager.ttflist) else "DejaVu Sans"


def _wrap(value: str, width: int) -> str:
    return "\n".join(textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False))


def _rounded(ax, x, y, width, height, color, radius=.18, zorder=2, edge="none", linewidth=0):
    item = patches.FancyBboxPatch(
        (x, y), width, height,
        boxstyle=f"round,pad=.02,rounding_size={radius}",
        facecolor=color, edgecolor=edge, linewidth=linewidth, zorder=zorder,
    )
    ax.add_patch(item)
    return item


def _bubble(ax, x, y, width, height, value, *, font_size=8.8, wrap=43):
    _rounded(ax, x + .035, y - .045, width, height, "#DDE2E4", zorder=3)
    _rounded(ax, x, y, width, height, WHITE, zorder=4)
    center = y + height * .52
    ax.add_patch(patches.Polygon(
        [(x, center + .13), (x - .17, center), (x, center - .13)],
        closed=True, facecolor=WHITE, edgecolor="none", zorder=4,
    ))
    ax.text(x + .2, y + height / 2, _wrap(value, wrap), ha="left", va="center",
            fontsize=font_size, color=TEXT, linespacing=1.24, zorder=5)


def _ai_icon(ax, cx, cy, scale=1.0):
    ax.add_patch(patches.Circle((cx - .2 * scale, cy + .28 * scale), .53 * scale, fc=AQUA, ec="none", zorder=5))
    ax.add_patch(patches.Circle((cx + .18 * scale, cy + .16 * scale), .44 * scale, fc=PEACH, ec="none", zorder=6))
    ax.add_patch(patches.Circle((cx + .4 * scale, cy + .16 * scale), .25 * scale, fc=WHITE, ec="none", zorder=7))
    ax.add_patch(patches.Polygon([
        (cx - .54 * scale, cy - .08 * scale), (cx - .7 * scale, cy - .74 * scale),
        (cx + .2 * scale, cy - .74 * scale), (cx + .15 * scale, cy - .06 * scale),
    ], closed=True, fc=NAVY, ec="none", zorder=5))
    ax.add_patch(patches.Circle((cx - .18 * scale, cy + .18 * scale), .16 * scale, fc=WHITE, ec="none", zorder=8))
    ax.add_patch(patches.Circle((cx - .18 * scale, cy + .18 * scale), .09 * scale, fc=NAVY, ec="none", zorder=9))
    ax.add_patch(patches.Circle((cx - .17 * scale, cy + .88 * scale), .18 * scale, fc=WHITE, ec="none", zorder=8))
    ax.text(cx - .17 * scale, cy + .88 * scale, "✦", color=BLUE, fontsize=15 * scale,
            ha="center", va="center", zorder=9)
    _rounded(ax, cx - 1.15 * scale, cy + .25 * scale, .58 * scale, .22 * scale, MINT, radius=.05, zorder=7)
    ax.text(cx - .86 * scale, cy + .36 * scale, "</>", color=WHITE, fontsize=8 * scale,
            ha="center", va="center", fontweight="bold", zorder=9)
    _rounded(ax, cx + .5 * scale, cy - .55 * scale, .58 * scale, .3 * scale, NAVY, radius=.03, zorder=7)


def _chat_icon(ax, cx, cy, scale=1.0):
    _rounded(ax, cx - .78 * scale, cy + .25 * scale, 1.55 * scale, .92 * scale, WHITE, radius=.08, zorder=6)
    ax.add_patch(patches.Rectangle((cx - .78 * scale, cy + 1 * scale), 1.55 * scale, .17 * scale,
                                   fc=NAVY, ec="none", zorder=7))
    for dx, color in [(-.61, CORAL), (-.47, MINT), (-.33, WHITE)]:
        ax.add_patch(patches.Circle((cx + dx * scale, cy + 1.085 * scale), .035 * scale,
                                    fc=color, ec="none", zorder=8))
    ax.add_line(Line2D([cx - .46 * scale, cx - .1 * scale], [cy + .63 * scale, cy + .63 * scale],
                       color=NAVY, lw=1.5 * scale, zorder=8))
    ax.add_patch(patches.Circle((cx + .42 * scale, cy + .7 * scale), .23 * scale, fc=NAVY, ec="none", zorder=8))
    ax.add_patch(patches.Polygon([
        (cx - .05 * scale, cy + .02 * scale), (cx + .55 * scale, cy + .02 * scale),
        (cx + .55 * scale, cy + .13 * scale), (cx + .76 * scale, cy - .04 * scale),
        (cx + .55 * scale, cy - .21 * scale), (cx + .55 * scale, cy - .1 * scale),
        (cx - .05 * scale, cy - .1 * scale),
    ], closed=True, fc=CORAL, ec="none", zorder=7))
    for x, y, radius in [(-.3, -.98, .3), (.06, -.92, .38), (.44, -1, .28)]:
        ax.add_patch(patches.Circle((cx + x * scale, cy + y * scale), radius * scale, fc=MINT, ec="none", zorder=6))
    ax.add_patch(patches.Rectangle((cx - .6 * scale, cy - 1.22 * scale), 1.26 * scale, .25 * scale,
                                   fc=MINT, ec="none", zorder=6))
    ax.add_patch(patches.Circle((cx + .05 * scale, cy - .96 * scale), .18 * scale, fc=WHITE, ec="none", zorder=7))
    ax.text(cx + .05 * scale, cy - .96 * scale, "✦", color=AQUA, fontsize=15 * scale,
            ha="center", va="center", zorder=8)


def _plot(output: Path, root: Path) -> None:
    plt.rcParams.update({"font.family": _font(root), "font.size": 10, "axes.unicode_minus": False})
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 17)
    ax.set_ylim(0, 9.2)
    ax.axis("off")
    _rounded(ax, .35, .3, 16.3, 8.55, BG, radius=.24, zorder=1)
    _rounded(ax, .68, 8.37, .09, .13, CORAL, radius=.025, zorder=4)
    ax.text(.86, 8.44, "Figura E.2.", fontsize=14.2, color=NAVY, fontweight="bold", va="center")
    ax.text(2.62, 8.44, "Principales hallazgos de la Inteligencia Artificial (IA) y ChatGPT",
            fontsize=14.2, color=NAVY, va="center")

    left_x, panel_y, panel_w, panel_h = .76, 1.55, 7.64, 6.2
    right_x = 8.6
    _rounded(ax, left_x, panel_y, panel_w, panel_h, CORAL, radius=.22)
    _rounded(ax, right_x, panel_y, panel_w, panel_h, BLUE, radius=.22)
    _ai_icon(ax, left_x + 1.95, panel_y + 3.62, 1.05)
    ax.text(left_x + 1.95, panel_y + 1.95, "Inteligencia\nArtificial (IA)", ha="center", va="top",
            color=WHITE, fontsize=14.3, fontweight="bold", linespacing=1.22, zorder=9)
    _chat_icon(ax, right_x + 1.95, panel_y + 4.13, 1.05)
    ax.text(right_x + 1.95, panel_y + 1.9, "ChatGPT", ha="center", va="top",
            color=WHITE, fontsize=14.5, fontweight="bold", zorder=9)

    left = [item[2] for item in FINDINGS if item[0].startswith("Inteligencia")]
    right = [item[2] for item in FINDINGS if item[0] == "ChatGPT"]
    _bubble(ax, left_x + 3.6, panel_y + 4.83, 3.73, 1.08, "› " + left[0], wrap=43)
    _bubble(ax, left_x + 3.6, panel_y + 2.45, 3.73, 2.12, "› " + left[1], font_size=8.65, wrap=43)
    _bubble(ax, left_x + 3.6, panel_y + .42, 3.73, 1.72, "› " + left[2], font_size=8.7, wrap=43)
    _bubble(ax, right_x + 3.58, panel_y + 5.15, 3.78, .79, "› " + right[0], wrap=43)
    _bubble(ax, right_x + 3.58, panel_y + 3.62, 3.78, 1.33, "› " + right[1], font_size=8.7, wrap=43)
    _bubble(ax, right_x + 3.58, panel_y + 2.12, 3.78, 1.29, "› " + right[2], font_size=8.65, wrap=43)
    _bubble(ax, right_x + 3.58, panel_y + .19, 3.78, 1.7, "› " + right[3], font_size=8.55, wrap=43)

    ax.text(.7, 1.04, "Fuente:", fontsize=8, color=NAVY, fontweight="bold", va="top")
    ax.text(1.42, 1.04, "IFT, Estudio Cualitativo Conocimiento y Percepción sobre la Inteligencia Artificial (IA) y ChatGPT 2023.",
            fontsize=8, color=TEXT, va="top")
    ax.text(.7, .78, "Nota:", fontsize=8, color=NAVY, fontweight="bold", va="top")
    ax.text(1.2, .78, "Resultados cualitativos de grupos de enfoque; no representan estimaciones poblacionales.",
            fontsize=8, color=TEXT, va="top")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  E.2 | Descarga o reutilización del estudio cualitativo oficial")
    raw = context.acquire_source(SOURCE_ID)
    if raw.read_bytes()[:4] != b"%PDF":
        raise ValueError("El archivo del estudio E.2 no es un PDF válido")
    context.record_source_period(SOURCE_ID, str(SOURCE_YEAR), "ULTIMO_ESTUDIO_COMPATIBLE")
    data = build_findings()
    context.write_data_used(data)
    for row in data.itertuples(index=False):
        context.record_calculation(
            f"hallazgo_{row.tema.lower().replace(' ', '_')}_{row.orden}",
            "clasificación temática de hallazgo cualitativo publicado",
            {"anio_estudio": row.anio_estudio, "tema": row.tema, "orden": row.orden},
            row.hallazgo,
            "hallazgo cualitativo",
        )
    text_path = context.render_text("f_digital.md.j2", {
        "resumen": "El estudio cualitativo identifica beneficios de accesibilidad y rapidez, junto con preocupaciones sobre precisión, privacidad y ciberdelitos."
    })
    print(data.to_string(index=False))
    print("  E.2 | Generación de gráfica PNG")
    _plot(context.expected_figure_path, context.project_root)
    return {"figure_path": str(context.expected_figure_path), "text_path": str(text_path),
            "source_latest_period": str(SOURCE_YEAR), "rows_used": len(data)}


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "src"))
    from anuario2026.pipeline import run_pipeline

    run_pipeline(root, only=FIGURE_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
