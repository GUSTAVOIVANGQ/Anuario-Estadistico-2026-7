"""Salidas reproducibles de figuras, con SVG como artefacto maestro de entrega.

Los scripts históricos siguen llamando a ``Figure.savefig`` con una ruta PNG para
no romper su contrato. Este adaptador aprovecha el objeto Matplotlib todavía vivo
para emitir, en la misma llamada, un SVG nativo de alta calidad y un JPG de
conveniencia. El PPTX y el PDF usan exclusivamente el SVG de cada figura.

El SVG se genera con texto real (``<text>``), sin rasterización silenciosa, sin
simplificación de trazos y con lienzo transparente. Después de escribirlo se
valida de inmediato: si una figura introduce una imagen raster, convierte el
texto en curvas o conserva un fondo opaco, la corrida falla en vez de degradar
la entrega sin avisar.
"""

from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import matplotlib as mpl
from matplotlib.figure import Figure
from PIL import Image


VECTOR_ELEMENTS = {
    "circle",
    "ellipse",
    "line",
    "path",
    "polygon",
    "polyline",
    "rect",
    "use",
}

SVG_RASTER_DPI = 600

_exporter_installed = False


@dataclass(frozen=True)
class SvgInspection:
    """Resumen verificable de qué tan editable es un SVG."""

    text_elements: int
    positioned_text_elements: int
    vector_elements: int
    embedded_images: int
    opaque_canvas_background: bool

    @property
    def editable_text(self) -> bool:
        return self.text_elements > 0 and self.positioned_text_elements == self.text_elements

    @property
    def fully_vector(self) -> bool:
        return self.embedded_images == 0

    @property
    def transparent_background(self) -> bool:
        return not self.opaque_canvas_background


def companion_paths(png_path: Path) -> dict[str, Path]:
    """Devuelve las tres rutas canónicas de una figura."""
    return {
        "png": png_path,
        "jpg": png_path.with_suffix(".jpg"),
        "svg": png_path.with_suffix(".svg"),
    }


def _saved_path(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Path | None:
    target = args[0] if args else kwargs.get("fname")
    if not isinstance(target, (str, PathLike)):
        return None
    path = Path(target)
    requested_format = str(kwargs.get("format") or path.suffix.lstrip(".")).lower()
    if requested_format != "png" or path.suffix.lower() != ".png":
        return None
    return path


def _svg_metadata(figure: Figure, target: Path) -> dict[str, str]:
    visible_text = [
        item.get_text().strip()
        for item in figure.findobj()
        if hasattr(item, "get_text")
        and hasattr(item, "get_visible")
        and item.get_visible()
        and isinstance(item.get_text(), str)
        and item.get_text().strip()
    ]
    title = next((text for text in visible_text if text.startswith("Figura ")), target.stem)
    return {
        "Title": title,
        "Description": (
            "Figura vectorial editable del Anuario Estadístico 2026. "
            "Los textos se conservan como texto seleccionable."
        ),
        "Creator": "Anuario Estadístico 2026 (Matplotlib)",
    }


def _companion_kwargs(
    figure: Figure,
    target: Path,
    original: dict[str, Any],
    kind: str,
) -> dict[str, Any]:
    options = dict(original)
    options.pop("backend", None)
    options.pop("format", None)
    options.pop("metadata", None)
    options.pop("pil_kwargs", None)

    if kind == "svg":
        options["format"] = "svg"
        options["metadata"] = _svg_metadata(figure, target)
        # ``dpi`` no afecta a los trazos vectoriales, pero sí a cualquier
        # artista que Matplotlib intentara rasterizar. Se fija alto y, además,
        # la validación posterior rechaza cualquier <image> en el SVG final.
        options["dpi"] = SVG_RASTER_DPI
        # El fondo de la diapositiva o de su tarjeta debe verse a través del
        # lienzo. Los parches añadidos explícitamente por una figura se
        # conservan, pero los parches automáticos de Figure/Axes no se pintan.
        options["transparent"] = True
        options["facecolor"] = "none"
        options["edgecolor"] = "none"
    elif kind == "jpg":
        options["format"] = "jpeg"
        options["transparent"] = False
        options["pil_kwargs"] = {"quality": 95, "optimize": True, "progressive": True}
    else:  # pragma: no cover - protección para futuros usos internos
        raise ValueError(f"Formato complementario desconocido: {kind}")
    return options


def install_figure_output_exporter() -> None:
    """Hace que todo PNG de figura genere también JPG y SVG editables.

    Debe instalarse después de los normalizadores visuales del pipeline. Es
    idempotente incluso si otro adaptador envuelve ``Figure.savefig`` después.
    """
    global _exporter_installed
    if _exporter_installed:
        return

    original_savefig = Figure.savefig

    def savefig(self, *args, **kwargs):
        png_path = _saved_path(args, kwargs)
        result = original_savefig(self, *args, **kwargs)
        if png_path is None:
            return result

        png_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path = png_path.with_suffix(".svg")
        jpg_path = png_path.with_suffix(".jpg")

        svg_options = _companion_kwargs(self, svg_path, kwargs, "svg")
        # ``none`` es la clave para conservar texto real. El valor predeterminado
        # de Matplotlib (``path``) convertiría cada letra en curvas no copiables.
        with mpl.rc_context(
            {
                "svg.fonttype": "none",
                "svg.image_inline": True,
                "svg.hashsalt": "anuario-estadistico-2026",
                # Evita perder detalle geométrico en líneas, mapas y contornos.
                "path.simplify": False,
                "agg.path.chunksize": 0,
                # Impide que Matplotlib combine artistas de imagen en un raster
                # compuesto. La entrega estricta rechaza cualquier raster de
                # todos modos, pero esta opción evita crear uno innecesario.
                "image.composite_image": False,
            }
        ):
            original_savefig(self, svg_path, **svg_options)

        # El SVG es el artefacto maestro para PPTX/PDF: no se acepta degradación
        # silenciosa a imagen, texto en curvas ni fondo de lienzo opaco.
        validate_editable_svg(svg_path, require_fully_vector=True)

        jpg_options = _companion_kwargs(self, jpg_path, kwargs, "jpg")
        original_savefig(self, jpg_path, **jpg_options)
        return result

    # Conserva las marcas de adaptadores ya instalados para que el orden de
    # importación no provoque dobles envolturas.
    for attribute in ("_anuario_title_marker_normalizer",):
        if getattr(original_savefig, attribute, False):
            setattr(savefig, attribute, True)
    savefig._anuario_figure_output_exporter = True
    Figure.savefig = savefig
    _exporter_installed = True


def inspect_svg(path: Path) -> SvgInspection:
    """Cuenta texto posicionado, vectores e imágenes raster dentro del SVG."""
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        raise ValueError(f"SVG inválido: {path}") from exc

    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError(f"El archivo no tiene una raíz SVG: {path}")

    text_elements = 0
    positioned_text_elements = 0
    vector_elements = 0
    embedded_images = 0
    opaque_canvas_background = False
    for element in root.iter():
        name = element.tag.rsplit("}", 1)[-1]
        if name == "text" and "".join(element.itertext()).strip():
            text_elements += 1
            if element.get("transform") or element.get("x") or element.get("y"):
                positioned_text_elements += 1
        elif name == "image":
            embedded_images += 1
        elif name in VECTOR_ELEMENTS:
            vector_elements += 1

        # Matplotlib identifica el parche automático del lienzo como
        # ``patch_1``. Si conserva un relleno opaco, el SVG todavía trae un
        # rectángulo de fondo aunque todo el contenido sea vectorial.
        if name == "g" and element.get("id") == "patch_1":
            for child in element.iter():
                child_name = child.tag.rsplit("}", 1)[-1]
                if child_name not in {"path", "rect"}:
                    continue
                style = {
                    key.strip(): value.strip().lower()
                    for declaration in child.get("style", "").split(";")
                    if ":" in declaration
                    for key, value in [declaration.split(":", 1)]
                }
                fill = str(child.get("fill") or style.get("fill") or "").lower()
                opacity = str(
                    child.get("fill-opacity")
                    or style.get("fill-opacity")
                    or child.get("opacity")
                    or style.get("opacity")
                    or "1"
                ).lower()
                if fill not in {"", "none", "transparent"} and opacity not in {
                    "0",
                    "0.0",
                    "0%",
                }:
                    opaque_canvas_background = True
                    break

    return SvgInspection(
        text_elements=text_elements,
        positioned_text_elements=positioned_text_elements,
        vector_elements=vector_elements,
        embedded_images=embedded_images,
        opaque_canvas_background=opaque_canvas_background,
    )


def extract_svg_text(path: Path) -> tuple[str, ...]:
    """Extrae el texto visible del SVG en el orden del documento."""
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        raise ValueError(f"SVG inválido: {path}") from exc
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError(f"El archivo no tiene una raíz SVG: {path}")

    texts: list[str] = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "text":
            continue
        content = " ".join("".join(element.itertext()).split())
        if content:
            texts.append(content)
    return tuple(texts)


def validate_editable_svg(
    path: Path,
    *,
    require_fully_vector: bool = True,
) -> SvgInspection:
    if not path.is_file():
        raise FileNotFoundError(f"La figura no generó su SVG nativo: {path}")
    inspection = inspect_svg(path)
    if not inspection.text_elements:
        raise ValueError(f"El SVG no conserva texto seleccionable: {path}")
    if not inspection.editable_text:
        raise ValueError(f"El SVG contiene texto sin posición explícita: {path}")
    if not inspection.vector_elements:
        raise ValueError(f"El SVG no contiene elementos vectoriales: {path}")
    if require_fully_vector and not inspection.fully_vector:
        raise ValueError(
            f"El SVG contiene {inspection.embedded_images} imagen(es) raster incrustada(s): "
            f"{path}"
        )
    if not inspection.transparent_background:
        raise ValueError(f"El SVG conserva un fondo de lienzo opaco: {path}")
    return inspection


def validate_jpg(path: Path, *, expected_size: tuple[int, int] | None = None) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"La figura no generó su JPG: {path}")
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        if image.format != "JPEG":
            raise ValueError(f"La salida no es un JPG válido: {path}")
        if expected_size is not None and image.size != expected_size:
            raise ValueError(
                f"El JPG no conserva las dimensiones del PNG: {image.size} != {expected_size}"
            )


def validate_figure_bundle(png_path: Path) -> SvgInspection:
    """Verifica que las tres salidas de código existan y sean coherentes."""
    if not png_path.is_file():
        raise FileNotFoundError(f"La figura no generó el archivo esperado: {png_path}")
    with Image.open(png_path) as image:
        image.verify()
    with Image.open(png_path) as image:
        png_size = image.size

    paths = companion_paths(png_path)
    validate_jpg(paths["jpg"], expected_size=png_size)
    return validate_editable_svg(paths["svg"])
