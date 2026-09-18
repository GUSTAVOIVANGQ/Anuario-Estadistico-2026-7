"""Figura F.14: medidas cualitativas de prevención y protección digital."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

FIGURE_ID = "F.14"
SOURCE_ID = "ift_tercera_encuesta_usuarios_2023_pdf"
PERIOD = "2023"

TEXT = "#3C3C3B"
SUBTEXT = "#6B7677"
BACKGROUND = "#F8F8FA"
TITLE_MARKER = "#4A7D75"
PREV_PANEL = "#1A4043"
PROT_PANEL = "#2D7B8A"
WHITE = "#FFFFFF"
MINT = "#6CACAD"
AQUA = "#4A7D75"
BORDER = "#CFD8DA"
SHADOW = "#D9DFE1"

PREVENTION = [
    "Cuidar el tipo de información que comparten y evitar divulgar información personal privada, propia o de familiares.",
    "Tener contacto solamente con personas conocidas y no aceptar a desconocidos.",
    "No entrar a sitios ni vínculos desconocidos, aunque parezcan atractivos.",
    "Utilizar los filtros de seguridad de las plataformas para restringir con quién se comparte información.",
]

PROTECTION = [
    "En casos menos delicados, hacer caso omiso a comentarios negativos, provocaciones o ataques.",
    "Platicar el caso con familiares y amistades de mucha confianza para recibir apoyo y consejo.",
    "En casos graves, acudir a la Policía Cibernética.",
    "Buscar ayuda psicológica.",
]


def build_metrics() -> pd.DataFrame:
    rows = (
        [{"tipo": "Prevención", "orden": i, "medida": m} for i, m in enumerate(PREVENTION, 1)]
        + [{"tipo": "Protección", "orden": i, "medida": m} for i, m in enumerate(PROTECTION, 1)]
    )
    return pd.DataFrame(rows)


def _font(root: Path) -> str:
    for name in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf"):
        path = root / "assets" / "fonts" / "Noto_Sans" / name
        if path.is_file():
            fm.fontManager.addfont(path)
    return "Noto Sans" if any(item.name == "Noto Sans" for item in fm.fontManager.ttflist) else "DejaVu Sans"


def _rounded(ax, x: float, y: float, w: float, h: float, color: str, *, radius: float = .18,
             edge: str = "none", lw: float = 0, z: int = 2):
    patch = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=.02,rounding_size={radius}",
        facecolor=color, edgecolor=edge, linewidth=lw, zorder=z,
    )
    ax.add_patch(patch)
    return patch


class TextMetrics:
    """Measures real glyph widths/heights for the active font so that text
    wrapping and box sizing match what matplotlib will actually render,
    instead of guessing a fixed character width (the cause of the
    text/box overlap in the previous version)."""

    def __init__(self, fig, ax) -> None:
        self._fig = fig
        self._ax = ax
        self._cache: dict[tuple, float] = {}

    def _extent(self, text: str, fontsize: float, linespacing: float = 1.0, weight: str = "normal"):
        artist = self._ax.text(0, 0, text, fontsize=fontsize, linespacing=linespacing,
                                fontweight=weight, ha="left", va="top", alpha=0)
        self._fig.canvas.draw()
        renderer = self._fig.canvas.get_renderer()
        bbox = artist.get_window_extent(renderer=renderer)
        inv = self._ax.transData.inverted()
        x0, y0 = inv.transform((bbox.x0, bbox.y0))
        x1, y1 = inv.transform((bbox.x1, bbox.y1))
        artist.remove()
        return abs(x1 - x0), abs(y1 - y0)

    def line_width(self, text: str, fontsize: float, weight: str = "normal") -> float:
        w, _ = self._extent(text, fontsize, weight=weight)
        return w

    def line_height(self, fontsize: float, linespacing: float) -> float:
        # Measure a known 3-line block so ascender/descender padding of a
        # single short line doesn't distort the per-line figure.
        _, h = self._extent("Áy\nÁy\nÁy", fontsize, linespacing)
        return h / 3

    def wrap(self, text: str, fontsize: float, max_width: float) -> list[str]:
        """Greedy word-wrap using measured pixel widths of the real font."""
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if current and self.line_width(trial, fontsize) > max_width:
                lines.append(current)
                current = word
            else:
                current = trial
        if current:
            lines.append(current)
        return lines


def _shield_icon(ax, cx: float, cy: float, scale: float = 1.0) -> None:
    """Larger shield glyph used as the panel header icon (prevention)."""
    ax.add_patch(patches.Circle((cx, cy), .42 * scale, fc=WHITE, ec="none", zorder=6, alpha=.11))
    ax.add_patch(patches.Circle((cx, cy), .31 * scale, fc=WHITE, ec="none", zorder=7, alpha=.16))
    verts = [
        (cx - .14 * scale, cy + .16 * scale),
        (cx + .14 * scale, cy + .16 * scale),
        (cx + .17 * scale, cy - .01 * scale),
        (cx, cy - .24 * scale),
        (cx - .17 * scale, cy - .01 * scale),
    ]
    ax.add_patch(patches.Polygon(verts, closed=True, fc=WHITE, ec="none", zorder=8))
    ax.add_patch(patches.Arc((cx, cy + .01 * scale), .12 * scale, .12 * scale, theta1=0, theta2=180,
                             color=PREV_PANEL, lw=1.8, zorder=9))
    ax.add_patch(patches.Rectangle((cx - .08 * scale, cy - .08 * scale), .16 * scale, .11 * scale,
                                   fc=PREV_PANEL, ec="none", zorder=9))
    ax.add_line(Line2D([cx - .06 * scale, cx - .01 * scale, cx + .06 * scale],
                       [cy - .01 * scale, cy - .07 * scale, cy + .03 * scale],
                       color=MINT, lw=1.8, zorder=10))


def _support_icon(ax, cx: float, cy: float, scale: float = 1.0) -> None:
    """Larger chat-bubble glyph used as the panel header icon (protection)."""
    ax.add_patch(patches.Circle((cx, cy), .42 * scale, fc=WHITE, ec="none", zorder=6, alpha=.11))
    ax.add_patch(patches.Circle((cx, cy), .31 * scale, fc=WHITE, ec="none", zorder=7, alpha=.16))
    _rounded(ax, cx - .22 * scale, cy - .03 * scale, .30 * scale, .18 * scale, WHITE, radius=.06, z=8)
    ax.add_patch(patches.Polygon([
        (cx - .03 * scale, cy - .03 * scale),
        (cx - .11 * scale, cy - .11 * scale),
        (cx + .01 * scale, cy - .05 * scale),
    ], closed=True, fc=WHITE, ec="none", zorder=8))
    _rounded(ax, cx - .01 * scale, cy + .01 * scale, .20 * scale, .14 * scale, WHITE, radius=.05, z=8)
    ax.add_patch(patches.Polygon([
        (cx + .06 * scale, cy + .01 * scale),
        (cx + .12 * scale, cy - .06 * scale),
        (cx + .10 * scale, cy + .01 * scale),
    ], closed=True, fc=WHITE, ec="none", zorder=8))
    ax.add_line(Line2D([cx - .14 * scale, cx - .04 * scale], [cy + .06 * scale, cy + .06 * scale],
                       color=PROT_PANEL, lw=1.8, zorder=9))
    ax.add_line(Line2D([cx + .03 * scale, cx + .13 * scale], [cy + .07 * scale, cy + .07 * scale],
                       color=PROT_PANEL, lw=1.8, zorder=9))
    ax.add_line(Line2D([cx + .08 * scale, cx + .08 * scale], [cy + .02 * scale, cy + .12 * scale],
                       color=PROT_PANEL, lw=1.8, zorder=9))


def _badge_shield(ax, cx: float, cy: float, accent_color: str) -> None:
    """Small shield-check glyph used as the bullet marker for prevention items."""
    verts = [
        (cx - .085, cy + .095),
        (cx + .085, cy + .095),
        (cx + .105, cy - .015),
        (cx, cy - .155),
        (cx - .105, cy - .015),
    ]
    ax.add_patch(patches.Polygon(verts, closed=True, fc=WHITE, ec="none", zorder=10))
    ax.add_line(Line2D([cx - .045, cx - .008, cx + .055], [cy - .012, cy - .062, cy + .035],
                       color=accent_color, lw=1.7, solid_capstyle="round", zorder=11))


def _badge_support(ax, cx: float, cy: float, accent_color: str) -> None:
    """Small chat-bubble glyph used as the bullet marker for protection items."""
    _rounded(ax, cx - .095, cy - .045, .155, .105, WHITE, radius=.035, z=10)
    ax.add_patch(patches.Polygon([
        (cx - .05, cy - .045),
        (cx - .095, cy - .105),
        (cx - .015, cy - .05),
    ], closed=True, fc=WHITE, ec="none", zorder=10))
    ax.add_line(Line2D([cx - .055, cx + .005], [cy + .005, cy + .005], color=accent_color, lw=1.4, zorder=11))
    ax.add_line(Line2D([cx - .025, cx - .025], [cy - .015, cy + .025], color=accent_color, lw=1.4, zorder=11))


# Layout constants for the item cards inside each panel.
ITEM_FONTSIZE = 9.6
ITEM_LINESPACING = 1.28
ITEM_PAD_V = .22       # vertical padding (top+bottom) inside a card
ITEM_PAD_H = .28       # horizontal padding (left+right) inside a card
ITEM_GAP = .17         # gap between stacked cards
ITEM_MIN_H = .62        # minimum card height (keeps the icon badge comfortable)
BODY_BOTTOM_PAD = .34   # bottom margin below the last card

# Layout constants for the panel heading (icon + full original title).
HEADING_FONTSIZE = 14.6
HEADING_LINESPACING = 1.18
HEADING_TOP_PAD = .40
HEADING_BOTTOM_GAP = .28
DIVIDER_GAP = .30


def _layout_items(tm: TextMetrics, items: list[str], bubble_w: float) -> tuple[list[list[str]], list[float], float]:
    """Wrap each item to the real card width and compute a height that
    exactly fits its wrapped text, so cards never overlap regardless of
    font or content length."""
    max_text_w = bubble_w - ITEM_PAD_H
    line_h = tm.line_height(ITEM_FONTSIZE, ITEM_LINESPACING)
    wrapped: list[list[str]] = []
    heights: list[float] = []
    for item in items:
        lines = tm.wrap(item, ITEM_FONTSIZE, max_text_w)
        h = max(ITEM_MIN_H, len(lines) * line_h + ITEM_PAD_V)
        wrapped.append(lines)
        heights.append(h)
    total = sum(heights) + ITEM_GAP * (len(items) - 1)
    return wrapped, heights, total


def _layout_heading(tm: TextMetrics, heading: str, max_width: float) -> tuple[list[str], float]:
    lines = tm.wrap(heading, HEADING_FONTSIZE, max_width)
    line_h = tm.line_height(HEADING_FONTSIZE, HEADING_LINESPACING)
    header_h = HEADING_TOP_PAD + len(lines) * line_h + HEADING_BOTTOM_GAP + DIVIDER_GAP
    header_h = max(header_h, 1.30)  # keep room for the icon regardless of heading length
    return lines, header_h


def _required_panel_height(header_h: float, total_items_height: float) -> float:
    return header_h + total_items_height + BODY_BOTTOM_PAD


def _section_panel(ax, tm: TextMetrics, x: float, y: float, w: float, h: float, *,
                    heading_lines: list[str], header_h: float,
                    wrapped_items: list[list[str]], item_heights: list[float],
                    panel_color: str, icon: str) -> None:
    _rounded(ax, x + .06, y - .05, w, h, SHADOW, radius=.22, z=0)
    _rounded(ax, x, y, w, h, panel_color, radius=.22, z=1)

    icon_x = x + .88
    icon_y = y + h - header_h / 2
    text_x = x + 1.30

    if icon == "shield":
        _shield_icon(ax, icon_x, icon_y, .82)
        badge = _badge_shield
    else:
        _support_icon(ax, icon_x, icon_y, .82)
        badge = _badge_support

    line_h = tm.line_height(HEADING_FONTSIZE, HEADING_LINESPACING)
    ty = y + h - HEADING_TOP_PAD - line_h * .72
    for line in heading_lines:
        ax.text(text_x, ty, line, ha="left", va="center",
                fontsize=HEADING_FONTSIZE, fontweight="bold", color=WHITE, zorder=9)
        ty -= line_h

    divider_y = y + h - header_h + DIVIDER_GAP * .55
    ax.plot([text_x, x + w - .40], [divider_y, divider_y], color=WHITE, alpha=.22, lw=.9, zorder=9)

    bubble_x = x + 1.90
    bubble_w = w - 2.20

    content_top = y + h - header_h
    content_bottom = y + BODY_BOTTOM_PAD
    available = content_top - content_bottom
    total_items_h = sum(item_heights) + ITEM_GAP * (len(item_heights) - 1)
    start_y = content_top - max(0.0, (available - total_items_h) / 2)

    yy = start_y
    for lines, item_h in zip(wrapped_items, item_heights):
        yy -= item_h
        cy = yy + item_h / 2
        ax.add_patch(patches.Circle((x + .84, cy), .205, fc=MINT, ec="none", zorder=8))
        badge(ax, x + .84, cy, panel_color)
        _rounded(ax, bubble_x + .035, cy - item_h / 2 - .035, bubble_w, item_h, SHADOW, radius=.11, z=4)
        _rounded(ax, bubble_x, cy - item_h / 2, bubble_w, item_h, WHITE, radius=.11, edge=BORDER, lw=.75, z=5)
        ax.text(bubble_x + .16, cy, "\n".join(lines), ha="left", va="center",
                fontsize=ITEM_FONTSIZE, color=TEXT, linespacing=ITEM_LINESPACING, zorder=6)
        yy -= ITEM_GAP


HEADING_PREVENTION = "Medidas preventivas para evitar ser víctima de violencia digital"
HEADING_PROTECTION = "Medidas de protección una vez que han sido víctimas de violencia digital"


def _plot(data: pd.DataFrame, out: Path, root: Path) -> None:
    plt.rcParams.update({"font.family": _font(root), "font.size": 10, "axes.unicode_minus": False})
    fig, ax = plt.subplots(figsize=(16, 9.6))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 17.6)
    ax.set_ylim(0, 11)
    ax.axis("off")

    tm = TextMetrics(fig, ax)

    left_x = .72
    panel_gap = .30
    panel1_w, panel2_w = 7.66, 7.34
    panel1_x = left_x
    panel2_x = left_x + panel1_w + panel_gap
    content_w = panel1_w + panel_gap + panel2_w

    # ---- content-driven sizing (bottom-up) --------------------------------
    heading_prev_lines, header_h_prev = _layout_heading(tm, HEADING_PREVENTION, panel1_w - 1.70)
    heading_prot_lines, header_h_prot = _layout_heading(tm, HEADING_PROTECTION, panel2_w - 1.70)

    wrapped_prev, heights_prev, total_prev = _layout_items(tm, PREVENTION, panel1_w - 2.20)
    wrapped_prot, heights_prot, total_prot = _layout_items(tm, PROTECTION, panel2_w - 2.20)

    header_h = max(header_h_prev, header_h_prot)
    panel_h = max(
        _required_panel_height(header_h, total_prev),
        _required_panel_height(header_h, total_prot),
    )

    gap_panel_footer = .58
    gap_title_panel = .40
    margin_bottom = .55
    margin_top = .52

    footer_line_gap = .27
    footer_h = footer_line_gap * 2

    # y-coordinates, built from the bottom of the composition upward
    bottom_y = margin_bottom
    footer_y = bottom_y + footer_h
    panel_y = footer_y + gap_panel_footer
    panel_top = panel_y + panel_h
    title_y = panel_top + gap_title_panel
    canvas_top = title_y + margin_top

    ax.set_xlim(0, content_w + 1.44)
    ax.set_ylim(0, canvas_top + .35)

    _rounded(ax, .35, bottom_y - .30, content_w + 1.10, canvas_top - bottom_y + .55,
             BACKGROUND, radius=.24, z=0)

    _rounded(ax, .66, title_y - .07, .09, .13, TITLE_MARKER, radius=.025, z=3)
    label = "Figura F.14."
    ax.text(.86, title_y, label, color=TEXT, fontsize=14.4, fontweight="bold", va="center", ha="left")
    label_w = tm.line_width(label, 14.4, weight="bold")
    ax.text(.86 + label_w + .18, title_y, "Medidas preventivas y de protección ante la violencia digital (2023)",
            color=TEXT, fontsize=14.4, va="center", ha="left")

    _section_panel(
        ax, tm, panel1_x, panel_y, panel1_w, panel_h,
        heading_lines=heading_prev_lines,
        header_h=header_h,
        wrapped_items=wrapped_prev,
        item_heights=heights_prev,
        panel_color=PREV_PANEL,
        icon="shield",
    )
    _section_panel(
        ax, tm, panel2_x, panel_y, panel2_w, panel_h,
        heading_lines=heading_prot_lines,
        header_h=header_h,
        wrapped_items=wrapped_prot,
        item_heights=heights_prot,
        panel_color=PROT_PANEL,
        icon="support",
    )

    ax.text(left_x, footer_y, "Fuente:", color=TEXT, fontsize=8.6, fontweight="bold", va="top")
    ax.text(left_x + .78, footer_y,
            "Elaborado por CRT con información de la Tercera Encuesta 2023, Personas Usuarias de Servicios de Telecomunicaciones.",
            color=SUBTEXT, fontsize=8.6, va="top")
    ax.text(left_x, footer_y - footer_line_gap, "Nota:", color=TEXT, fontsize=8.6, fontweight="bold", va="top")
    ax.text(left_x + .57, footer_y - footer_line_gap,
            "Información correspondiente al estudio cualitativo; no es representativa a nivel nacional.",
            color=SUBTEXT, fontsize=8.6, va="top")

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, facecolor="white", edgecolor="none", bbox_inches="tight", pad_inches=.18)
    plt.close(fig)


def generate(context):
    print("  F.14 | Reutilización o descarga del reporte oficial IFT")
    source = context.acquire_source(SOURCE_ID)
    if source.read_bytes()[:4] != b"%PDF":
        raise ValueError("La fuente de F.14 no es un PDF válido")
    data = build_metrics()
    context.record_source_period(SOURCE_ID, PERIOD, "ULTIMO_COMPATIBLE")
    context.write_data_used(data)
    for row in data.itertuples(index=False):
        context.record_calculation(
            f"{row.tipo.lower()}_{row.orden}",
            "síntesis fiel del hallazgo cualitativo publicado",
            {"pagina_fuente": "apartado de violencia digital", "tipo": row.tipo},
            row.medida,
            "texto cualitativo",
        )
    text_path = context.render_text(
        "f_digital.md.j2",
        {
            "resumen": "El estudio cualitativo recomienda limitar la exposición de información personal, usar filtros de seguridad y buscar apoyo o denunciar cuando corresponda.",
        },
    )
    _plot(data, context.expected_figure_path, context.project_root)
    return {
        "figure_path": str(context.expected_figure_path),
        "text_path": str(text_path),
        "source_latest_period": PERIOD,
        "rows_used": len(data),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "src"))
    from anuario2026.pipeline import run_pipeline

    run_pipeline(root, only=FIGURE_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())