from __future__ import annotations

import csv
import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from .figure_outputs import companion_paths, inspect_svg, validate_editable_svg, validate_jpg
from .pdf_export import PdfConversionError, PdfConverterUnavailable, convert_pptx_to_pdf
from .pipeline import assemble_pptx
from .reports import sha256_file


class ExportUnavailable(RuntimeError):
    """La exportación solicitada no puede construirse con artefactos verificados."""


def _run_dir(project_root: Path, run_id: str) -> Path:
    candidate = (project_root / "reportes" / run_id).resolve()
    reports_root = (project_root / "reportes").resolve()
    if reports_root not in candidate.parents or not candidate.is_dir():
        raise FileNotFoundError(f"No existe la corrida: {run_id}")
    return candidate


def _read_successful_rows(project_root: Path, run_id: str) -> list[dict[str, str | Path]]:
    run_dir = _run_dir(project_root, run_id)
    status_path = run_dir / "estado_figuras.csv"
    if not status_path.is_file():
        raise FileNotFoundError(f"No existe el estado de la corrida: {status_path}")

    rows: list[dict[str, str | Path]] = []
    with status_path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("status") != "OK":
                continue
            figure_id = (row.get("figure_id") or "").strip()
            rel = (row.get("output_path") or "").strip()
            if not figure_id or not rel:
                continue
            path = (project_root / Path(rel.replace("\\", "/"))).resolve()
            if project_root.resolve() not in path.parents or not path.is_file():
                continue
            rows.append(
                {
                    "figure_id": figure_id,
                    "source_path": path,
                    "script_path": (row.get("script_path") or "").replace("\\", "/"),
                }
            )
    if not rows:
        raise FileNotFoundError("La corrida no contiene figuras generadas correctamente.")
    return rows


def successful_figure_paths(project_root: Path, run_id: str) -> list[tuple[str, Path]]:
    return [
        (str(row["figure_id"]), Path(row["source_path"]))
        for row in _read_successful_rows(project_root, run_id)
    ]


def _safe_name(figure_id: str) -> str:
    return "figura_" + figure_id.lower().replace(".", "_")


def _write_export_notes(temp_root: Path, project_root: Path, kind: str) -> None:
    description = {
        "png": "PNG sin pérdida, generado directamente por el script de cada figura.",
        "jpg": "JPG de alta calidad, generado desde la misma figura Matplotlib que el PNG.",
        "svg": (
            "SVG nativo, autocontenido y con lienzo transparente. Los textos permanecen como elementos <text> "
            "seleccionables, con su posición en x/y o transform; las formas compatibles "
            "permanecen vectoriales. Los mapas o capas creadas originalmente como imagen "
            "pueden conservar imágenes incrustadas sin convertir el texto en curvas."
        ),
    }[kind]
    font_note = ""
    if kind == "svg":
        font_source = project_root / "assets" / "fonts" / "Noto_Sans"
        if font_source.is_dir():
            shutil.copytree(font_source, temp_root / "FUENTES" / "Noto_Sans")
            font_note = (
                "Para evitar sustituciones tipográficas al editar, instala las fuentes "
                "Noto Sans incluidas en FUENTES/Noto_Sans. Se conserva también su "
                "licencia OFL.txt.\n"
            )

    notes = (
        "Anuario Estadístico 2026 — compendio de figuras\n"
        "===================================================\n\n"
        f"{description}\n\n"
        "MANIFIESTO_EXPORTACION.csv registra el script de origen y la huella SHA-256 "
        "de cada archivo.\n"
        + (
            "TEXTOS_Y_POSICIONES.csv permite localizar y auditar cada texto del SVG.\n"
            if kind == "svg"
            else ""
        )
        + font_note
    )
    (temp_root / "LEEME.txt").write_text(notes, encoding="utf-8")


def _svg_text_rows(figure_id: str, svg_path: Path) -> list[dict[str, str | int]]:
    root = ElementTree.parse(svg_path).getroot()
    parents = {child: parent for parent in root.iter() for child in parent}
    rows: list[dict[str, str | int]] = []
    position = 0
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "text":
            continue
        content = "".join(element.itertext()).strip()
        if not content:
            continue
        position += 1
        ancestor = parents.get(element)
        group_id = ""
        while ancestor is not None:
            if ancestor.get("id"):
                group_id = ancestor.get("id", "")
                break
            ancestor = parents.get(ancestor)
        rows.append(
            {
                "figure_id": figure_id,
                "text_order": position,
                "svg_group_id": group_id,
                "svg_element_id": element.get("id", ""),
                "text": " ".join(content.split()),
                "x": element.get("x", ""),
                "y": element.get("y", ""),
                "transform": element.get("transform", ""),
                "style": element.get("style", ""),
            }
        )
    return rows


def create_figure_compendium(project_root: Path, run_id: str, kind: str) -> Path:
    kind = kind.lower()
    if kind not in {"png", "jpg", "svg"}:
        raise ValueError(f"Formato de compendio no soportado: {kind}")

    rows = _read_successful_rows(project_root, run_id)
    export_dir = project_root / "entrega" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"anuario_estadistico_2026_{run_id}_figuras_{kind}.zip"

    with tempfile.TemporaryDirectory(prefix=f"anuario_{kind}_") as temp_name:
        temp_root = Path(temp_name)
        manifest: list[dict[str, str | int | bool]] = []
        svg_texts: list[dict[str, str | int]] = []
        for row in rows:
            figure_id = str(row["figure_id"])
            source_path = Path(row["source_path"])
            section_dir = temp_root / figure_id.split(".", 1)[0]
            section_dir.mkdir(parents=True, exist_ok=True)
            base_name = _safe_name(figure_id)
            sources = companion_paths(source_path)
            target = section_dir / f"{base_name}.{kind}"
            if kind == "png":
                export_source = sources["png"]
            elif kind == "jpg":
                export_source = sources["jpg"]
                if not export_source.is_file():
                    raise ExportUnavailable(
                        f"La figura {figure_id} no tiene JPG generado por código. "
                        "Vuelve a ejecutar esa figura o la corrida completa."
                    )
                try:
                    validate_jpg(export_source)
                except (OSError, ValueError) as exc:
                    raise ExportUnavailable(
                        f"El JPG generado para {figure_id} no superó la validación. "
                        "Vuelve a ejecutar esa figura."
                    ) from exc
            else:
                export_source = sources["svg"]
                if not export_source.is_file():
                    raise ExportUnavailable(
                        f"La figura {figure_id} no tiene SVG nativo editable. "
                        "Vuelve a ejecutar esa figura o la corrida completa."
                    )
                try:
                    validate_editable_svg(export_source)
                except (OSError, ValueError) as exc:
                    raise ExportUnavailable(
                        f"El SVG de {figure_id} no contiene texto editable y posicionado. "
                        "Vuelve a ejecutar esa figura."
                    ) from exc

            shutil.copy2(export_source, target)
            inspection = inspect_svg(export_source) if kind == "svg" else None
            manifest.append(
                {
                    "figure_id": figure_id,
                    "section": figure_id.split(".", 1)[0],
                    "format": kind.upper(),
                    "archive_path": target.relative_to(temp_root).as_posix(),
                    "source_script": str(row["script_path"]),
                    "generated_path": export_source.relative_to(
                        project_root.resolve()
                    ).as_posix(),
                    "sha256": sha256_file(target),
                    "bytes": target.stat().st_size,
                    "editable_text": inspection.editable_text if inspection else "",
                    "fully_vector": inspection.fully_vector if inspection else "",
                    "transparent_background": (
                        inspection.transparent_background if inspection else ""
                    ),
                    "text_elements": inspection.text_elements if inspection else "",
                    "positioned_text_elements": (
                        inspection.positioned_text_elements if inspection else ""
                    ),
                    "vector_elements": inspection.vector_elements if inspection else "",
                    "embedded_images": inspection.embedded_images if inspection else "",
                }
            )
            if kind == "svg":
                svg_texts.extend(_svg_text_rows(figure_id, export_source))

        _write_export_notes(temp_root, project_root, kind)
        manifest_fields = [
            "figure_id",
            "section",
            "format",
            "archive_path",
            "source_script",
            "generated_path",
            "sha256",
            "bytes",
            "editable_text",
            "fully_vector",
            "transparent_background",
            "text_elements",
            "positioned_text_elements",
            "vector_elements",
            "embedded_images",
        ]
        with (temp_root / "MANIFIESTO_EXPORTACION.csv").open(
            "w", encoding="utf-8-sig", newline=""
        ) as stream:
            writer = csv.DictWriter(stream, fieldnames=manifest_fields)
            writer.writeheader()
            writer.writerows(manifest)
        if kind == "svg":
            with (temp_root / "TEXTOS_Y_POSICIONES.csv").open(
                "w", encoding="utf-8-sig", newline=""
            ) as stream:
                fields = [
                    "figure_id",
                    "text_order",
                    "svg_group_id",
                    "svg_element_id",
                    "text",
                    "x",
                    "y",
                    "transform",
                    "style",
                ]
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(svg_texts)

        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(temp_root.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(temp_root))
    return zip_path


def ensure_pptx(project_root: Path, run_id: str) -> Path:
    run_dir = _run_dir(project_root, run_id)
    output = project_root / "entrega" / f"anuario_estadistico_2026_{run_id}.pptx"
    if not output.is_file():
        assemble_pptx(project_root, run_dir, output=output)
    return output


def ensure_pdf(project_root: Path, run_id: str) -> Path:
    pptx_path = ensure_pptx(project_root, run_id)
    pdf_path = project_root / "entrega" / f"anuario_estadistico_2026_{run_id}.pdf"
    try:
        result = convert_pptx_to_pdf(
            project_root,
            run_id,
            pptx_path,
            pdf_path,
        )
    except (PdfConverterUnavailable, PdfConversionError) as exc:
        raise ExportUnavailable(str(exc)) from exc
    return result.output_path
