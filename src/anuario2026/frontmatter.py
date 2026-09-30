"""Reproduce el texto y la tipografía de las páginas preliminares de 2024.

Las diapositivas 2–10 conservan el fondo de la plantilla 2026. El contenido
editorial se toma línea por línea del PDF de referencia para evitar resúmenes,
omisiones y pérdida de negritas o cursivas. Las líneas siguen siendo texto
nativo y editable en PowerPoint.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE, MSO_VERTICAL_ANCHOR
from pptx.util import Inches, Pt


DESIGNED_FRONTMATTER_SHAPES = {
    3: "ANUARIO_LEGALES_DESIGN_2026",
    4: "ANUARIO_LEGALES_CONT_DESIGN_2026",
    5: "ANUARIO_GLOSARIO_DESIGN_2026",
    6: "ANUARIO_GLOSARIO_CONT_DESIGN_2026",
    7: "ANUARIO_INTRO_DESIGN_2026",
    8: "ANUARIO_INTRO_CONT_DESIGN_2026",
}


def _body_line(block: dict, page_number: int) -> bool:
    """Descarta solamente el encabezado y pie propios del PDF 2024."""
    x0, y0, _x1, y1 = block["bbox"]
    if y0 < 55 or y0 > 855 or y1 > 858:
        return False
    text = "".join(
        span["text"] for line in block.get("lines", []) for span in line["spans"]
    ).strip()
    if not text:
        return False
    if page_number == 2 and x0 < 450 and text == "ÍNDICE":
        return False
    if page_number in (3, 5, 7, 9) and x0 < 450 and text in {
        "LEGALES", "GLOSARIO", "INTRODUCCIÓN", "PUNTOS CLAVE"
    }:
        return False
    if page_number == 5 and text in {"A", "B"}:
        return False
    return True


def _source_lines(page, page_number: int):
    for block in page.get_text("dict")["blocks"]:
        if "lines" not in block or not _body_line(block, page_number):
            continue
        for line in block["lines"]:
            spans = [span for span in line["spans"] if span["text"].strip()]
            if spans:
                yield line, spans


def _colour(source: int) -> RGBColor:
    # Algunos rótulos blancos del original estaban sobre tarjetas de color.
    # En el fondo blanco del Anuario 2026 se imprimen en verde oscuro.
    if source >= 0xE8E8E8:
        return RGBColor(26, 64, 61)
    if source == 0:
        return RGBColor(28, 40, 41)
    return RGBColor((source >> 16) & 255, (source >> 8) & 255, source & 255)


def _add_line(slide, line: dict, spans: list[dict], page_number: int, serial: int) -> None:
    x0, y0, x1, y1 = line["bbox"]
    # El diseño 2026 deja libres 0,64–5,11 pulgadas entre encabezado y pie.
    # El cuerpo 2024 ocupa aproximadamente los puntos y=60–850.
    scale_x = 9.12 / 1480
    scale_y = 4.43 / 790
    left = 0.41 + (x0 - 60) * scale_x
    top = 0.65 + (y0 - 60) * scale_y
    font_scale = 0.43
    if page_number == 2:
        # El índice original dejaba un tercio de la página para el icono.
        # En la portada oscura de 2026 ambos listados ocupan el ancho útil.
        left = (0.55 + (x0 - 474) * 0.0067) if x0 < 1000 else (5.16 + (x0 - 1033) * 0.0067)
        top = 1.26 + (y0 - 106) * (3.35 / 690)
        scale_x = 0.0067
        scale_y = 3.35 / 690
        font_scale = 0.50
    elif page_number in (5, 6) and x0 >= 470:
        left = (0.54 + (x0 - 474) * 0.0080) if x0 < 1000 else (5.10 + (x0 - 1013) * 0.0080)
        top = 0.88 + (y0 - 90) * (4.08 / 720)
        scale_x = 0.0080
        scale_y = 4.08 / 720
        font_scale = 0.49
    elif page_number == 9 and x0 < 800 and 180 <= y0 < 650:
        top -= 0.38
    width = max(0.15, (x1 - x0) * scale_x + 0.10)
    height = max(0.12, (y1 - y0) * scale_y + 0.04)
    # Un poco de holgura evita cortes en visores con métricas diferentes.
    width = min(9.55 - left, width)
    shape = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    shape.name = f"ANUARIO_REFERENCIA_2024_P{page_number}_L{serial:03d}"
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = False
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.vertical_anchor = MSO_VERTICAL_ANCHOR.TOP
    frame.margin_left = frame.margin_right = 0
    frame.margin_top = frame.margin_bottom = 0
    paragraph = frame.paragraphs[0]
    paragraph.space_before = Pt(0)
    paragraph.space_after = Pt(0)
    for span in spans:
        run = paragraph.add_run()
        run.text = (
            span["text"]
            .replace("\ufb01", "fi")
            .replace("\ufb02", "fl")
            .replace("\x08", "")
        )
        font = run.font
        font.name = "Noto Sans"
        font.size = Pt(round(span["size"] * font_scale, 2))
        font.bold = bool(span["flags"] & 16)
        font.italic = bool(span["flags"] & 2)
        font.color.rgb = (
            RGBColor(239, 243, 239) if page_number == 2 and span["color"] != 0xEB595B
            else RGBColor(241, 194, 123) if page_number == 2
            else _colour(span["color"])
        )


def apply_reference_frontmatter(project_root: Path, presentation) -> None:
    """Sustituye los resúmenes preliminares por el texto íntegro de 2024."""
    source = project_root / "anuarioestadistico2024vf_0.pdf"
    if not source.is_file():
        source = (
            project_root / "assets" / "reference" / "anuario_2024_fuente"
            / "anuarioestadistico2024vf_0.pdf"
        )
    if not source.is_file():
        raise FileNotFoundError(f"Falta el anuario de referencia 2024: {source}")
    with pymupdf.open(source) as document:
        for page_number in range(2, 11):
            slide = presentation.slides[page_number - 1]
            # Conserva las páginas diseñadas como elementos editables en la plantilla.
            design_shape = DESIGNED_FRONTMATTER_SHAPES.get(page_number)
            if design_shape and any(
                shape.name == design_shape for shape in slide.shapes
            ):
                continue
            for shape in list(slide.shapes):
                if shape.name.startswith("ANUARIO_HEADER_") or shape.name == "ANUARIO_PAGE_NUMBER":
                    continue
                if page_number == 2 and shape.name == "ANUARIO_INDEX_TITLE":
                    continue
                slide.shapes._spTree.remove(shape._element)
            for serial, (line, spans) in enumerate(
                _source_lines(document[page_number - 1], page_number), start=1
            ):
                _add_line(slide, line, spans, page_number, serial)
            # Enlace general actualizado. Los vínculos a estudios y herramientas
            # citados dentro de pasajes de 2024 conservan su carácter histórico.
            link = slide.shapes.add_textbox(
                Inches(5.45), Inches(0.42), Inches(4.18), Inches(0.14)
            )
            link.name = "ANUARIO_ENLACE_BIT_CRT"
            link.text = "BIT CRT: https://bit.crt.gob.mx/BitWebApp/"
            link.text_frame.margin_left = link.text_frame.margin_right = 0
            link.text_frame.margin_top = link.text_frame.margin_bottom = 0
            for run in link.text_frame.paragraphs[0].runs:
                run.font.name = "Noto Sans"
                run.font.size = Pt(6.1)
                run.font.color.rgb = RGBColor(239, 243, 239)
                run.hyperlink.address = "https://bit.crt.gob.mx/BitWebApp/"
