"""Generador PDF portátil, sin PowerPoint ni LibreOffice.

La presentación se construye directamente con las imágenes producidas por los
scripts de figuras. ReportLab y pypdf son dependencias Python puras, por lo que
el mismo flujo funciona en Windows, macOS y Linux.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PAGE_WIDTH = 720.0
PAGE_HEIGHT = 405.0
PAGE_SIZE = (PAGE_WIDTH, PAGE_HEIGHT)

BACKGROUND = "#F5F7F6"
DEEP_GREEN = "#06231F"
MID_GREEN = "#1D4A43"
ACCENT = "#82C9BC"
TEXT = "#253532"
MUTED = "#637873"
WHITE = "#FFFFFF"

DEFAULT_SECTIONS = {
    "A": "INDICADORES ECONÓMICOS",
    "B": "SERVICIOS FIJOS DE TELECOMUNICACIONES",
    "C": "SERVICIOS MÓVILES DE TELECOMUNICACIONES",
    "D": "TECNOLOGÍAS DE LA INFORMACIÓN Y COMUNICACIÓN (TIC)",
    "E": "PERSONAS USUARIAS DE SERVICIOS DE TELECOMUNICACIONES",
    "F": "INDICADORES CON PERSPECTIVA DE GÉNERO",
    "G": "INDICADORES DE RADIODIFUSIÓN",
    "H": "CONSUMO DE RADIO Y TELEVISIÓN",
}


class PdfDependencyUnavailable(RuntimeError):
    """Falta una dependencia Python declarada por el proyecto."""


@dataclass(frozen=True)
class PortablePdfFigure:
    figure_id: str
    title: str
    section: str
    image_path: Path


@dataclass(frozen=True)
class PortablePdfResult:
    output_path: Path
    page_count: int
    figure_count: int
    section_count: int


def _pdf_dependencies() -> dict[str, Any]:
    try:
        from pypdf import PdfReader
        from reportlab.lib.colors import HexColor
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas
        from reportlab.platypus import Paragraph
    except ImportError as exc:  # pragma: no cover - depende del entorno de instalación
        raise PdfDependencyUnavailable(
            "Faltan reportlab o pypdf. Ejecuta preparar_entorno.ps1 para instalar "
            "las dependencias del proyecto."
        ) from exc
    return {
        "PdfReader": PdfReader,
        "HexColor": HexColor,
        "TA_LEFT": TA_LEFT,
        "ParagraphStyle": ParagraphStyle,
        "ImageReader": ImageReader,
        "pdfmetrics": pdfmetrics,
        "TTFont": TTFont,
        "canvas": canvas,
        "Paragraph": Paragraph,
    }


def _catalog(project_root: Path) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    manifest_path = project_root / "assets" / "presentation" / (
        "anuario_estadistico_2026_manifest.json"
    )
    catalog: dict[str, dict[str, str]] = {}
    sections = dict(DEFAULT_SECTIONS)
    if not manifest_path.is_file():
        return catalog, sections

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    for section, title in payload.get("sections", {}).items():
        sections[str(section)] = str(title).removeprefix(f"{section}. ")
    for entry in payload.get("entries", []):
        figure_id = str(entry.get("figure_id", ""))
        if figure_id:
            catalog[figure_id] = {
                "title": str(entry.get("title") or f"Figura {figure_id}"),
                "section": str(entry.get("section") or figure_id.split(".", 1)[0]),
            }
    return catalog, sections


def figures_for_pdf(
    project_root: Path,
    rows: list[tuple[str, Path]],
) -> tuple[list[PortablePdfFigure], dict[str, str]]:
    catalog, sections = _catalog(project_root)
    figures: list[PortablePdfFigure] = []
    for figure_id, image_path in rows:
        metadata = catalog.get(figure_id, {})
        figures.append(
            PortablePdfFigure(
                figure_id=figure_id,
                title=metadata.get("title", f"Figura {figure_id}"),
                section=metadata.get("section", figure_id.split(".", 1)[0]),
                image_path=image_path,
            )
        )
    return figures, sections


def _register_fonts(project_root: Path, dependencies: dict[str, Any]) -> tuple[str, str]:
    pdfmetrics = dependencies["pdfmetrics"]
    TTFont = dependencies["TTFont"]
    font_dir = project_root / "assets" / "fonts" / "Noto_Sans"
    regular_path = font_dir / "NotoSans-Regular.ttf"
    bold_path = font_dir / "NotoSans-Bold.ttf"
    regular_name = "AnuarioNotoSans"
    bold_name = "AnuarioNotoSansBold"
    if regular_path.is_file() and bold_path.is_file():
        registered = set(pdfmetrics.getRegisteredFontNames())
        if regular_name not in registered:
            pdfmetrics.registerFont(TTFont(regular_name, str(regular_path)))
        if bold_name not in registered:
            pdfmetrics.registerFont(TTFont(bold_name, str(bold_path)))
        return regular_name, bold_name
    return "Helvetica", "Helvetica-Bold"


def _draw_paragraph(
    pdf,
    dependencies: dict[str, Any],
    text: str,
    *,
    x: float,
    top: float,
    width: float,
    height: float,
    font_name: str,
    font_size: float,
    leading: float,
    color: str,
) -> None:
    ParagraphStyle = dependencies["ParagraphStyle"]
    Paragraph = dependencies["Paragraph"]
    HexColor = dependencies["HexColor"]
    style = ParagraphStyle(
        name="AnuarioPdfParagraph",
        fontName=font_name,
        fontSize=font_size,
        leading=leading,
        textColor=HexColor(color),
        alignment=dependencies["TA_LEFT"],
        spaceAfter=0,
        spaceBefore=0,
    )
    paragraph = Paragraph(text, style)
    _, rendered_height = paragraph.wrap(width, height)
    paragraph.drawOn(pdf, x, top - rendered_height)


def _start_page(pdf, dependencies: dict[str, Any], color: str) -> None:
    pdf.setFillColor(dependencies["HexColor"](color))
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)


def _finish_page(pdf, page_number: int, regular_font: str, dependencies: dict[str, Any]) -> None:
    pdf.setFillColor(dependencies["HexColor"](MUTED))
    pdf.setFont(regular_font, 7.5)
    pdf.drawRightString(PAGE_WIDTH - 24, 14, str(page_number))
    pdf.showPage()


def _draw_cover(
    pdf,
    dependencies: dict[str, Any],
    run_id: str,
    figure_count: int,
    regular_font: str,
    bold_font: str,
) -> None:
    _start_page(pdf, dependencies, DEEP_GREEN)
    accent = dependencies["HexColor"](ACCENT)
    pdf.setFillColor(accent)
    pdf.roundRect(42, 310, 10, 46, 5, stroke=0, fill=1)
    pdf.setFont(bold_font, 34)
    pdf.drawString(68, 326, "Anuario Estadístico 2026")
    pdf.setFont(regular_font, 17)
    pdf.drawString(68, 294, "Presentación completa")
    pdf.setFillColor(dependencies["HexColor"]("#B8D5CF"))
    pdf.setFont(regular_font, 10)
    pdf.drawString(68, 254, f"Corrida: {run_id}")
    pdf.drawString(68, 236, f"Figuras incluidas: {figure_count}")
    pdf.setFillColor(dependencies["HexColor"]("#87A8A2"))
    pdf.setFont(regular_font, 8.5)
    pdf.drawString(68, 70, "PDF portátil generado directamente por el código del proyecto")
    pdf.drawString(68, 54, "No requiere Microsoft PowerPoint ni LibreOffice")
    pdf.bookmarkPage("portada")
    pdf.addOutlineEntry("Portada", "portada", level=0, closed=False)
    pdf.showPage()


def _draw_contents(
    pdf,
    dependencies: dict[str, Any],
    sections_in_run: list[tuple[str, str, int]],
    regular_font: str,
    bold_font: str,
) -> None:
    _start_page(pdf, dependencies, BACKGROUND)
    pdf.setFillColor(dependencies["HexColor"](TEXT))
    pdf.setFont(bold_font, 23)
    pdf.drawString(44, 346, "Contenido")
    pdf.setFont(regular_font, 9)
    pdf.setFillColor(dependencies["HexColor"](MUTED))
    pdf.drawString(44, 325, "Secciones incluidas en esta corrida")

    use_columns = len(sections_in_run) > 5
    rows_per_column = math.ceil(len(sections_in_run) / 2) if use_columns else len(
        sections_in_run
    )
    for index, (section, title, count) in enumerate(sections_in_run):
        column = index // rows_per_column if use_columns else 0
        row = index % rows_per_column if use_columns else index
        x = 44 + column * 338
        y = (280 - row * 62) if use_columns else (286 - row * 43)
        pdf.setFillColor(dependencies["HexColor"](MID_GREEN))
        pdf.roundRect(x, y - 3, 34, 28, 6, stroke=0, fill=1)
        pdf.setFillColor(dependencies["HexColor"](WHITE))
        pdf.setFont(bold_font, 12)
        pdf.drawCentredString(x + 17, y + 6, section)
        _draw_paragraph(
            pdf,
            dependencies,
            title,
            x=x + 48,
            top=y + 19,
            width=245 if use_columns else 560,
            height=27,
            font_name=bold_font,
            font_size=8.5 if use_columns else 10.5,
            leading=10 if use_columns else 12,
            color=TEXT,
        )
        pdf.setFillColor(dependencies["HexColor"](MUTED))
        pdf.setFont(regular_font, 8.5)
        suffix = "figura" if count == 1 else "figuras"
        pdf.drawString(x + 48, y - 8, f"{count} {suffix}")

    pdf.bookmarkPage("contenido")
    pdf.addOutlineEntry("Contenido", "contenido", level=0, closed=False)
    _finish_page(pdf, 2, regular_font, dependencies)


def _draw_introduction(
    pdf,
    dependencies: dict[str, Any],
    figure_count: int,
    section_count: int,
    regular_font: str,
    bold_font: str,
) -> None:
    _start_page(pdf, dependencies, WHITE)
    pdf.setFillColor(dependencies["HexColor"](ACCENT))
    pdf.roundRect(44, 330, 8, 34, 4, stroke=0, fill=1)
    pdf.setFillColor(dependencies["HexColor"](TEXT))
    pdf.setFont(bold_font, 23)
    pdf.drawString(66, 340, "Introducción")
    _draw_paragraph(
        pdf,
        dependencies,
        (
            "Esta presentación reúne las figuras generadas correctamente en la corrida "
            "seleccionada del Anuario Estadístico 2026. Cada gráfica procede de los scripts "
            "reproducibles del proyecto y conserva sus títulos, fuentes, notas y periodos."
        ),
        x=66,
        top=292,
        width=560,
        height=105,
        font_name=regular_font,
        font_size=12,
        leading=18,
        color=TEXT,
    )
    pdf.setFillColor(dependencies["HexColor"](BACKGROUND))
    pdf.roundRect(66, 115, 250, 70, 10, stroke=0, fill=1)
    pdf.roundRect(334, 115, 250, 70, 10, stroke=0, fill=1)
    pdf.setFillColor(dependencies["HexColor"](MID_GREEN))
    pdf.setFont(bold_font, 24)
    pdf.drawString(86, 145, str(figure_count))
    pdf.drawString(354, 145, str(section_count))
    pdf.setFillColor(dependencies["HexColor"](MUTED))
    pdf.setFont(regular_font, 9)
    pdf.drawString(128, 151, "figuras verificadas")
    pdf.drawString(396, 151, "secciones incluidas")
    pdf.bookmarkPage("introduccion")
    pdf.addOutlineEntry("Introducción", "introduccion", level=0, closed=False)
    _finish_page(pdf, 3, regular_font, dependencies)


def _draw_section_divider(
    pdf,
    dependencies: dict[str, Any],
    section: str,
    title: str,
    count: int,
    regular_font: str,
    bold_font: str,
    page_number: int,
) -> None:
    _start_page(pdf, dependencies, DEEP_GREEN)
    pdf.setFillColor(dependencies["HexColor"](ACCENT))
    pdf.setFont(bold_font, 72)
    pdf.drawString(48, 238, section)
    _draw_paragraph(
        pdf,
        dependencies,
        title,
        x=155,
        top=282,
        width=500,
        height=105,
        font_name=bold_font,
        font_size=24,
        leading=29,
        color=WHITE,
    )
    pdf.setFillColor(dependencies["HexColor"]("#9BBDB6"))
    pdf.setFont(regular_font, 10)
    suffix = "figura" if count == 1 else "figuras"
    pdf.drawString(158, 166, f"{count} {suffix} en esta sección")
    key = f"seccion_{section}"
    pdf.bookmarkPage(key)
    pdf.addOutlineEntry(f"{section}. {title}", key, level=0, closed=False)
    _finish_page(pdf, page_number, regular_font, dependencies)


def _draw_figure_page(
    pdf,
    dependencies: dict[str, Any],
    figure: PortablePdfFigure,
    regular_font: str,
    page_number: int,
) -> None:
    from PIL import Image

    _start_page(pdf, dependencies, WHITE)
    with Image.open(figure.image_path) as image:
        image_width, image_height = image.size
    scale = min(PAGE_WIDTH / image_width, PAGE_HEIGHT / image_height)
    width = image_width * scale
    height = image_height * scale
    x = (PAGE_WIDTH - width) / 2
    y = (PAGE_HEIGHT - height) / 2
    pdf.drawImage(
        dependencies["ImageReader"](str(figure.image_path)),
        x,
        y,
        width=width,
        height=height,
        preserveAspectRatio=True,
        anchor="c",
        mask="auto",
    )
    key = "figura_" + figure.figure_id.replace(".", "_")
    pdf.bookmarkPage(key)
    pdf.addOutlineEntry(
        f"Figura {figure.figure_id}. {figure.title}", key, level=1, closed=False
    )
    # Las figuras ya incluyen pie y numeración editorial. No se superpone el
    # número de página para evitar cubrir notas o fuentes.
    pdf.showPage()


def _draw_conclusion(
    pdf,
    dependencies: dict[str, Any],
    run_id: str,
    figure_count: int,
    regular_font: str,
    bold_font: str,
    page_number: int,
) -> None:
    _start_page(pdf, dependencies, BACKGROUND)
    pdf.setFillColor(dependencies["HexColor"](MID_GREEN))
    pdf.roundRect(44, 320, 8, 38, 4, stroke=0, fill=1)
    pdf.setFillColor(dependencies["HexColor"](TEXT))
    pdf.setFont(bold_font, 24)
    pdf.drawString(68, 333, "Presentación generada")
    figure_phrase = (
        "Se integró 1 figura verificada"
        if figure_count == 1
        else f"Se integraron {figure_count} figuras verificadas"
    )
    _draw_paragraph(
        pdf,
        dependencies,
        (
            f"{figure_phrase} de la corrida {run_id}. "
            "El documento fue construido de forma local y reproducible, sin automatización "
            "de aplicaciones de escritorio ni servicios externos."
        ),
        x=68,
        top=280,
        width=540,
        height=100,
        font_name=regular_font,
        font_size=12,
        leading=18,
        color=TEXT,
    )
    pdf.setFillColor(dependencies["HexColor"](MID_GREEN))
    pdf.roundRect(68, 92, 330, 48, 8, stroke=0, fill=1)
    pdf.setFillColor(dependencies["HexColor"](WHITE))
    pdf.setFont(bold_font, 10)
    pdf.drawString(88, 112, "Anuario Estadístico 2026 - exportación portátil")
    pdf.bookmarkPage("cierre")
    pdf.addOutlineEntry("Cierre", "cierre", level=0, closed=False)
    _finish_page(pdf, page_number, regular_font, dependencies)


def _validate_pdf(path: Path, expected_pages: int, dependencies: dict[str, Any]) -> None:
    if not path.is_file() or path.stat().st_size < 1024:
        raise RuntimeError(f"El generador no produjo un PDF válido: {path}")
    reader = dependencies["PdfReader"](str(path))
    if len(reader.pages) != expected_pages:
        raise RuntimeError(
            f"El PDF contiene {len(reader.pages)} páginas; se esperaban {expected_pages}."
        )
    for page in reader.pages:
        box = page.mediabox
        width = float(box.width)
        height = float(box.height)
        if abs(width - PAGE_WIDTH) > 0.5 or abs(height - PAGE_HEIGHT) > 0.5:
            raise RuntimeError(f"El PDF contiene una página con tamaño inesperado: {width}x{height}")


def create_portable_presentation_pdf(
    project_root: Path,
    run_id: str,
    figures: list[PortablePdfFigure],
    output_path: Path,
    *,
    section_titles: dict[str, str] | None = None,
) -> PortablePdfResult:
    """Crea y verifica una presentación PDF 16:9 completamente portátil."""
    if not figures:
        raise FileNotFoundError("La corrida no contiene figuras para integrar en el PDF.")
    for figure in figures:
        if not figure.image_path.is_file():
            raise FileNotFoundError(f"No existe la imagen de la figura {figure.figure_id}")

    dependencies = _pdf_dependencies()
    regular_font, bold_font = _register_fonts(project_root, dependencies)
    sections = section_titles or DEFAULT_SECTIONS
    grouped: dict[str, list[PortablePdfFigure]] = {}
    for figure in figures:
        grouped.setdefault(figure.section, []).append(figure)
    sections_in_run = [
        (section, sections.get(section, f"SECCIÓN {section}"), len(items))
        for section, items in grouped.items()
    ]

    expected_pages = 4 + len(grouped) + len(figures)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(output_path.stem + ".tmp.pdf")
    if temporary_path.exists():
        temporary_path.unlink()

    canvas_module = dependencies["canvas"]
    pdf = canvas_module.Canvas(
        str(temporary_path),
        pagesize=PAGE_SIZE,
        pageCompression=1,
    )
    pdf.setTitle("Anuario Estadístico 2026 - Presentación completa")
    pdf.setAuthor("Anuario Estadístico 2026")
    pdf.setCreator("Pipeline portátil Python - ReportLab")
    subject_label = "figura" if len(figures) == 1 else "figuras"
    pdf.setSubject(f"Corrida {run_id} - {len(figures)} {subject_label}")
    pdf.setKeywords("Anuario Estadístico 2026, CRT, presentación, figuras")

    page_number = 1
    _draw_cover(pdf, dependencies, run_id, len(figures), regular_font, bold_font)
    page_number += 1
    _draw_contents(pdf, dependencies, sections_in_run, regular_font, bold_font)
    page_number += 1
    _draw_introduction(
        pdf,
        dependencies,
        len(figures),
        len(grouped),
        regular_font,
        bold_font,
    )
    page_number += 1
    for section, title, count in sections_in_run:
        _draw_section_divider(
            pdf,
            dependencies,
            section,
            title,
            count,
            regular_font,
            bold_font,
            page_number,
        )
        page_number += 1
        for figure in grouped[section]:
            _draw_figure_page(
                pdf,
                dependencies,
                figure,
                regular_font,
                page_number,
            )
            page_number += 1
    _draw_conclusion(
        pdf,
        dependencies,
        run_id,
        len(figures),
        regular_font,
        bold_font,
        page_number,
    )
    pdf.save()

    try:
        _validate_pdf(temporary_path, expected_pages, dependencies)
        if output_path.exists():
            output_path.unlink()
        temporary_path.replace(output_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    sidecar = output_path.with_name(output_path.stem + "_pdf.json")
    sidecar.write_text(
        json.dumps(
            {
                "project": "Anuario Estadístico 2026",
                "run_id": run_id,
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "generator": "Python + ReportLab",
                "external_office_required": False,
                "page_size_points": [PAGE_WIDTH, PAGE_HEIGHT],
                "page_count": expected_pages,
                "figure_count": len(figures),
                "section_count": len(grouped),
                "figures": [
                    {
                        "figure_id": figure.figure_id,
                        "title": figure.title,
                        "section": figure.section,
                        "image_path": figure.image_path.relative_to(project_root).as_posix()
                        if figure.image_path.is_relative_to(project_root)
                        else str(figure.image_path),
                    }
                    for figure in figures
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return PortablePdfResult(
        output_path=output_path,
        page_count=expected_pages,
        figure_count=len(figures),
        section_count=len(grouped),
    )
