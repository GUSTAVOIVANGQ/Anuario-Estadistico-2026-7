"""Correcciones revisadas sobre la plantilla, antes de exportar la edición."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from pptx.enum.text import MSO_AUTO_SIZE
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from .editorial_statistics import calculate_highlights


REGISTRY = Path("assets/presentation/textos_editoriales_2026.json")


def load_publication_revision(root: Path) -> dict:
    path = root / REGISTRY
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("publication_revision", {})


def revision_fingerprint(root: Path) -> str | None:
    revision = load_publication_revision(root)
    if not revision:
        return None
    return hashlib.sha256(json.dumps(revision, ensure_ascii=False, sort_keys=True)
                          .encode("utf-8")).hexdigest()


def publication_page(number: int, omitted: list[int]) -> int:
    return number - sum(page < number for page in omitted)


def _shape(slide, name):
    return next(shape for shape in slide.shapes if shape.name == name)


def _replace_block(slide, names, value, *, top=None, height=None, source_font=None):
    """Reutiliza geometría, color y tipografía de las líneas de la plantilla."""
    originals = [_shape(slide, name) for name in names]
    first = originals[0]
    font = deepcopy(first.text_frame.paragraphs[0].runs[0]._r.rPr)
    original_top = min(s.top for s in originals)
    original_bottom = max(s.top + s.height for s in originals)
    first.top = Inches(top) if top is not None else original_top
    first.height = Inches(height) if height is not None else original_bottom - original_top
    for other in originals[1:]:
        slide.shapes._spTree.remove(other._element)
    frame = first.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.margin_top = frame.margin_bottom = 0
    frame.margin_left = frame.margin_right = 0
    for index, text in enumerate(value.split("\n\n")):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.space_before = Pt(0)
        paragraph.space_after = Pt(3) if index < len(value.split("\n\n")) - 1 else Pt(0)
        paragraph.line_spacing = 1.0
        for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
            if not part:
                continue
            run = paragraph.add_run()
            run._r.insert(0, deepcopy(source_font if source_font is not None and
                                     text.startswith("Fuente:") else font))
            run.text = part.strip("*")
            if part.startswith("**"):
                run.font.bold = True
            elif part.startswith("*"):
                run.font.italic = True


def _legal_copy(slide, sections):
    blocks = (
        ("fundamento", 2, 28, 1.22, 4.02),
        ("personas_usuarias", 32, 53, 0.97, 1.16),
        ("tic", 55, 65, 2.64, 1.00),
        ("genero", 67, 71, 4.146, 1.10),
        ("radio_tv", 73, 80, 0.97, 1.38),
        ("nielsen", 82, 99, 2.86, 2.38),
    )
    # Las tarjetas conservan sus colores y su ancho. Sólo se distribuye el
    # espacio entre columnas para acomodar el texto sin reducir la tipografía.
    for suffix, left, top, width, height in (
        ("USUARIOS", 2.722, 0.667, 3.389, 1.56),
        ("TIC", 2.722, 2.338, 3.389, 1.395),
        ("GENERO", 2.722, 3.844, 3.389, 1.489),
        ("RADIO_TV", 6.222, 0.667, 3.444, 1.78),
        ("NIELSEN", 6.222, 2.558, 3.444, 2.775),
    ):
        card = _shape(slide, "LEGALES_RECUADRO_" + suffix)
        accent = _shape(slide, "LEGALES_ACENTO_" + suffix)
        card.left, card.width = Inches(left), Inches(width)
        card.top, card.height = Inches(top), Inches(height)
        accent.left = Inches(left)
        accent.top, accent.height = Inches(top + 0.083), Inches(height - 0.166)
    for key, start, end, top, height in blocks:
        names = [f"LEGALES_TEXTO_{n}" for n in range(start, end + 1)]
        # La última línea depende de la versión de la plantilla.
        if key == "nielsen":
            names = [s.name for s in slide.shapes if s.name.startswith("LEGALES_TEXTO_")
                     and int(s.name.rsplit("_", 1)[1]) >= start]
        _replace_block(slide, names, sections[key]["body"], top=top, height=height)
        if key == "fundamento":
            _shape(slide, names[0]).width = Inches(1.832)
        if key == "genero":
            _shape(slide, names[0]).left = Inches(2.86)
    for key, serial, top in (
        ("personas_usuarias", 31, 0.763), ("tic", 54, 2.438),
        ("genero", 66, 3.944), ("radio_tv", 72, 0.763), ("nielsen", 81, 2.658),
    ):
        _replace_block(slide, [f"LEGALES_TEXTO_{serial}"], sections[key]["title"], top=top)
        if key == "genero":
            _shape(slide, f"LEGALES_TEXTO_{serial}").left = Inches(2.86)


def _replace_text(slide, old, new):
    # Una denominación puede estar repartida entre runs con distintas negritas.
    # Reemplazar sólo a:t completos dejaría referencias parcialmente actualizadas.
    for paragraph in slide._element.xpath(".//a:p"):
        nodes = paragraph.xpath(".//a:t")
        offsets = []
        text = ""
        for node in nodes:
            offsets.append(len(text))
            text += node.text or ""
        for match in reversed(list(re.finditer(re.escape(old), text))):
            first = next(i for i, n in enumerate(nodes)
                         if offsets[i] <= match.start() < offsets[i] + len(n.text or ""))
            last = next(i for i, n in enumerate(nodes)
                        if offsets[i] < match.end() <= offsets[i] + len(n.text or ""))
            prefix = (nodes[first].text or "")[:match.start() - offsets[first]]
            suffix = (nodes[last].text or "")[match.end() - offsets[last]:]
            nodes[first].text = prefix + new + (suffix if first == last else "")
            if first != last:
                for node in nodes[first + 1:last]:
                    node.text = ""
                nodes[last].text = suffix


def _introduction_copy(presentation, revision):
    intro = revision.get("introduction")
    if intro:
        slide = presentation.slides[6]
        _replace_block(slide, [f"INTRO_TEXTO_{n}" for n in range(4, 29)],
                       intro["body"], top=1.22, height=4.02)
        _shape(slide, "INTRO_TEXTO_4").width = Inches(1.832)
    notes = revision.get("introduction_notes", [])
    slide = presentation.slides[7]
    for index, item in enumerate(notes, 2):
        names = [s.name for s in slide.shapes if s.name.startswith(f"INTRO8_NOTA_{index}_")]
        top, height = {2: (3.694, 0.25), 3: (3.994, 0.33),
                       4: (4.384, 0.31), 5: (4.764, 0.48)}[index]
        _replace_block(slide, names, item["body"], top=top, height=height)
        labels = [s for s in slide.shapes if s.name.startswith(f"INTRO8_ROTULO_{index}_")]
        label_top = min(s.top for s in labels)
        for shape in labels:
            shape.top = Inches(top) + shape.top - label_top
        if item["title"] == "Consulta interactiva":
            paragraph = _shape(slide, names[0]).text_frame.paragraphs[0]
            original = paragraph.runs[0]
            properties = deepcopy(original._r.rPr)
            url = "https://bit.crt.gob.mx/BitWebApp/PortalBIT.xhtml?view="
            prefix, suffix = original.text.split(url, 1)
            original.text = prefix
            for text in (url, suffix):
                run = paragraph.add_run()
                run._r.insert(0, deepcopy(properties))
                run.text = text
                if text == url:
                    run.font.color.rgb = RGBColor(41, 107, 140)
                    run.font.underline = True
            # El enlace en el objeto conserva el color explícito del texto,
            # evitando el blanco que impone el tema a los hyperlinks de runs.
            _shape(slide, names[0]).click_action.hyperlink.address = url


def _economic_copy(presentation, highlights):
    slide = presentation.slides[8]
    for key, name in (("income", "TextBox 14"), ("gdp", "TextBox 17")):
        if key not in highlights:
            continue
        shape = _shape(slide, name)
        source_font = deepcopy(shape.text_frame.paragraphs[1].runs[0]._r.rPr)
        _replace_block(slide, [name], highlights[key]["text"], source_font=source_font)
        slide.notes_slide.notes_text_frame.text += "\n" + highlights[key]["source_url"]


def apply_publication_revision(root: Path, presentation, run_dir: Path | None = None) -> dict:
    revision = load_publication_revision(root)
    if not revision:
        return {}
    _legal_copy(presentation.slides[2], revision["legal_sections"])
    glossary = presentation.slides[4]
    _replace_block(glossary, ["GLOSARIO_left_2_1", "GLOSARIO_left_2_2"],
                   revision["gemini_definition"])
    # Conserva la negrita del acrónimo y el cuerpo de su definición.
    gemini = _shape(glossary, "GLOSARIO_left_2_1").text_frame.paragraphs[0]
    gemini.runs[0].font.bold = False
    definition = gemini.runs[0].text
    gemini.runs[0].text = "GEMINI:"
    gemini.runs[0].font.bold = True
    run = gemini.add_run()
    run._r.insert(0, deepcopy(gemini.runs[0]._r.rPr))
    run.text = definition[len("GEMINI:"):]
    run.font.bold = False
    for slide in presentation.slides:
        _replace_text(slide, "Coordinación General de Planeación Estratégica", "Dirección General de Planeación")
        _replace_text(slide, "CGPE", "DGP")
    _replace_block(glossary, ["GLOSARIO_left_8_1"], "DGP: Dirección General de Planeación")
    paragraph = _shape(glossary, "GLOSARIO_left_8_1").text_frame.paragraphs[0]
    paragraph.runs[0].text = "DGP:"
    paragraph.runs[0].font.bold = True
    run = paragraph.add_run()
    run._r.insert(0, deepcopy(paragraph.runs[0]._r.rPr))
    run.text, run.font.bold = " Dirección General de Planeación", False
    intro = presentation.slides[6]
    for name, text in (
        ("INTRO_TEXTO_15", "federativa. Con ello la CRT, a"),
        ("INTRO_TEXTO_16", "través de la Dirección General"),
        ("INTRO_TEXTO_17", "de Planeación (DGP)"),
    ):
        _replace_block(intro, [name], text)
    glossary.notes_slide.notes_text_frame.text += "\n" + revision["gemini_source"]
    _introduction_copy(presentation, revision)
    highlights = calculate_highlights(root, revision, run_dir)
    _economic_copy(presentation, highlights)

    omitted = sorted(set(revision.get("omitted_template_pages", [])))
    original_count = len(presentation.slides)
    page_map = {n: publication_page(n, omitted) for n in range(1, original_count + 1)
                if n not in omitted}
    index = presentation.slides[1]
    for shape in index.shapes:
        if not shape.has_text_frame or shape.name == "ANUARIO_PAGE_NUMBER":
            continue
        for node in shape._element.xpath(".//a:t"):
            if not node.text:
                continue
            # Índice editable y líneas extraídas del PDF histórico.
            if shape.name.startswith("ANUARIO_REFERENCIA_2024_P2_") and node.text.strip().isdigit():
                old = int(node.text.strip())
                node.text = str(page_map.get(old, publication_page(old, omitted)))
            else:
                node.text = re.sub(r"(·\s+)(\d+)(?=\s*$)",
                                   lambda m: m[1] + str(publication_page(int(m[2]), omitted)),
                                   node.text)
    for number in reversed(omitted):
        slide_id = presentation.slides._sldIdLst[number - 1]
        presentation.part.drop_rel(slide_id.rId)
        presentation.slides._sldIdLst.remove(slide_id)
    presentation.part.rename_slide_parts([s.rId for s in presentation.slides._sldIdLst])
    for number, slide in enumerate(presentation.slides, 1):
        for shape in slide.shapes:
            if shape.has_text_frame and (shape.name == "ANUARIO_PAGE_NUMBER" or
                                        (shape.top > Inches(5.4) and shape.text.strip().isdigit())):
                nodes = shape._element.xpath(".//a:t")
                if nodes:
                    nodes[0].text = str(number)
    return {"version": revision["version"], "fingerprint": revision_fingerprint(root),
            "economic_highlights": highlights,
            "omitted_template_pages": omitted,
            "template_to_publication_pages": {str(k): v for k, v in page_map.items()}}
