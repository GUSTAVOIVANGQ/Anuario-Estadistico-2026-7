"""Exportación PDF con composición directa de los SVG originales.

El PPTX de entrega se mantiene intacto. Para crear el PDF se genera una copia
*temporal* del PPTX sin las figuras ``ANUARIO_IMAGE_*`` ni las capas auxiliares
``ANUARIO_TEXT_LAYER_*`` y esa copia se usa solamente como base visual para los
fondos, títulos, narrativas y demás elementos de la presentación.

Después, cada SVG original de ``build/figures`` se convierte directamente a un
fragmento PDF vectorial con CairoSVG y se coloca en la página correspondiente,
en exactamente la misma caja que ocupa en el PPTX. No se crea un SVG alterno,
no se rasteriza la figura y no se depende de cómo PowerPoint o LibreOffice
interpreten el texto del SVG. El texto ``<text>`` del SVG queda seleccionable y
copiable en el PDF final.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter
from pptx import Presentation

from .figure_outputs import validate_editable_svg


CONVERSION_TIMEOUT_SECONDS = 900
PDF_EXPORT_SCHEMA_VERSION = 6
EMU_PER_POINT = 12_700.0


class PdfConverterUnavailable(RuntimeError):
    """No hay un motor instalado capaz de renderizar la base del PPTX."""


class PdfConversionError(RuntimeError):
    """No se logró producir un PDF válido y verificable."""


@dataclass(frozen=True)
class ConverterBackend:
    name: str
    executable: Path | None = None


@dataclass(frozen=True)
class PresentationPdfResult:
    output_path: Path
    source_pptx: Path
    converter: str
    slide_count: int
    page_count: int
    reused: bool = False


@dataclass(frozen=True)
class OriginalSvgPlacement:
    figure_id: str
    slide_index: int
    svg_path: Path
    left_emu: int
    top_emu: int
    width_emu: int
    height_emu: int
    sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _powerpoint_available() -> bool:
    if os.name != "nt" or not (shutil.which("powershell.exe") or shutil.which("powershell")):
        return False
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"PowerPoint.Application\CLSID"):
            return True
    except (FileNotFoundError, OSError):
        return any(
            candidate.is_file()
            for candidate in (
                Path(r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"),
                Path(r"C:\Program Files (x86)\Microsoft Office\root\Office16\POWERPNT.EXE"),
            )
        )


def _find_soffice() -> Path | None:
    configured = os.environ.get("ANUARIO_SOFFICE")
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_file():
            return candidate.resolve()

    discovered = shutil.which("soffice") or shutil.which("libreoffice")
    if discovered:
        return Path(discovered).resolve()

    candidates = [
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
        Path("/usr/bin/libreoffice"),
        Path("/usr/bin/soffice"),
        Path("/snap/bin/libreoffice"),
    ]
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def available_pdf_converters() -> list[str]:
    """Devuelve motores instalados capaces de renderizar la base de diapositivas."""
    converters: list[str] = []
    if _powerpoint_available():
        converters.append("Microsoft PowerPoint")
    if _find_soffice() is not None:
        converters.append("LibreOffice")
    return converters


def _available_backends(preferred: str | None = None) -> list[ConverterBackend]:
    preference = (preferred or os.environ.get("ANUARIO_PDF_CONVERTER", "auto")).strip().lower()
    if preference not in {"auto", "powerpoint", "libreoffice"}:
        raise PdfConverterUnavailable(
            "ANUARIO_PDF_CONVERTER debe ser auto, powerpoint o libreoffice."
        )

    candidates: list[ConverterBackend] = []
    # Como las figuras SVG ya no pasan por el motor Office, en Windows se puede
    # priorizar PowerPoint por fidelidad del diseño general sin arriesgar el texto
    # SVG. LibreOffice queda como alternativa multiplataforma.
    if preference in {"auto", "powerpoint"} and _powerpoint_available():
        candidates.append(ConverterBackend("Microsoft PowerPoint"))
    soffice = _find_soffice()
    if preference in {"auto", "libreoffice"} and soffice is not None:
        candidates.append(ConverterBackend("LibreOffice", soffice))
    return candidates


def _run_powerpoint(source: Path, target: Path) -> None:
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise PdfConverterUnavailable("No se encontró PowerShell para automatizar PowerPoint.")

    script = r"""
$ErrorActionPreference = 'Stop'
$source = [System.IO.Path]::GetFullPath($env:ANUARIO_PPTX_SOURCE)
$target = [System.IO.Path]::GetFullPath($env:ANUARIO_PDF_TARGET)
$powerPoint = $null
$presentation = $null
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $powerPoint.DisplayAlerts = 1
    $presentation = $powerPoint.Presentations.Open($source, $true, $false, $false)
    $presentation.SaveAs($target, 32)
    if (-not (Test-Path -LiteralPath $target)) {
        throw 'PowerPoint terminó sin crear el PDF.'
    }
}
finally {
    if ($null -ne $presentation) {
        $presentation.Close()
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation)
    }
    if ($null -ne $powerPoint) {
        $powerPoint.Quit()
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($powerPoint)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
"""
    environment = os.environ.copy()
    environment["ANUARIO_PPTX_SOURCE"] = str(source.resolve())
    environment["ANUARIO_PDF_TARGET"] = str(target.resolve())
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=CONVERSION_TIMEOUT_SECONDS,
            env=environment,
            creationflags=creation_flags,
        )
    except subprocess.TimeoutExpired as exc:
        raise PdfConversionError(
            f"PowerPoint excedió {CONVERSION_TIMEOUT_SECONDS // 60} minutos de conversión."
        ) from exc
    if completed.returncode != 0 or not target.is_file():
        detail = (completed.stderr or completed.stdout or "error sin detalle").strip()
        raise PdfConversionError(f"PowerPoint no pudo exportar la base del PPTX: {detail}")


def _run_libreoffice(source: Path, target: Path, executable: Path, workspace: Path) -> None:
    profile = workspace / "libreoffice-profile"
    profile.mkdir(parents=True, exist_ok=True)
    command = [
        str(executable),
        "--headless",
        "--nologo",
        "--nodefault",
        "--nofirststartwizard",
        f"-env:UserInstallation={profile.resolve().as_uri()}",
        "--convert-to",
        "pdf:impress_pdf_Export",
        "--outdir",
        str(workspace),
        str(source.resolve()),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=CONVERSION_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise PdfConversionError(
            f"LibreOffice excedió {CONVERSION_TIMEOUT_SECONDS // 60} minutos de conversión."
        ) from exc

    generated = workspace / f"{source.stem}.pdf"
    if completed.returncode != 0 or not generated.is_file():
        detail = (completed.stderr or completed.stdout or "error sin detalle").strip()
        raise PdfConversionError(f"LibreOffice no pudo exportar la base del PPTX: {detail}")
    generated.replace(target)


def _run_converter(
    backend: ConverterBackend,
    source: Path,
    target: Path,
    workspace: Path,
) -> None:
    if backend.name == "Microsoft PowerPoint":
        _run_powerpoint(source, target)
        return
    if backend.name == "LibreOffice" and backend.executable is not None:
        _run_libreoffice(source, target, backend.executable, workspace)
        return
    raise PdfConverterUnavailable(f"Motor PDF desconocido o incompleto: {backend.name}")


def _presentation_info(source: Path) -> tuple[int, float, float]:
    if not source.is_file() or source.suffix.lower() != ".pptx":
        raise FileNotFoundError(f"No existe la presentación PPTX: {source}")
    try:
        presentation = Presentation(str(source))
    except Exception as exc:
        raise PdfConversionError(f"El archivo no es un PPTX válido: {source.name}") from exc
    slide_count = len(presentation.slides)
    if slide_count < 1:
        raise PdfConversionError("La presentación no contiene diapositivas.")
    width = float(presentation.slide_width) / EMU_PER_POINT
    height = float(presentation.slide_height) / EMU_PER_POINT
    return slide_count, width, height


def _assembly_payload(source_pptx: Path) -> dict[str, Any]:
    report_path = source_pptx.with_name(source_pptx.stem + "_ensamblaje.json")
    if not report_path.is_file():
        return {}
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise PdfConversionError(
            f"No se pudo leer el reporte de ensamblaje: {report_path.name}"
        ) from exc


def _picture_shape_map(source_pptx: Path) -> dict[tuple[int, str], tuple[int, int, int, int]]:
    presentation = Presentation(str(source_pptx))
    positions: dict[tuple[int, str], tuple[int, int, int, int]] = {}
    for slide_index, slide in enumerate(presentation.slides):
        for shape in slide.shapes:
            name = shape.name or ""
            if not name.startswith("ANUARIO_IMAGE_"):
                continue
            figure_id = name.removeprefix("ANUARIO_IMAGE_").replace("_", ".")
            positions[(slide_index, figure_id)] = (
                int(shape.left),
                int(shape.top),
                int(shape.width),
                int(shape.height),
            )
    return positions


def _embedded_svg_hashes(source_pptx: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    with zipfile.ZipFile(source_pptx, "r") as archive:
        for name in archive.namelist():
            if not name.startswith("ppt/media/anuario_figure_") or not name.endswith(".svg"):
                continue
            stem = Path(name).stem.removeprefix("anuario_figure_")
            figure_id = stem.upper().replace("_", ".")
            hashes[figure_id] = _bytes_sha256(archive.read(name))
    return hashes


def _original_svg_placements(
    project_root: Path,
    source_pptx: Path,
) -> list[OriginalSvgPlacement]:
    payload = _assembly_payload(source_pptx)
    inserted = payload.get("inserted", [])
    if not inserted:
        return []

    positions = _picture_shape_map(source_pptx)
    embedded_hashes = _embedded_svg_hashes(source_pptx)
    placements: list[OriginalSvgPlacement] = []
    errors: list[str] = []

    for item in inserted:
        figure_id = str(item.get("figure_id", "")).strip()
        slide_index = int(item.get("slide_number", 0)) - 1
        svg_value = str(item.get("svg_path", "")).strip()
        if not figure_id or slide_index < 0 or not svg_value:
            errors.append(f"Registro de figura incompleto: {item!r}")
            continue
        svg_path = Path(svg_value)
        if not svg_path.is_absolute():
            svg_path = project_root / svg_path
        svg_path = svg_path.resolve()
        if not svg_path.is_file():
            errors.append(f"{figure_id}: no existe el SVG original {svg_path}")
            continue
        try:
            validate_editable_svg(svg_path, require_fully_vector=True)
        except Exception as exc:
            errors.append(f"{figure_id}: SVG original inválido: {exc}")
            continue

        bounds = positions.get((slide_index, figure_id))
        if bounds is None:
            errors.append(
                f"{figure_id}: no se encontró ANUARIO_IMAGE_{figure_id.replace('.', '_')} "
                f"en la diapositiva {slide_index + 1}."
            )
            continue

        svg_hash = _sha256(svg_path)
        embedded_hash = embedded_hashes.get(figure_id)
        if embedded_hash is not None and embedded_hash != svg_hash:
            errors.append(
                f"{figure_id}: el SVG original cambió después de ensamblar el PPTX. "
                "Vuelve a generar la presentación antes de exportar el PDF."
            )
            continue

        placements.append(
            OriginalSvgPlacement(
                figure_id=figure_id,
                slide_index=slide_index,
                svg_path=svg_path,
                left_emu=bounds[0],
                top_emu=bounds[1],
                width_emu=bounds[2],
                height_emu=bounds[3],
                sha256=svg_hash,
            )
        )

    if errors:
        preview = " | ".join(errors[:5])
        suffix = f" | +{len(errors) - 5} errores" if len(errors) > 5 else ""
        raise PdfConversionError(
            "No se puede componer el PDF con los SVG originales: " + preview + suffix
        )
    return placements


def _svg_bundle_sha256(placements: list[OriginalSvgPlacement]) -> str:
    digest = hashlib.sha256()
    for placement in sorted(placements, key=lambda row: (row.slide_index, row.figure_id)):
        digest.update(placement.figure_id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(placement.sha256.encode("ascii"))
        digest.update(b"\0")
        digest.update(
            f"{placement.slide_index}:{placement.left_emu}:{placement.top_emu}:"
            f"{placement.width_emu}:{placement.height_emu}".encode("ascii")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _remove_shape(shape) -> None:
    element = shape._element
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)


def _prepare_pdf_base_source(source: Path, target: Path) -> tuple[int, int]:
    """Guarda un PPTX temporal sin figuras ni helpers de texto.

    El PPTX original no se modifica. Usar python-pptx para guardar la copia hace
    que también se limpien relaciones huérfanas, evitando que Office intente
    procesar SVG de figura durante la conversión de la base.
    """
    presentation = Presentation(str(source))
    removed_figures = 0
    removed_helpers = 0
    for slide in presentation.slides:
        for shape in list(slide.shapes):
            name = shape.name or ""
            if name.startswith("ANUARIO_IMAGE_"):
                _remove_shape(shape)
                removed_figures += 1
            elif name.startswith("ANUARIO_TEXT_LAYER_"):
                _remove_shape(shape)
                removed_helpers += 1

    target.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(target)

    # Verificación explícita: el motor Office sólo recibe la base de diseño.
    check = Presentation(str(target))
    leftovers = [
        shape.name
        for slide in check.slides
        for shape in slide.shapes
        if (shape.name or "").startswith(("ANUARIO_IMAGE_", "ANUARIO_TEXT_LAYER_"))
    ]
    if leftovers:
        raise PdfConversionError(
            "La copia temporal para PDF conservó figuras o helpers: " + ", ".join(leftovers[:5])
        )
    return removed_figures, removed_helpers


def _validate_pdf(
    path: Path,
    expected_pages: int,
    expected_width: float,
    expected_height: float,
) -> PdfReader:
    if not path.is_file() or path.stat().st_size < 256:
        raise PdfConversionError("El convertidor no produjo un PDF utilizable.")
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise PdfConversionError("El archivo producido no es un PDF válido.") from exc
    if len(reader.pages) != expected_pages:
        raise PdfConversionError(
            f"El PPTX tiene {expected_pages} diapositivas y el PDF contiene "
            f"{len(reader.pages)} páginas."
        )
    for page_number, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if abs(width - expected_width) > 1 or abs(height - expected_height) > 1:
            raise PdfConversionError(
                f"La página {page_number} mide {width:.2f} x {height:.2f} puntos; "
                f"se esperaban {expected_width:.2f} x {expected_height:.2f}."
            )
        if page.get_contents() is None:
            raise PdfConversionError(f"La página {page_number} quedó vacía.")
    return reader


def _compose_original_svgs(
    base_pdf: Path,
    output_pdf: Path,
    placements: list[OriginalSvgPlacement],
    expected_pages: int,
    expected_width: float,
    expected_height: float,
) -> int:
    """Superpone directamente los SVG originales sobre la base PDF.

    CairoSVG produce un fragmento PDF vectorial directamente desde los bytes del
    SVG original. PyMuPDF lo coloca como página/XObject sin reescribir sus
    operadores de texto; esto conserva mejor los espacios y el orden de copia
    que fusionar los content streams manualmente.
    """
    _validate_pdf(base_pdf, expected_pages, expected_width, expected_height)
    try:
        import cairosvg  # noqa: PLC0415
        import fitz  # noqa: PLC0415
    except ImportError as exc:
        raise PdfConversionError(
            "CairoSVG o PyMuPDF no están instalados o la librería nativa Cairo no se encuentra. "
            "Instala GTK3 Runtime para Windows: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer"
        ) from exc
    try:
        document = fitz.open(base_pdf)
    except Exception as exc:
        raise PdfConversionError("No se pudo abrir la base PDF para componer los SVG.") from exc

    converted = 0
    try:
        for placement in placements:
            try:
                fragment_bytes = cairosvg.svg2pdf(bytestring=placement.svg_path.read_bytes())
                fragment = fitz.open(stream=fragment_bytes, filetype="pdf")
            except Exception as exc:
                raise PdfConversionError(
                    f"No se pudo convertir directamente el SVG original de {placement.figure_id}: {exc}"
                ) from exc
            try:
                if fragment.page_count != 1:
                    raise PdfConversionError(
                        f"El SVG original de {placement.figure_id} produjo {fragment.page_count} páginas."
                    )
                left = placement.left_emu / EMU_PER_POINT
                top = placement.top_emu / EMU_PER_POINT
                right = (placement.left_emu + placement.width_emu) / EMU_PER_POINT
                bottom = (placement.top_emu + placement.height_emu) / EMU_PER_POINT
                target = fitz.Rect(left, top, right, bottom)
                document[placement.slide_index].show_pdf_page(
                    target,
                    fragment,
                    0,
                    overlay=True,
                    keep_proportion=False,
                )
                converted += 1
            finally:
                fragment.close()

        output_pdf.unlink(missing_ok=True)
        document.save(output_pdf, garbage=4, deflate=True)
    finally:
        document.close()
    return converted


def _load_manifest(project_root: Path) -> dict[str, Any]:
    path = project_root / "assets" / "presentation" / "anuario_estadistico_2026_manifest.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _add_delivery_outline(
    writer: PdfWriter,
    manifest: dict[str, Any],
    page_count: int,
) -> int:
    outline_count = 0

    def add(title: str, page_index: int, parent=None):
        nonlocal outline_count
        if 0 <= page_index < page_count:
            outline_count += 1
            return writer.add_outline_item(title, page_index, parent=parent, is_open=False)
        return None

    add("Portada", 0)
    add("Índice", 1)
    add("Introducción", 2)

    entries = manifest.get("entries", [])
    sections = manifest.get("sections", {})
    for section, section_title in sections.items():
        section_entries = [entry for entry in entries if entry.get("section") == section]
        if not section_entries:
            continue
        section_entries.sort(key=lambda entry: int(entry.get("slide_number", 0)))
        first_slide = int(section_entries[0].get("slide_number", 0))
        parent = add(str(section_title), first_slide - 2)
        for entry in section_entries:
            slide_number = int(entry.get("slide_number", 0))
            figure_id = str(entry.get("figure_id", "")).strip()
            title = str(entry.get("title", "")).strip()
            label = f"Figura {figure_id}. {title}" if title else f"Figura {figure_id}"
            add(label, slide_number - 1, parent=parent)

    if page_count >= 2:
        add("Conclusión", page_count - 2)
    return outline_count


def _searchable_text_expectations(
    source_pptx: Path,
) -> list[tuple[int, str, str, tuple[str, ...]]]:
    payload = _assembly_payload(source_pptx)
    expectations: list[tuple[int, str, str, tuple[str, ...]]] = []
    for item in payload.get("inserted", []):
        svg_texts = tuple(
            str(text) for text in item.get("svg_texts", []) if str(text).strip()
        )
        if not svg_texts:
            continue
        expectations.append(
            (
                int(item.get("slide_number", 0)) - 1,
                str(item.get("figure_id", "")),
                str(item.get("searchable_text_marker") or "").strip(),
                svg_texts,
            )
        )
    return expectations


def _normalized_copy_text(value: str) -> str:
    text = " ".join(
        unicodedata.normalize("NFKC", value).replace("\u00a0", " ").split()
    )
    text = re.sub(r"\s+([,.;:!?%])", r"\1", text)
    text = re.sub(r"([¿¡(\[])\s+", r"\1", text)
    text = re.sub(r"\s+([)\]])", r"\1", text)
    return text


def _validate_svg_text_in_pdf(reader: PdfReader, source_pptx: Path) -> int:
    """Verifica que los textos SVG sean copiables y que no exista el helper PPTX."""
    expectations = _searchable_text_expectations(source_pptx)
    for page_index, figure_id, marker, svg_texts in expectations:
        if page_index < 0 or page_index >= len(reader.pages):
            raise PdfConversionError(
                f"El texto SVG de {figure_id} apunta a una página inexistente."
            )
        page_text = _normalized_copy_text(reader.pages[page_index].extract_text() or "")
        if marker and _normalized_copy_text(marker) in page_text:
            raise PdfConversionError(
                f"El PDF de {figure_id} conserva la capa auxiliar de texto del PPTX; "
                "las figuras deben provenir exclusivamente del SVG original."
            )

        missing_texts = [
            text
            for text in svg_texts
            if _normalized_copy_text(text) not in page_text
        ]
        if missing_texts:
            raise PdfConversionError(
                f"La composición directa perdió {len(missing_texts)} textos SVG copiables de "
                f"la figura {figure_id}; por ejemplo: {missing_texts[0]!r}."
            )
    return len(expectations)


def _polish_pdf(
    project_root: Path,
    run_id: str,
    source_pptx: Path,
    composed_pdf: Path,
    polished_pdf: Path,
    expected_pages: int,
    expected_width: float,
    expected_height: float,
) -> tuple[int, int]:
    reader = _validate_pdf(
        composed_pdf,
        expected_pages,
        expected_width,
        expected_height,
    )
    searchable_text_count = _validate_svg_text_in_pdf(reader, source_pptx)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata(
        {
            "/Title": "Anuario Estadístico 2026 - Presentación completa",
            "/Author": "Comisión Reguladora de Telecomunicaciones",
            "/Subject": f"Presentación de la corrida {run_id}",
            "/Creator": "Anuario Estadístico 2026 - SVG original directo",
            "/Keywords": "Anuario Estadístico 2026, telecomunicaciones, radiodifusión, CRT, SVG",
        }
    )
    outline_count = _add_delivery_outline(writer, _load_manifest(project_root), expected_pages)
    with polished_pdf.open("wb") as stream:
        writer.write(stream)
    polished_reader = _validate_pdf(
        polished_pdf,
        expected_pages,
        expected_width,
        expected_height,
    )
    _validate_svg_text_in_pdf(polished_reader, source_pptx)
    return outline_count, searchable_text_count


def _assembly_summary(project_root: Path, source: Path) -> dict[str, Any]:
    path = source.with_name(source.stem + "_ensamblaje.json")
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {
        "inserted_figure_count": payload.get("inserted_count"),
        "missing_figure_count": payload.get("missing_count"),
        "missing_figures": payload.get("missing_figures", []),
        "embedded_svg_count": payload.get("embedded_svg_count"),
        "transparent_svg_count": payload.get("transparent_svg_count"),
        "fully_vector_svg_count": payload.get("fully_vector_svg_count"),
        "embedded_raster_image_count": payload.get("embedded_raster_image_count"),
        "raster_fallback_count": payload.get("raster_fallback_count"),
        "searchable_text_layer_count": payload.get("searchable_text_layer_count"),
        "svg_missing_count": payload.get("svg_missing_count"),
        "svg_missing_figures": payload.get("svg_missing_figures", []),
        "assembly_manifest": path.relative_to(project_root).as_posix()
        if path.is_relative_to(project_root)
        else str(path),
    }


def _cached_result(
    source: Path,
    output: Path,
    sidecar: Path,
    source_hash: str,
    svg_bundle_hash: str,
    slide_count: int,
    width: float,
    height: float,
) -> PresentationPdfResult | None:
    if not output.is_file() or not sidecar.is_file():
        return None
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if (
        payload.get("pdf_export_schema") != PDF_EXPORT_SCHEMA_VERSION
        or payload.get("source_sha256") != source_hash
        or payload.get("original_svg_bundle_sha256") != svg_bundle_hash
        or payload.get("pdf_composition_mode") != "pptx_base_plus_original_svg_overlay"
    ):
        return None
    try:
        reader = _validate_pdf(output, slide_count, width, height)
        _validate_svg_text_in_pdf(reader, source)
    except PdfConversionError:
        return None
    return PresentationPdfResult(
        output_path=output,
        source_pptx=source,
        converter=str(payload.get("converter", "desconocido")),
        slide_count=slide_count,
        page_count=len(reader.pages),
        reused=True,
    )


def convert_pptx_to_pdf(
    project_root: Path,
    run_id: str,
    source_pptx: Path,
    output_path: Path,
    *,
    preferred_backend: str | None = None,
) -> PresentationPdfResult:
    """Crea el PDF usando el PPTX sólo como base y los SVG originales como figuras."""
    project_root = project_root.resolve()
    source_pptx = source_pptx.resolve()
    output_path = output_path.resolve()
    slide_count, width, height = _presentation_info(source_pptx)
    source_hash = _sha256(source_pptx)
    placements = _original_svg_placements(project_root, source_pptx)
    svg_bundle_hash = _svg_bundle_sha256(placements)
    sidecar = output_path.with_name(output_path.stem + "_pdf.json")

    cached = _cached_result(
        source_pptx,
        output_path,
        sidecar,
        source_hash,
        svg_bundle_hash,
        slide_count,
        width,
        height,
    )
    if cached is not None:
        return cached

    backends = _available_backends(preferred_backend)
    if not backends:
        raise PdfConverterUnavailable(
            "No se encontró un motor para renderizar la base del PPTX. Instala Microsoft "
            "PowerPoint en Windows o LibreOffice en Windows, macOS o Linux. Las figuras "
            "SVG no pasan por ese motor: se insertan directamente después."
        )

    temp_root = project_root / "tmp" / "pdfs"
    temp_root.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    selected_backend: ConverterBackend | None = None
    outline_count = 0
    searchable_text_page_count = 0
    removed_figure_shapes = 0
    removed_helper_text_layers = 0
    directly_composed_svg_count = 0

    with tempfile.TemporaryDirectory(prefix="pptx-base-svg-a-pdf-", dir=temp_root) as temp_name:
        workspace = Path(temp_name)
        base_pptx = workspace / "presentacion_base_sin_figuras.pptx"
        removed_figure_shapes, removed_helper_text_layers = _prepare_pdf_base_source(
            source_pptx,
            base_pptx,
        )
        raw_base_pdf = workspace / "presentacion_base.pdf"
        composed_pdf = workspace / "presentacion_con_svg_original.pdf"
        polished_pdf = workspace / "presentacion_entrega.pdf"

        for backend in backends:
            raw_base_pdf.unlink(missing_ok=True)
            composed_pdf.unlink(missing_ok=True)
            polished_pdf.unlink(missing_ok=True)
            try:
                _run_converter(backend, base_pptx, raw_base_pdf, workspace)
                directly_composed_svg_count = _compose_original_svgs(
                    raw_base_pdf,
                    composed_pdf,
                    placements,
                    slide_count,
                    width,
                    height,
                )
                outline_count, searchable_text_page_count = _polish_pdf(
                    project_root,
                    run_id,
                    source_pptx,
                    composed_pdf,
                    polished_pdf,
                    slide_count,
                    width,
                    height,
                )
            except (PdfConversionError, PdfConverterUnavailable, OSError) as exc:
                errors.append(f"{backend.name}: {exc}")
                continue
            selected_backend = backend
            break

        if selected_backend is None or not polished_pdf.is_file():
            details = " | ".join(errors) or "ningún motor disponible"
            raise PdfConversionError(f"No se pudo crear el PDF: {details}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        pending_output = output_path.with_name(
            f".{output_path.stem}.{uuid.uuid4().hex}.tmp.pdf"
        )
        try:
            shutil.copy2(polished_pdf, pending_output)
            pending_output.replace(output_path)
        finally:
            pending_output.unlink(missing_ok=True)

    payload = {
        "project": "Anuario Estadístico 2026",
        "pdf_export_schema": PDF_EXPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "converted_from_pptx": True,
        "pdf_composition_mode": "pptx_base_plus_original_svg_overlay",
        "pptx_role": "base visual sin figuras SVG",
        "figures_converted_from_pptx": False,
        "pdf_figure_source_policy": (
            "cada figura se inserta directamente desde su SVG original de build/figures; "
            "no se genera SVG alterno ni respaldo raster"
        ),
        "pdf_searchable_text_source": "elementos <text> de los SVG originales convertidos directamente",
        "removed_figure_shapes_from_pdf_base": removed_figure_shapes,
        "removed_helper_text_layers_from_pdf_base": removed_helper_text_layers,
        "directly_composed_original_svg_count": directly_composed_svg_count,
        "original_svg_bundle_sha256": svg_bundle_hash,
        "source_pptx": source_pptx.relative_to(project_root).as_posix()
        if source_pptx.is_relative_to(project_root)
        else str(source_pptx),
        "source_sha256": source_hash,
        "output_pdf": output_path.relative_to(project_root).as_posix()
        if output_path.is_relative_to(project_root)
        else str(output_path),
        "output_sha256": _sha256(output_path),
        "converter": selected_backend.name,
        "platform": sys.platform,
        "slide_count": slide_count,
        "page_count": slide_count,
        "page_size_points": [width, height],
        "outline_count": outline_count,
        "searchable_text_page_count": searchable_text_page_count,
        "validation": {
            "page_count_matches_slides": True,
            "page_size_matches_slides": True,
            "all_pages_have_content": True,
            "embedded_svg_text_is_selectable": True,
            "all_svg_text_is_copyable": True,
            "pdf_uses_svg_text_not_hidden_pptx_layer": True,
            "pdf_figures_are_direct_original_svg": True,
            "no_new_svg_generated_for_pdf": True,
            "pptx_svg_figure_shapes_removed_before_base_render": (
                removed_figure_shapes == len(placements)
            ),
            "original_svg_matches_pptx_assembly": True,
            "figures_use_direct_svg_without_raster_fallback": (
                _assembly_summary(project_root, source_pptx).get("raster_fallback_count") == 0
            ),
            "figures_are_fully_vector_svg": (
                (_assembly_summary(project_root, source_pptx).get("embedded_raster_image_count") or 0)
                == 0
            ),
        },
        **_assembly_summary(project_root, source_pptx),
    }
    pending_sidecar = sidecar.with_name(f".{sidecar.name}.{uuid.uuid4().hex}.tmp")
    try:
        pending_sidecar.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        pending_sidecar.replace(sidecar)
    finally:
        pending_sidecar.unlink(missing_ok=True)

    return PresentationPdfResult(
        output_path=output_path,
        source_pptx=source_pptx,
        converter=selected_backend.name,
        slide_count=slide_count,
        page_count=slide_count,
    )
