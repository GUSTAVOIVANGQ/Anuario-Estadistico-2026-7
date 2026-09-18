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

BG = "#F8F8FA"
PANEL_IA = "#1A4043"
PANEL_CHATGPT = "#2D7B8A"
TEXT = "#3C3C3B"
WHITE = "#FFFFFF"
MINT = "#6CACAD"
ACCENT = "#4A7D75"
LIGHT_TEAL = "#DCEFF0"
SHADOW = "#CDD5D8"
TITLE_MARKER = "#4A7D75"
BUBBLE_BORDER = "#C8D2D5"
ICON_LINE = "#EAF3F2"

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


def _bubble(ax, x, y, width, height, value, *, font_size=8.9, wrap=52):
    _rounded(ax, x + .04, y - .05, width, height, SHADOW, radius=.14, zorder=3)
    _rounded(ax, x, y, width, height, WHITE, radius=.14, zorder=4, edge=BUBBLE_BORDER, linewidth=.8)
    center = y + height * .52
    ax.add_patch(patches.Polygon(
        [(x, center + .11), (x - .14, center), (x, center - .11)],
        closed=True, facecolor=WHITE, edgecolor=BUBBLE_BORDER, linewidth=.8, zorder=4,
    ))
    ax.text(
        x + .18, y + height / 2, _wrap(value, wrap),
        ha="left", va="center", fontsize=font_size, color=TEXT,
        linespacing=1.38, zorder=5,
    )


def _icon_badge(ax, x, y, w, h, label, panel_color):
    _rounded(ax, x, y, w, h, WHITE, radius=.18, zorder=6)
    _rounded(ax, x + .06, y + .06, w - .12, h - .12, panel_color, radius=.16, zorder=7)
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", color=WHITE,
            fontsize=14.5, fontweight="bold", zorder=8)


def _ai_icon(ax, cx, cy, scale=1.0):
    body = 1.12 * scale
    # chip body
    _rounded(ax, cx - body / 2, cy - body / 2, body, body, LIGHT_TEAL, radius=.16, zorder=6)
    _rounded(ax, cx - body / 2 + .08 * scale, cy - body / 2 + .08 * scale,
             body - .16 * scale, body - .16 * scale, WHITE, radius=.13, zorder=7)
    # pins
    pin_len = .18 * scale
    pin_w = .08 * scale
    offsets = [-.28, 0, .28]
    for off in offsets:
        ax.add_patch(patches.Rectangle((cx - .04 * scale + off * scale, cy + body / 2), pin_w, pin_len,
                                       fc=ICON_LINE, ec="none", zorder=5))
        ax.add_patch(patches.Rectangle((cx - .04 * scale + off * scale, cy - body / 2 - pin_len), pin_w, pin_len,
                                       fc=ICON_LINE, ec="none", zorder=5))
        ax.add_patch(patches.Rectangle((cx + body / 2, cy - .04 * scale + off * scale), pin_len, pin_w,
                                       fc=ICON_LINE, ec="none", zorder=5))
        ax.add_patch(patches.Rectangle((cx - body / 2 - pin_len, cy - .04 * scale + off * scale), pin_len, pin_w,
                                       fc=ICON_LINE, ec="none", zorder=5))
    # simple network / brain form
    nodes = [(-.2, .18), (.22, .2), (-.1, -.18), (.24, -.12), (.02, .02)]
    lines = [(0, 4), (1, 4), (2, 4), (3, 4), (0, 2), (1, 3)]
    for i, j in lines:
        (x1, y1), (x2, y2) = nodes[i], nodes[j]
        ax.add_line(Line2D([cx + x1 * scale, cx + x2 * scale], [cy + y1 * scale, cy + y2 * scale],
                           color=ACCENT, lw=2, zorder=8))
    for x0, y0 in nodes:
        ax.add_patch(patches.Circle((cx + x0 * scale, cy + y0 * scale), .07 * scale, fc=PANEL_IA, ec="none", zorder=9))
    _icon_badge(ax, cx - .36 * scale, cy - .92 * scale, .72 * scale, .34 * scale, "IA", ACCENT)


def _chat_icon(ax, cx, cy, scale=1.0):
    # app window
    _rounded(ax, cx - .78 * scale, cy + .04 * scale, 1.56 * scale, .98 * scale, WHITE, radius=.1, zorder=6)
    ax.add_patch(patches.Rectangle((cx - .78 * scale, cy + .79 * scale), 1.56 * scale, .23 * scale,
                                   fc=TEXT, ec="none", zorder=7))
    for dx, color in [(-.58, "#F48D7E"), (-.44, MINT), (-.30, LIGHT_TEAL)]:
        ax.add_patch(patches.Circle((cx + dx * scale, cy + .905 * scale), .04 * scale, fc=color, ec="none", zorder=8))
    for y in (.54, .34, .14):
        ax.add_line(Line2D([cx - .48 * scale, cx + .16 * scale], [cy + y * scale, cy + y * scale],
                           color=ACCENT, lw=2, zorder=8))
    # chat bubble
    _rounded(ax, cx - .26 * scale, cy - .72 * scale, 1.08 * scale, .56 * scale, WHITE, radius=.11, zorder=6)
    ax.add_patch(patches.Polygon([
        (cx + .18 * scale, cy - .72 * scale),
        (cx + .03 * scale, cy - .92 * scale),
        (cx + .34 * scale, cy - .76 * scale),
    ], closed=True, fc=WHITE, ec="none", zorder=6))
    for y in (-.48, -.63):
        ax.add_line(Line2D([cx - .12 * scale, cx + .46 * scale], [cy + y * scale, cy + y * scale],
                           color=ACCENT, lw=2, zorder=8))
    # sparkle
    ax.add_line(Line2D([cx + .84 * scale, cx + 1.05 * scale], [cy + .06 * scale, cy + .06 * scale], color=WHITE, lw=2.2, zorder=8))
    ax.add_line(Line2D([cx + .945 * scale, cx + .945 * scale], [cy - .05 * scale, cy + .17 * scale], color=WHITE, lw=2.2, zorder=8))
    ax.add_line(Line2D([cx + .86 * scale, cx + 1.03 * scale], [cy - .01 * scale, cy + .13 * scale], color=WHITE, lw=1.8, zorder=8))
    ax.add_line(Line2D([cx + .86 * scale, cx + 1.03 * scale], [cy + .13 * scale, cy - .01 * scale], color=WHITE, lw=1.8, zorder=8))
    _icon_badge(ax, cx - .42 * scale, cy - 1.18 * scale, .84 * scale, .34 * scale, "GPT", ACCENT)


def _plot(output: Path, root: Path) -> None:
    plt.rcParams.update({"font.family": _font(root), "font.size": 10, "axes.unicode_minus": False})
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 17)
    ax.set_ylim(0, 9.2)
    ax.axis("off")
    _rounded(ax, .35, .3, 16.3, 8.55, BG, radius=.24, zorder=1)
    _rounded(ax, .68, 8.37, .09, .13, TITLE_MARKER, radius=.025, zorder=4)
    ax.text(.86, 8.44, "Figura E.2.", fontsize=14.2, color=TEXT, fontweight="bold", va="center")
    ax.text(2.62, 8.44, "Principales hallazgos de la Inteligencia Artificial (IA) y ChatGPT",
            fontsize=14.2, fontweight="medium", color=TEXT, va="center")

    left_x, panel_y, panel_w, panel_h = .76, 1.55, 7.64, 6.2
    right_x = 8.6
    _rounded(ax, left_x, panel_y, panel_w, panel_h, PANEL_IA, radius=.22)
    _rounded(ax, right_x, panel_y, panel_w, panel_h, PANEL_CHATGPT, radius=.22)

    # Icons and panel titles
    _ai_icon(ax, left_x + 1.85, panel_y + 3.82, 1.18)
    ax.text(left_x + 1.85, panel_y + 1.7, "Inteligencia\nArtificial (IA)", ha="center", va="top",
            color=WHITE, fontsize=14.0, fontweight="bold", linespacing=1.22, zorder=9)
    _chat_icon(ax, right_x + 1.72, panel_y + 4.15, 1.12)
    ax.text(right_x + 1.72, panel_y + 1.68, "ChatGPT", ha="center", va="top",
            color=WHITE, fontsize=14.5, fontweight="bold", zorder=9)

    # Findings: use more of each box and reduce unused margins
    left = [item[2] for item in FINDINGS if item[0].startswith("Inteligencia")]
    right = [item[2] for item in FINDINGS if item[0] == "ChatGPT"]

    left_bubble_x = left_x + 3.28
    right_bubble_x = right_x + 3.12
    left_bubble_w = 4.02
    right_bubble_w = 4.28

    _bubble(ax, left_bubble_x, panel_y + 4.83, left_bubble_w, 1.02, "› " + left[0], font_size=9.0, wrap=49)
    _bubble(ax, left_bubble_x, panel_y + 2.47, left_bubble_w, 2.08, "› " + left[1], font_size=9.0, wrap=49)
    _bubble(ax, left_bubble_x, panel_y + .48, left_bubble_w, 1.62, "› " + left[2], font_size=9.0, wrap=49)

    _bubble(ax, right_bubble_x, panel_y + 5.08, right_bubble_w, .85, "› " + right[0], font_size=8.95, wrap=52)
    _bubble(ax, right_bubble_x, panel_y + 3.58, right_bubble_w, 1.34, "› " + right[1], font_size=8.95, wrap=52)
    _bubble(ax, right_bubble_x, panel_y + 2.05, right_bubble_w, 1.35, "› " + right[2], font_size=8.95, wrap=52)
    _bubble(ax, right_bubble_x, panel_y + .18, right_bubble_w, 1.73, "› " + right[3], font_size=8.8, wrap=52)

    ax.text(.7, 1.04, "Fuente:", fontsize=8, color=TEXT, fontweight="bold", va="top")
    ax.text(1.42, 1.04, "IFT, Estudio Cualitativo Conocimiento y Percepción sobre la Inteligencia Artificial (IA) y ChatGPT 2023.",
            fontsize=8, color=TEXT, va="top")
    ax.text(.7, .78, "Nota:", fontsize=8, color=TEXT, fontweight="bold", va="top")
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
