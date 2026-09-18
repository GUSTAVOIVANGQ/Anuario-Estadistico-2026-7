"""Compatibilidad visual con las figuras del Anuario Estadístico 2024.

Este módulo SOLO transforma artistas de Matplotlib justo antes de guardar el PNG.
No toca adquisición, cálculos, periodos, archivos de datos ni metadatos.

La paleta y los neutros proceden de ``scripts/estilos.py`` del proyecto 2024.
Las excepciones por figura se obtuvieron comparando la figura y el script con el
mismo identificador (A.1, B.9, etc.). B.8, F.1.4 y F.3 se excluyen en los
scripts de integración porque no tienen una correspondencia 2024 segura/verificable.
"""
from __future__ import annotations

from collections.abc import Iterable

import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.container import BarContainer
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

TEXT = "#3c3c3b"
AXES_BG = "#F8F8FA"
AXIS = "#7c7c7c"
GRID = "#d1d1d1"
TITLE_MARKER = "#4a7d75"
TEAL = ("#132b2d", "#234244", "#335a5c", "#3b6667", "#4c7d7e", "#5c9596", "#64a0a1", "#86adae")
MAP_GREEN = ("#afafaf", "#737f7c", "#63918b", "#2d4f4b", "#012f2a")

# Orden visual de series/categorías según el código 2024. No modifica datos.
PALETTES: dict[str, tuple[str, ...]] = {
    "A.1": ("#86adae", "#2c3e40"),
    "A.2": ("#335a5c", "#86adae"),
    "A.3": ("#006157", "#b35aba"),
    "A.4": ("#234244", "#4c7d7e", "#64a0a1", "#86adae"),
    "A.5": ("#86adae", "#335a5c"),
    "A.6": ("#335a5c", "#86adae"),
    "A.7": ("#335a5c", "#86adae"),
    "A.8": ("#86adae", "#335a5c"),
    "A.9": ("#335a5c", "#86adae"),
    "A.10": ("#86adae", "#335a5c"),
    "B.1": TEAL,
    "B.2": TEAL,
    "B.3": TEAL,
    "B.4": ("#006157",),
    "B.5": ("#335a5c",),
    "B.6": MAP_GREEN,
    "B.7": MAP_GREEN,
    "B.8": ("#335a5c",),
    "B.9": ("#1e6284", "#ed8945", "#5844a0", "#99b554", "#8e244d", "#368491", "#728781"),
    "B.10": ("#335a5c",),
    "B.11": ("#006157",),
    "B.12": ("#006157",),
    "B.13": MAP_GREEN,
    "B.14": MAP_GREEN,
    "B.15": ("#6cacad", "#2d7b8a", "#1a4043", "#728781"),
    "B.16": ("#132b2d", "#3b6667", "#64a0a1", "#86adae", "#afafaf"),
    "B.17": ("#1e6284", "#ed8945", "#5844a0", "#99b554", "#8e244d", "#728781", "#64a0a1", "#2d4f4b", "#b18193"),
    "B.18": ("#c0392b",),
    "B.19": ("#006157",),
    "B.20": ("#86adae",),
    "B.21": MAP_GREEN,
    "B.22": MAP_GREEN,
    "B.23": ("#132b2d", "#3b6667", "#64a0a1", "#86adae"),
    "B.24": ("#a8d8ea", "#1a5276", "#2e4057", "#5dade2", "#f0a500", "#e74c3c"),
    "B.25": ("#335a5c",),
    "C.1": TEAL,
    "C.2": ("#753d6a", "#667489", "#8e244d"),
    "C.3": ("#3b6667", "#132b2d"),
    "C.4": ("#86adae", "#3b6667", "#343b5c", "#b5b7c8", "#e0e0e0"),
    "C.5": ("#86adae", "#64a0a1", "#5c9596", "#4c7d7e", "#3b6667", "#132b2d"),
    "C.6": ("#335a5c",),
    "C.7": MAP_GREEN,
    "C.8": ("#006157",),
    "C.9": ("#1e6284", "#ed8945", "#5844a0", "#99b554"),
    "C.10": ("#335a5c",),
    "C.11": ("#86adae", "#64a0a1", "#5c9596", "#4c7d7e", "#3b6667", "#132b2d"),
    "C.12": ("#006157",),
    "C.13": MAP_GREEN,
    "C.14": ("#86adae", "#4c7d7e", "#132b2d"),
    "C.15": ("#1e6284", "#667489", "#1b4044", "#368491", "#728781"),
    "C.16": ("#335a5c",),
    "D.1": ("#006157", "#b35aba", "#ed8945", "#368491", "#8e244d"),
    "D.2": ("#86adae", "#335a5c"),
    "D.3": ("#86adae", "#64a0a1", "#5c9596", "#4c7d7e", "#3b6667", "#335a5c", "#234244", "#132b2d"),
    "D.4": ("#86adae",),
    "D.5": ("#86adae", "#64a0a1", "#5c9596", "#4c7d7e", "#3b6667", "#335a5c", "#234244", "#132b2d"),
    "D.6": ("#afafaf", "#86adae", "#335a5c"),
    "D.7": ("#86adae", "#64a0a1", "#335a5c", "#132b2d"),
    "D.8": ("#86adae", "#64a0a1", "#4c7d7e", "#3b6667", "#335a5c", "#132b2d"),
    "D.9": ("#86adae", "#64a0a1", "#4c7d7e", "#335a5c", "#132b2d"),
    "D.10": ("#86adae", "#64a0a1", "#4c7d7e", "#335a5c", "#132b2d"),
    "D.11": ("#335a5c", "#86adae"),
    "E.1": ("#86adae", "#64a0a1", "#4c7d7e", "#335a5c"),
    "E.2": ("#1a4043", "#2d7b8a", "#6cacad"),
    "E.3": ("#afafaf", "#86adae"),
    # E.4 y E.5 conservan sus paletas editoriales particulares del 2024.
    "E.4": ("#ea746a", "#d8e8e2", "#f0f5f8", "#f9dfd6", "#f4ae9d", "#f4bcad", "#ec7c6f", "#c0d5e0", "#80a8ba", "#5b6770"),
    "E.5": ("#335a5c", "#86adae"),
    "E.6": ("#afafaf", "#86adae", "#5c9596", "#335a5c"),
    "E.7": ("#86adae", "#335a5c"),
    "E.8": ("#335a5c",),
    "E.9": ("#335a5c",),
    "F.1.1": ("#b35aba", "#006157"),
    "F.1.2": ("#b35aba", "#006157"),
    "F.1.3": ("#b35aba", "#006157"),
    "F.1.4": ("#b35aba", "#006157"),
    "F.2": ("#64a0a1", "#132b2d"),
    "F.4": ("#86adae", "#335a5c"),
    "F.5": ("#86adae", "#335a5c"),
    "F.6": ("#335a5c", "#86adae"),
    "F.7": ("#335a5c", "#86adae"),
    "F.8": ("#86adae",),
    "F.9": ("#335a5c",),
    "F.10": ("#335a5c", "#86adae"),
    "F.11": ("#335a5c", "#86adae"),
    "F.12": ("#335a5c", "#86adae"),
    "F.13": ("#86adae", "#335a5c"),
    "F.14": ("#1a4043", "#2d7b8a", "#6cacad"),
    "F.15": ("#afafaf", "#86adae", "#335a5c"),
    "F.16": ("#afafaf", "#86adae", "#335a5c"),
}

# Figuras cuyo referente usa barras rectangulares y el 2026 incluía extremos
# redondeados o clip paths redondeados.
RECTANGULAR_BAR_IDS = {
    "A.1", "A.2", "A.4", "A.5", "A.6", "A.7", "A.8", "A.9", "A.10",
    "B.5", "B.20", "B.25", "E.1", "E.9", "F.10", "F.11", "F.13", "F.15", "F.16",
}

# Las paletas especiales de E.4/E.5 contienen tarjetas y diagramas propios;
# no se fuerza el fondo de todos sus ejes para no alterar su composición.
KEEP_SPECIAL_BACKGROUNDS = {"E.4", "E.5"}


def format_source_credit(value: object) -> object:
    """Normaliza únicamente el organismo que encabeza los pies de fuente."""
    if not isinstance(value, str):
        return value
    leading = value[: len(value) - len(value.lstrip())]
    body = value.lstrip()
    if body.startswith("Elaborado por CRT"):
        return value
    if body.startswith("IFT "):
        return leading + "Elaborado por CRT " + body[4:]
    if body.startswith("IFT,"):
        return leading + "Elaborado por CRT," + body[4:]
    if body.startswith("CRT "):
        return leading + "Elaborado por CRT " + body[4:]
    if body.startswith("CRT,"):
        return leading + "Elaborado por CRT," + body[4:]
    return value


def install_source_credit_normalizer() -> None:
    """Aplica el crédito institucional a texto de figura y de ejes.

    Se instala una sola vez antes de cargar los generadores. Así cubre también
    figuras históricas que construyen el pie directamente con ``fig.text`` o
    ``ax.text`` y mantiene intactos títulos, notas y datos.
    """
    if getattr(Figure.text, "_crt_source_credit", False):
        return

    original_figure_text = Figure.text
    original_axes_text = Axes.text

    def figure_text(self, x, y, s, *args, **kwargs):
        return original_figure_text(self, x, y, format_source_credit(s), *args, **kwargs)

    def axes_text(self, x, y, s, *args, **kwargs):
        return original_axes_text(self, x, y, format_source_credit(s), *args, **kwargs)

    figure_text._crt_source_credit = True
    axes_text._crt_source_credit = True
    Figure.text = figure_text
    Axes.text = axes_text


def annotate_stacked_segments_outside(
    ax,
    bar_x: float,
    segments: list[dict[str, float | int | str]],
    *,
    bar_width: float,
    x_offset: float = 0.22,
    lower: float = 2.0,
    upper: float = 98.0,
    min_gap: float = 6.0,
    fontsize: float = 6.2,
    decimals: int = 1,
) -> None:
    """Coloca todos los porcentajes fuera de una barra apilada con guías.

    Cada segmento requiere ``index``, ``value``, ``center`` y ``color``. Los
    segmentos se alternan a izquierda/derecha y sus alturas se redistribuyen
    por costado para evitar superposiciones sin alterar las barras.
    """
    visible = [item for item in segments if float(item["value"]) > 0.005]
    for side in (-1, 1):
        group = [item for item in visible if (-1 if int(item["index"]) % 2 == 0 else 1) == side]
        group.sort(key=lambda item: float(item["center"]))
        positions: list[float] = []
        for item in group:
            center = float(item["center"])
            positions.append(max(center, positions[-1] + min_gap if positions else center))
        if positions and positions[-1] > upper:
            shift = positions[-1] - upper
            positions = [position - shift for position in positions]
        for index in range(len(positions) - 2, -1, -1):
            positions[index] = min(positions[index], positions[index + 1] - min_gap)
        if positions and positions[0] < lower:
            shift = lower - positions[0]
            positions = [position + shift for position in positions]

        for item, label_y in zip(group, positions, strict=False):
            center = float(item["center"])
            value = float(item["value"])
            precision = 2 if value < 0.1 else decimals
            edge_x = bar_x + side * bar_width / 2
            label_x = edge_x + side * x_offset
            ax.annotate(
                f"{value:.{precision}f}%",
                xy=(edge_x, center),
                xytext=(label_x, label_y),
                textcoords="data",
                ha="right" if side < 0 else "left",
                va="center",
                fontsize=fontsize,
                fontweight="bold",
                color=TEXT,
                zorder=8,
                bbox=dict(
                    boxstyle="round,pad=0.20,rounding_size=0.35",
                    facecolor="white",
                    edgecolor="none",
                    alpha=0.98,
                ),
                arrowprops=dict(
                    arrowstyle="-",
                    color=str(item["color"]),
                    linewidth=0.75,
                    shrinkA=0,
                    shrinkB=0,
                    connectionstyle="arc3,rad=0",
                ),
                annotation_clip=False,
            )


def _is_white(color) -> bool:
    try:
        r, g, b, a = mcolors.to_rgba(color)
    except (TypeError, ValueError):
        return False
    return r > .94 and g > .94 and b > .94 and a > .5


def _set_text_color(text) -> None:
    # Normaliza únicamente colores tipográficos de UI/neutral. Los colores que
    # codifican datos (p. ej. Mujeres/Hombres en F.1) se conservan.
    color = text.get_color()
    if _is_white(color):
        return
    try:
        rgba = mcolors.to_rgba(color)
        rgb = rgba[:3]
        hex_color = mcolors.to_hex(rgba, keep_alpha=False).lower()
    except (TypeError, ValueError):
        return
    generic_ui = {
        "#565682", "#4b4b83", "#4b4b7d", "#50517f", "#4b4d7b",
        "#222222", "#333333", "#444444", "#3c3c3b", "#000000",
    }
    neutral_dark = max(rgb) < .70 and (max(rgb) - min(rgb)) < .075
    if hex_color in generic_ui or neutral_dark:
        text.set_color(TEXT)
    try:
        text.set_fontfamily("Noto Sans")
    except Exception:
        pass


def _bar_containers(ax) -> list[BarContainer]:
    return [container for container in ax.containers if isinstance(container, BarContainer)]


def _recolor_bars(ax, palette: tuple[str, ...], figure_id: str) -> None:
    containers = _bar_containers(ax)
    if not containers:
        return
    if len(containers) == 1:
        patches = list(containers[0].patches)
        if figure_id == "F.10":
            # Referente: dos categorías destacadas en teal oscuro y el resto claro.
            colors = ["#335a5c" if index < 2 else "#86adae" for index in range(len(patches))]
        elif figure_id in {"D.3", "D.5", "D.8", "E.1", "F.12"} and len(palette) > 1:
            colors = [palette[index % len(palette)] for index in range(len(patches))]
        else:
            colors = [palette[0]] * len(patches)
        for patch, color in zip(patches, colors, strict=False):
            patch.set_facecolor(color)
            patch.set_edgecolor("none")
        return
    for index, container in enumerate(containers):
        color = palette[index % len(palette)]
        for patch in container.patches:
            patch.set_facecolor(color)
            patch.set_edgecolor("none")


def _recolor_lines(ax, palette: tuple[str, ...], has_bars: bool, figure_id: str) -> None:
    data_lines: list[Line2D] = []
    grid_ids = {id(line) for line in [*ax.get_xgridlines(), *ax.get_ygridlines()]}
    for line in ax.lines:
        if id(line) in grid_ids:
            continue
        # líneas guía (axhline/axvline) de gris institucional, no serie de datos
        label = str(line.get_label())
        if label.startswith("_") and len(line.get_xdata()) <= 2 and len(line.get_ydata()) <= 2:
            try:
                line.set_color(AXIS)
            except Exception:
                pass
            continue
        data_lines.append(line)
    start = 1 if has_bars and len(palette) > 1 else 0
    if figure_id == "A.1" and not has_bars and len(palette) > 1:
        start = 1
    for index, line in enumerate(data_lines):
        color = palette[(start + index) % len(palette)]
        line.set_color(color)
        try:
            line.set_markerfacecolor(color)
            line.set_markeredgecolor(color)
        except Exception:
            pass


def _recolor_collections(ax, palette: tuple[str, ...], has_bars: bool, has_lines: bool, figure_id: str) -> None:
    # PathCollections son principalmente scatter. PolyCollections de fill_between
    # se dejan con su alpha, pero alineados a la serie base.
    from matplotlib.collections import PathCollection, PolyCollection

    index = 1 if has_bars and len(palette) > 1 else 0
    if figure_id in {"A.8", "A.10"} and not has_bars and len(palette) > 1:
        index = 1
    if has_lines:
        index = min(index, len(palette) - 1)
    for collection in ax.collections:
        if isinstance(collection, PathCollection):
            color = palette[index % len(palette)]
            collection.set_facecolor(color)
            collection.set_edgecolor(color)
            index += 1
        elif isinstance(collection, PolyCollection):
            # No tocar colecciones de polígonos de mapas: suelen tener muchos paths.
            try:
                if len(collection.get_paths()) <= 2:
                    color = palette[0]
                    collection.set_facecolor(mcolors.to_rgba(color, .20))
            except Exception:
                pass


def _recolor_wedges(ax, palette: tuple[str, ...]) -> None:
    wedges = [patch for patch in ax.patches if isinstance(patch, mpatches.Wedge)]
    for index, wedge in enumerate(wedges):
        wedge.set_facecolor(palette[index % len(palette)])
        wedge.set_edgecolor("white")


def _square_data_fancy_patches(ax, palette: tuple[str, ...], figure_id: str) -> None:
    if figure_id not in RECTANGULAR_BAR_IDS:
        return
    candidates = [patch for patch in ax.patches if isinstance(patch, mpatches.FancyBboxPatch)]
    for index, patch in enumerate(candidates):
        # Los chips de texto no viven en ax.patches; aquí los FancyBboxPatch suelen
        # ser las barras hechas a mano del rediseño 2026.
        try:
            patch.set_boxstyle("square,pad=0")
            patch.set_facecolor(palette[index % len(palette)])
            patch.set_edgecolor("none")
        except Exception:
            continue


def _clean_rounded_figure_panels(fig: Figure, figure_id: str) -> None:
    # El 2026 añadió una tarjeta redondeada casi a página completa en muchas
    # figuras. No existe en el 2024. Se ocultan únicamente esas tarjetas grandes.
    if figure_id in KEEP_SPECIAL_BACKGROUNDS:
        return
    for artist in list(fig.artists):
        if not isinstance(artist, mpatches.FancyBboxPatch):
            continue
        try:
            width, height = float(artist.get_width()), float(artist.get_height())
            x, y = float(artist.get_x()), float(artist.get_y())
        except Exception:
            continue
        if width >= .70 and height >= .55:
            artist.set_visible(False)
        elif y >= .84 and width <= .025 and height <= .035:
            # marcador editorial junto al título: cuadrado verde, no píldora coral
            artist.set_boxstyle("square,pad=0")
            artist.set_facecolor(TITLE_MARKER)
            artist.set_edgecolor("none")


def _fix_title_markers(fig: Figure) -> None:
    texts = list(fig.texts)
    for ax in fig.axes:
        texts.extend(ax.texts)
    for text in texts:
        raw = text.get_text().strip()
        x, y = text.get_position()
        # Marcadores representados como glifo en la banda superior.
        if raw in {"•", "●", "▪", "■"}:
            if (text.axes is None and y >= .82 and x <= .10) or (text.axes is not None and y >= .82 and x <= .15):
                text.set_text("■")
                text.set_color(TITLE_MARKER)
                text.set_fontsize(min(float(text.get_fontsize()), 13.0))
        # Algunos scripts usan un texto vacío con bbox como pseudo-cuadrado.
        if not raw:
            patch = text.get_bbox_patch()
            if patch is not None and ((text.axes is None and y >= .82) or (text.axes is not None and y >= .82)):
                try:
                    patch.set_boxstyle("square,pad=0.35")
                    patch.set_facecolor(TITLE_MARKER)
                    patch.set_edgecolor("none")
                except Exception:
                    pass



def _copy_artist_color(source, target) -> None:
    """Sincroniza el color de una muestra de leyenda con su artista real."""
    try:
        if isinstance(source, BarContainer):
            source = source.patches[0] if source.patches else source
        if isinstance(source, mpatches.Patch) and isinstance(target, mpatches.Patch):
            target.set_facecolor(source.get_facecolor())
            target.set_edgecolor(source.get_edgecolor())
            return
        if isinstance(source, Line2D) and isinstance(target, Line2D):
            target.set_color(source.get_color())
            target.set_markerfacecolor(source.get_markerfacecolor())
            target.set_markeredgecolor(source.get_markeredgecolor())
            return
        if hasattr(source, "get_facecolor") and hasattr(target, "set_facecolor"):
            color = source.get_facecolor()
            if len(color):
                target.set_facecolor(color[0] if hasattr(color[0], "__len__") else color)
    except Exception:
        pass


def _style_legends(fig: Figure) -> None:
    """Alinea textos y muestras de leyenda con los artistas ya recoloreados."""
    label_to_source: dict[str, object] = {}
    for ax in fig.axes:
        try:
            handles, labels = ax.get_legend_handles_labels()
        except Exception:
            continue
        for handle, label in zip(handles, labels, strict=False):
            if label and not str(label).startswith("_"):
                label_to_source[str(label)] = handle

    legends = list(fig.legends)
    for ax in fig.axes:
        legend = ax.get_legend()
        if legend is not None and legend not in legends:
            legends.append(legend)

    for legend in legends:
        for text in legend.get_texts():
            _set_text_color(text)
        legend_handles = getattr(legend, "legend_handles", None)
        if legend_handles is None:
            legend_handles = getattr(legend, "legendHandles", [])
        for handle, text in zip(legend_handles, legend.get_texts(), strict=False):
            source = label_to_source.get(text.get_text())
            if source is not None:
                _copy_artist_color(source, handle)

def _style_numeric_chips(fig: Figure, palette: tuple[str, ...]) -> None:
    edge = palette[-1] if palette else TITLE_MARKER
    texts = list(fig.texts)
    for ax in fig.axes:
        texts.extend(ax.texts)
    for text in texts:
        patch = text.get_bbox_patch()
        if patch is None:
            continue
        raw = text.get_text().strip()
        if not any(char.isdigit() for char in raw):
            continue
        # Mantener chips sólo donde ya existen. Se cambia apariencia, no se crean.
        try:
            patch.set_boxstyle("round,pad=0.35,rounding_size=0.25")
            patch.set_facecolor("white")
            patch.set_edgecolor(edge)
            patch.set_linewidth(.8)
            patch.set_alpha(.98)
            text.set_color(TEXT)
        except Exception:
            pass


def apply_reference_ui(fig: Figure, figure_id: str) -> None:
    """Replica el lenguaje visual 2024 sobre una figura 2026 ya calculada.

    Esta función es idempotente y deliberadamente no conoce ni altera los datos.
    """
    if figure_id == "F.3":
        return
    palette = PALETTES.get(figure_id, TEAL)
    fig.patch.set_facecolor("white")
    _clean_rounded_figure_panels(fig, figure_id)
    _fix_title_markers(fig)

    for text in fig.texts:
        _set_text_color(text)

    for ax in fig.axes:
        if figure_id not in KEEP_SPECIAL_BACKGROUNDS and ax.axison:
            ax.set_facecolor(AXES_BG)
        ax.tick_params(colors=TEXT)
        for label in [*ax.get_xticklabels(), *ax.get_yticklabels()]:
            _set_text_color(label)
        if ax.xaxis.label is not None:
            _set_text_color(ax.xaxis.label)
        if ax.yaxis.label is not None:
            _set_text_color(ax.yaxis.label)
        if ax.title is not None:
            _set_text_color(ax.title)
        for spine in ax.spines.values():
            if spine.get_visible():
                spine.set_color(AXIS)
        for line in [*ax.get_xgridlines(), *ax.get_ygridlines()]:
            line.set_color(GRID)
            line.set_linewidth(.8)

        bars = _bar_containers(ax)
        _recolor_bars(ax, palette, figure_id)
        _square_data_fancy_patches(ax, palette, figure_id)
        if figure_id in {"A.4", "A.6"}:
            for container in bars:
                for patch in container.patches:
                    # elimina clip paths usados únicamente para redondear extremos
                    patch.set_clip_path(None)
        if figure_id == "A.5":
            for line in ax.lines:
                try:
                    if line.get_linewidth() >= 5:
                        line.set_solid_capstyle("butt")
                except Exception:
                    pass
        _recolor_lines(ax, palette, bool(bars), figure_id)
        _recolor_collections(ax, palette, bool(bars), bool(ax.lines), figure_id)
        _recolor_wedges(ax, palette)
        for text in ax.texts:
            _set_text_color(text)

    _style_numeric_chips(fig, palette)
    _style_legends(fig)
