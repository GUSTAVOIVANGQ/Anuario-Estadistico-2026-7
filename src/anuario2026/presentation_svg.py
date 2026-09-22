"""Incrusta cada figura como SVG directo, sin respaldo raster dentro del PPTX.

``python-pptx`` necesita una imagen compatible para crear inicialmente el
objeto y su geometría. Después de guardar, este módulo cambia la relación
principal de ``a:blip`` para que apunte directamente al SVG, elimina el medio
temporal cuando deja de estar referenciado y valida el paquete resultante.
"""

from __future__ import annotations

import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
import posixpath
from xml.etree import ElementTree


A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
IMAGE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

ElementTree.register_namespace("a", A_NS)
ElementTree.register_namespace("p", P_NS)
ElementTree.register_namespace("r", R_NS)


@dataclass(frozen=True)
class SvgEmbeddingRequest:
    figure_id: str
    slide_number: int
    picture_name: str
    svg_path: Path


@dataclass(frozen=True)
class SvgEmbeddingResult:
    figure_id: str
    slide_number: int
    picture_name: str
    svg_path: Path
    media_path: str
    relationship_id: str
    replaced_media_path: str


def _xml_bytes(root: ElementTree.Element) -> bytes:
    # Los manifiestos de paquete OOXML usan un namespace predeterminado. Aunque
    # PowerPoint acepta el prefijo ``ns0``, algunos validadores y aplicaciones
    # de terceros exigen la serialización canónica sin prefijo.
    if root.tag in {
        f"{{{CONTENT_TYPES_NS}}}Types",
        f"{{{PACKAGE_REL_NS}}}Relationships",
    }:
        namespace = root.tag[1:].split("}", 1)[0]
        ElementTree.register_namespace("", namespace)
    return ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)


def _find_picture_blip(slide_root: ElementTree.Element, picture_name: str):
    namespaces = {"p": P_NS, "a": A_NS}
    for picture in slide_root.findall(".//p:pic", namespaces):
        properties = picture.find("./p:nvPicPr/p:cNvPr", namespaces)
        if properties is None or properties.get("name") != picture_name:
            continue
        blip = picture.find("./p:blipFill/a:blip", namespaces)
        if blip is not None:
            return blip
    return None


def _relationship_by_id(relationships_root: ElementTree.Element, relationship_id: str):
    return next(
        (
            relationship
            for relationship in relationships_root
            if relationship.get("Id") == relationship_id
        ),
        None,
    )


def _add_svg_content_type(content_types_root: ElementTree.Element) -> None:
    for entry in content_types_root:
        if entry.get("Extension", "").lower() == "svg":
            entry.set("ContentType", "image/svg+xml")
            return
    ElementTree.SubElement(
        content_types_root,
        f"{{{CONTENT_TYPES_NS}}}Default",
        {"Extension": "svg", "ContentType": "image/svg+xml"},
    )


def _remove_svg_fallback_extensions(blip: ElementTree.Element) -> None:
    extension_list = blip.find(f"{{{A_NS}}}extLst")
    if extension_list is None:
        return
    for extension in list(extension_list):
        if extension.find(".//{http://schemas.microsoft.com/office/drawing/2016/SVG/main}svgBlip") is not None:
            extension_list.remove(extension)
    if not list(extension_list):
        blip.remove(extension_list)


def _safe_media_name(figure_id: str) -> str:
    token = figure_id.lower().replace(".", "_").replace("-", "_")
    return f"ppt/media/anuario_figure_{token}.svg"


def _resolved_relationship_target(source_part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(source_part), target))


def _source_part_for_relationships(relationships_name: str) -> str:
    if relationships_name == "_rels/.rels":
        return ""
    marker = "/_rels/"
    if marker not in relationships_name or not relationships_name.endswith(".rels"):
        raise ValueError(f"Ruta de relaciones OOXML inesperada: {relationships_name}")
    prefix, filename = relationships_name.split(marker, 1)
    return f"{prefix}/{filename[:-5]}"


def _referenced_parts(
    original_parts: dict[str, tuple[zipfile.ZipInfo, bytes]],
    replacements: dict[str, bytes],
) -> set[str]:
    referenced: set[str] = set()
    for name, (_, original_data) in original_parts.items():
        if not name.endswith(".rels"):
            continue
        root = ElementTree.fromstring(replacements.get(name, original_data))
        source_part = _source_part_for_relationships(name)
        for relationship in root:
            if relationship.get("TargetMode") == "External":
                continue
            target = relationship.get("Target")
            if target:
                referenced.add(_resolved_relationship_target(source_part, target))
    return referenced


def embed_svg_images(
    pptx_path: Path,
    requests: list[SvgEmbeddingRequest],
) -> list[SvgEmbeddingResult]:
    """Sustituye la relación raster temporal por una relación SVG directa."""
    if not requests:
        return []
    for request in requests:
        if not request.svg_path.is_file():
            raise FileNotFoundError(
                f"No existe el SVG de la figura {request.figure_id}: {request.svg_path}"
            )

    with zipfile.ZipFile(pptx_path, "r") as source:
        original_parts = {info.filename: (info, source.read(info.filename)) for info in source.infolist()}

    content_name = "[Content_Types].xml"
    content_root = ElementTree.fromstring(original_parts[content_name][1])
    _add_svg_content_type(content_root)
    replacements: dict[str, bytes] = {content_name: _xml_bytes(content_root)}
    new_media: dict[str, bytes] = {}
    results: list[SvgEmbeddingResult] = []

    for request in requests:
        slide_name = f"ppt/slides/slide{request.slide_number}.xml"
        relationships_name = (
            f"ppt/slides/_rels/slide{request.slide_number}.xml.rels"
        )
        slide_bytes = replacements.get(slide_name, original_parts[slide_name][1])
        relationships_bytes = replacements.get(
            relationships_name,
            original_parts[relationships_name][1],
        )
        slide_root = ElementTree.fromstring(slide_bytes)
        relationships_root = ElementTree.fromstring(relationships_bytes)
        blip = _find_picture_blip(slide_root, request.picture_name)
        if blip is None:
            raise ValueError(
                f"No se encontró {request.picture_name!r} en la diapositiva "
                f"{request.slide_number}."
            )

        relationship_id = blip.get(f"{{{R_NS}}}embed")
        if not relationship_id:
            raise ValueError(
                f"La imagen {request.picture_name!r} no tiene una relación incrustada."
            )
        relationship = _relationship_by_id(relationships_root, relationship_id)
        if relationship is None or relationship.get("Type") != IMAGE_REL_TYPE:
            raise ValueError(
                f"La relación de {request.picture_name!r} no es una imagen OOXML válida."
            )
        previous_target = relationship.get("Target", "")
        previous_media_path = _resolved_relationship_target(slide_name, previous_target)
        media_path = _safe_media_name(request.figure_id)
        target = "../media/" + Path(media_path).name
        relationship.set("Target", target)
        _remove_svg_fallback_extensions(blip)
        replacements[slide_name] = _xml_bytes(slide_root)
        replacements[relationships_name] = _xml_bytes(relationships_root)
        new_media[media_path] = request.svg_path.read_bytes()
        results.append(
            SvgEmbeddingResult(
                figure_id=request.figure_id,
                slide_number=request.slide_number,
                picture_name=request.picture_name,
                svg_path=request.svg_path,
                media_path=media_path,
                relationship_id=relationship_id,
                replaced_media_path=previous_media_path,
            )
        )

    referenced_parts = _referenced_parts(original_parts, replacements)
    obsolete_media = {
        result.replaced_media_path
        for result in results
        if result.replaced_media_path not in referenced_parts
    }

    temporary_path = pptx_path.with_name(
        f".{pptx_path.stem}.{uuid.uuid4().hex}.svg.tmp.pptx"
    )
    try:
        with zipfile.ZipFile(temporary_path, "w") as target:
            for name, (info, data) in original_parts.items():
                if name in obsolete_media or name in new_media:
                    continue
                target.writestr(info, replacements.get(name, data))
            for media_path, data in new_media.items():
                target.writestr(media_path, data, compress_type=zipfile.ZIP_DEFLATED)
        temporary_path.replace(pptx_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    validate_svg_embeddings(pptx_path, results)
    return results


def validate_svg_embeddings(
    pptx_path: Path,
    embeddings: list[SvgEmbeddingResult],
) -> None:
    """Comprueba que cada figura apunta sólo al SVG y no conserva su raster."""
    with zipfile.ZipFile(pptx_path, "r") as archive:
        content_types = ElementTree.fromstring(archive.read("[Content_Types].xml"))
        svg_types = [
            entry
            for entry in content_types
            if entry.get("Extension", "").lower() == "svg"
            and entry.get("ContentType") == "image/svg+xml"
        ]
        if not svg_types:
            raise RuntimeError("El PPTX no declaró el tipo MIME image/svg+xml.")

        for embedding in embeddings:
            if archive.read(embedding.media_path) != embedding.svg_path.read_bytes():
                raise RuntimeError(
                    f"El SVG incrustado de {embedding.figure_id} no coincide con su origen."
                )
            slide_name = f"ppt/slides/slide{embedding.slide_number}.xml"
            relationships_name = (
                f"ppt/slides/_rels/slide{embedding.slide_number}.xml.rels"
            )
            slide_root = ElementTree.fromstring(archive.read(slide_name))
            relationships_root = ElementTree.fromstring(archive.read(relationships_name))
            blip = _find_picture_blip(slide_root, embedding.picture_name)
            if blip is None:
                raise RuntimeError(f"No se conservó la figura {embedding.figure_id}.")
            if blip.get(f"{{{R_NS}}}embed") != embedding.relationship_id:
                raise RuntimeError(
                    f"La figura {embedding.figure_id} no apunta al SVG nativo."
                )
            if blip.find(
                ".//{http://schemas.microsoft.com/office/drawing/2016/SVG/main}svgBlip"
            ) is not None:
                raise RuntimeError(
                    f"La figura {embedding.figure_id} conserva un respaldo raster."
                )
            relationship = _relationship_by_id(
                relationships_root,
                embedding.relationship_id,
            )
            if relationship is None or relationship.get("Target") != (
                "../media/" + Path(embedding.media_path).name
            ):
                raise RuntimeError(
                    f"La relación SVG de {embedding.figure_id} quedó incompleta."
                )
            if embedding.replaced_media_path in archive.namelist():
                raise RuntimeError(
                    f"La figura {embedding.figure_id} todavía conserva el medio raster "
                    f"{embedding.replaced_media_path}."
                )
