"""Figura F.14: medidas cualitativas de prevención y protección digital.

Rediseño inspirado en la composición de la Figura F.14 del Anuario Estadístico 2024:
- dos paneles paralelos;
- ilustración/identidad visual en el tercio izquierdo de cada panel;
- encabezado en la parte inferior izquierda;
- cuatro tarjetas tipo bocadillo apiladas en el lado derecho.

La paleta cromática del proyecto se conserva; la referencia se usa solamente para
jerarquía y posición de los elementos.
"""
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

# Paleta original del proyecto (sin copiar los colores del Anuario).
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

HEADING_PREVENTION = "Medidas preventivas para evitar ser víctima de violencia digital"
HEADING_PROTECTION = "Medidas de protección una vez que han sido víctimas de violencia digital"


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
             edge: str = "none", lw: float = 0, z: int = 2, alpha: float = 1.0):
    patch = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=.02,rounding_size={radius}",
        facecolor=color, edgecolor=edge, linewidth=lw, zorder=z, alpha=alpha,
    )
    ax.add_patch(patch)
    return patch


class TextMetrics:
    def __init__(self, fig, ax) -> None:
        self._fig = fig
        self._ax = ax

    def _extent(self, text: str, fontsize: float, linespacing: float = 1.0, weight: str = "normal"):
        artist = self._ax.text(
            0, 0, text, fontsize=fontsize, linespacing=linespacing,
            fontweight=weight, ha="left", va="top", alpha=0,
        )
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
        _, h = self._extent("Áy\nÁy\nÁy", fontsize, linespacing)
        return h / 3

    def wrap(self, text: str, fontsize: float, max_width: float, weight: str = "normal") -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if current and self.line_width(trial, fontsize, weight) > max_width:
                lines.append(current)
                current = word
            else:
                current = trial
        if current:
            lines.append(current)
        return lines


# ---------- Ilustraciones vectoriales sobrias (misma paleta) -----------------

def _draw_device_shield(ax, cx: float, cy: float, s: float = 1.0) -> None:
    """Ilustración formal para prevención: persona, laptop y escudo."""
    # halo discreto
    ax.add_patch(patches.Circle((cx, cy + .05*s), 1.00*s, fc=WHITE, ec="none", alpha=.07, zorder=3))

    # laptop
    _rounded(ax, cx - .78*s, cy - .48*s, 1.56*s, .78*s, WHITE, radius=.09*s, z=6, alpha=.96)
    _rounded(ax, cx - .66*s, cy - .38*s, 1.32*s, .56*s, panel_mix(PREV_PANEL, 0.88), radius=.05*s, z=7)
    ax.add_patch(patches.Polygon([
        (cx - .92*s, cy - .53*s), (cx + .92*s, cy - .53*s),
        (cx + .72*s, cy - .72*s), (cx - .72*s, cy - .72*s),
    ], closed=True, fc=WHITE, ec="none", zorder=6, alpha=.96))

    # persona detrás de la laptop
    ax.add_patch(patches.Circle((cx, cy + .78*s), .28*s, fc=WHITE, ec="none", zorder=5))
    ax.add_patch(patches.Arc((cx, cy + .79*s), .68*s, .72*s, theta1=8, theta2=172,
                             color=MINT, lw=10*s, zorder=4, capstyle="round"))
    _rounded(ax, cx - .36*s, cy + .20*s, .72*s, .58*s, MINT, radius=.22*s, z=4, alpha=.90)

    # escudo flotante
    sx, sy = cx + .92*s, cy + .38*s
    ax.add_patch(patches.Circle((sx, sy), .39*s, fc=WHITE, ec="none", alpha=.15, zorder=7))
    verts = [
        (sx - .20*s, sy + .20*s), (sx + .20*s, sy + .20*s),
        (sx + .24*s, sy - .04*s), (sx, sy - .34*s), (sx - .24*s, sy - .04*s),
    ]
    ax.add_patch(patches.Polygon(verts, closed=True, fc=WHITE, ec="none", zorder=8))
    ax.add_line(Line2D([sx - .10*s, sx - .02*s, sx + .13*s],
                       [sy - .02*s, sy - .12*s, sy + .10*s],
                       color=PREV_PANEL, lw=2.4*s, solid_capstyle="round", zorder=9))

    # pequeña tarjeta de identidad
    ix, iy = cx - 1.05*s, cy + .34*s
    _rounded(ax, ix - .28*s, iy - .22*s, .56*s, .46*s, WHITE, radius=.05*s, z=7)
    ax.add_patch(patches.Circle((ix, iy + .08*s), .07*s, fc=PREV_PANEL, ec="none", zorder=8))
    ax.plot([ix - .16*s, ix + .16*s], [iy - .06*s, iy - .06*s], color=PREV_PANEL, lw=1.6*s, zorder=8)
    ax.plot([ix - .10*s, ix + .10*s], [iy - .13*s, iy - .13*s], color=MINT, lw=1.6*s, zorder=8)


def _draw_support_network(ax, cx: float, cy: float, s: float = 1.0) -> None:
    """Ilustración formal para protección: persona contenida por una red de apoyo."""
    ax.add_patch(patches.Circle((cx, cy + .03*s), 1.02*s, fc=WHITE, ec="none", alpha=.07, zorder=3))

    # red de apoyo: nodos alrededor
    for dx, dy, r in [(-.92,.50,.22), (.94,.52,.22), (-1.02,-.18,.19), (1.03,-.18,.19), (0,.98,.20)]:
        ax.add_patch(patches.Circle((cx + dx*s, cy + dy*s), r*s, fc=WHITE, ec="none", alpha=.88, zorder=5))
        ax.add_patch(patches.Circle((cx + dx*s, cy + (dy+.035)*s), .055*s, fc=PROT_PANEL, ec="none", zorder=6))
        ax.add_patch(patches.Arc((cx + dx*s, cy + (dy-.045)*s), .16*s, .11*s,
                                 theta1=0, theta2=180, color=PROT_PANEL, lw=2.0*s, zorder=6))
        ax.plot([cx + dx*.78*s, cx], [cy + dy*.78*s, cy + .10*s], color=WHITE,
                lw=1.2*s, alpha=.42, zorder=4)

    # persona central
    ax.add_patch(patches.Circle((cx, cy + .38*s), .29*s, fc=WHITE, ec="none", zorder=7))
    ax.add_patch(patches.Arc((cx, cy + .40*s), .72*s, .75*s, theta1=8, theta2=172,
                             color=MINT, lw=10*s, zorder=6, capstyle="round"))
    _rounded(ax, cx - .42*s, cy - .35*s, .84*s, .74*s, WHITE, radius=.28*s, z=6, alpha=.96)
    # corazón / apoyo
    ax.add_patch(patches.Circle((cx - .06*s, cy - .02*s), .09*s, fc=PROT_PANEL, ec="none", zorder=8))
    ax.add_patch(patches.Circle((cx + .06*s, cy - .02*s), .09*s, fc=PROT_PANEL, ec="none", zorder=8))
    ax.add_patch(patches.Polygon([
        (cx - .14*s, cy - .01*s), (cx + .14*s, cy - .01*s), (cx, cy - .20*s),
    ], closed=True, fc=PROT_PANEL, ec="none", zorder=8))

    # burbuja superior que refuerza la idea de pedir ayuda
    bx, by = cx + .70*s, cy + .95*s
    _rounded(ax, bx - .30*s, by - .13*s, .60*s, .27*s, WHITE, radius=.08*s, z=8)
    ax.add_patch(patches.Polygon([
        (bx - .05*s, by - .12*s), (bx + .04*s, by - .25*s), (bx + .10*s, by - .11*s),
    ], closed=True, fc=WHITE, ec="none", zorder=8))
    ax.plot([bx - .11*s, bx + .11*s], [by, by], color=PROT_PANEL, lw=1.8*s, zorder=9)
    ax.plot([bx, bx], [by - .08*s, by + .08*s], color=PROT_PANEL, lw=1.8*s, zorder=9)


def panel_mix(color: str, factor: float) -> str:
    """Mezcla muy ligera con blanco para usar una tonalidad del mismo color base."""
    color = color.lstrip("#")
    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    mixed = tuple(round(255 - (255-c)*factor) for c in rgb)
    return "#%02X%02X%02X" % mixed


# ---------- Tarjetas y composición -------------------------------------------
ITEM_FONTSIZE = 9.25
ITEM_LINESPACING = 1.22
CARD_PAD_X = .18
CARD_PAD_Y = .16
CARD_MIN_H = .70
CARD_GAP = .20


def _layout_cards(tm: TextMetrics, items: list[str], width: float) -> tuple[list[list[str]], list[float]]:
    text_w = width - 2*CARD_PAD_X
    line_h = tm.line_height(ITEM_FONTSIZE, ITEM_LINESPACING)
    wrapped: list[list[str]] = []
    heights: list[float] = []
    for item in items:
        lines = tm.wrap(item, ITEM_FONTSIZE, text_w)
        h = max(CARD_MIN_H, len(lines)*line_h + 2*CARD_PAD_Y)
        wrapped.append(lines)
        heights.append(h)
    return wrapped, heights


def _speech_card(ax, x: float, cy: float, w: float, h: float, lines: list[str], panel_color: str) -> None:
    """Tarjeta con pequeña punta hacia la ilustración, como en la referencia."""
    y = cy - h/2
    tail_w = .15
    tail_h = min(.23, h*.28)

    # sombra
    _rounded(ax, x + .035, y - .035, w, h, SHADOW, radius=.14, z=4, alpha=.72)
    ax.add_patch(patches.Polygon([
        (x + .04, cy + tail_h/2 - .035),
        (x - tail_w + .04, cy - .035),
        (x + .04, cy - tail_h/2 - .035),
    ], closed=True, fc=SHADOW, ec="none", alpha=.72, zorder=4))

    # cuerpo y cola
    _rounded(ax, x, y, w, h, WHITE, radius=.14, edge=BORDER, lw=.6, z=5)
    ax.add_patch(patches.Polygon([
        (x + .01, cy + tail_h/2), (x - tail_w, cy), (x + .01, cy - tail_h/2),
    ], closed=True, fc=WHITE, ec="none", zorder=6))

    ax.text(x + CARD_PAD_X, cy, "\n".join(lines), ha="left", va="center",
            fontsize=ITEM_FONTSIZE, color=TEXT, linespacing=ITEM_LINESPACING, zorder=7)


def _draw_heading(ax, tm: TextMetrics, x: float, y: float, width: float, text: str, *, fontsize: float) -> None:
    lines = tm.wrap(text, fontsize, width, weight="bold")
    line_h = tm.line_height(fontsize, 1.08)
    # y is the top of the heading block
    yy = y
    for line in lines:
        ax.text(x, yy, line, ha="left", va="top", fontsize=fontsize,
                fontweight="bold", color=WHITE, zorder=9)
        yy -= line_h


def _section_panel(ax, tm: TextMetrics, x: float, y: float, w: float, h: float, *,
                   heading: str, items: list[str], panel_color: str, kind: str) -> None:
    # panel and understated shadow
    _rounded(ax, x + .05, y - .055, w, h, SHADOW, radius=.22, z=0, alpha=.78)
    _rounded(ax, x, y, w, h, panel_color, radius=.22, z=1)

    # Referencia de página 98: aproximadamente 41% para ilustración/título y 59% para tarjetas.
    left_col_w = w * .405
    card_x = x + left_col_w + .16
    card_w = w - (card_x - x) - .26

    wrapped, heights = _layout_cards(tm, items, card_w)
    total = sum(heights) + CARD_GAP*(len(heights)-1)
    available_top = y + h - .55
    available_bottom = y + .45
    available = available_top - available_bottom
    if total > available:
        # compactación limitada; no altera tipografía ni posiciones relativas.
        gap = max(.10, (available - sum(heights))/(len(heights)-1))
    else:
        gap = CARD_GAP
    total = sum(heights) + gap*(len(heights)-1)
    start = available_top - max(0.0, (available - total)/2)

    yy = start
    for lines, ch in zip(wrapped, heights):
        cy = yy - ch/2
        _speech_card(ax, card_x, cy, card_w, ch, lines, panel_color)
        yy -= ch + gap

    # Ilustración: arriba-izquierda; encabezado: abajo-izquierda.
    ill_cx = x + left_col_w*.50
    ill_cy = y + h*.68
    if kind == "prevention":
        _draw_device_shield(ax, ill_cx, ill_cy, .92)
        heading_fs = 12.6
    else:
        _draw_support_network(ax, ill_cx, ill_cy, .88)
        heading_fs = 12.25

    # pequeño acento horizontal para ordenar la columna sin copiar la gráfica original
    ax.plot([x + .42, x + left_col_w - .32], [y + 2.08, y + 2.08],
            color=WHITE, alpha=.22, lw=.9, zorder=8)
    _draw_heading(
        ax, tm,
        x + .42, y + 1.86,
        left_col_w - .70,
        heading,
        fontsize=heading_fs,
    )


def _plot(data: pd.DataFrame, out: Path, root: Path) -> None:
    plt.rcParams.update({
        "font.family": _font(root),
        "font.size": 10,
        "axes.unicode_minus": False,
    })

    fig, ax = plt.subplots(figsize=(16, 9.15))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 17.6)
    ax.set_ylim(0, 10.15)
    ax.axis("off")
    tm = TextMetrics(fig, ax)

    # Contenedor general similar a la versión previa del proyecto.
    _rounded(ax, .35, .35, 16.90, 9.42, BACKGROUND, radius=.24, z=0)

    # Título superior formal.
    title_y = 9.25
    _rounded(ax, .66, title_y - .075, .09, .15, TITLE_MARKER, radius=.025, z=3)
    label = "Figura F.14."
    ax.text(.86, title_y, label, color=TEXT, fontsize=14.2, fontweight="bold", va="center", ha="left")
    label_w = tm.line_width(label, 14.2, weight="bold")
    ax.text(.86 + label_w + .18, title_y,
            "Medidas preventivas y de protección ante la violencia digital (2023)",
            color=TEXT, fontsize=14.2, va="center", ha="left")

    # Dos paneles con proporciones y distribución inspiradas en la página 98.
    panel_y = 1.58
    panel_h = 7.05
    left_x = .72
    panel_gap = .30
    panel1_w = 7.66
    panel2_w = 7.34
    panel2_x = left_x + panel1_w + panel_gap

    _section_panel(
        ax, tm, left_x, panel_y, panel1_w, panel_h,
        heading=HEADING_PREVENTION,
        items=PREVENTION,
        panel_color=PREV_PANEL,
        kind="prevention",
    )
    _section_panel(
        ax, tm, panel2_x, panel_y, panel2_w, panel_h,
        heading=HEADING_PROTECTION,
        items=PROTECTION,
        panel_color=PROT_PANEL,
        kind="protection",
    )

    # Pie de figura: limpio y separado de los paneles.
    footer_y = .92
    ax.text(left_x, footer_y, "Fuente:", color=TEXT, fontsize=8.55, fontweight="bold", va="top")
    ax.text(left_x + .78, footer_y,
            "Elaborado por CRT con información de la Tercera Encuesta 2023, Personas Usuarias de Servicios de Telecomunicaciones.",
            color=SUBTEXT, fontsize=8.55, va="top")
    ax.text(left_x, footer_y - .28, "Nota:", color=TEXT, fontsize=8.55, fontweight="bold", va="top")
    ax.text(left_x + .57, footer_y - .28,
            "Información correspondiente al estudio cualitativo; no es representativa a nivel nacional.",
            color=SUBTEXT, fontsize=8.55, va="top")

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=220, facecolor="white", edgecolor="none", bbox_inches="tight", pad_inches=.16)
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
