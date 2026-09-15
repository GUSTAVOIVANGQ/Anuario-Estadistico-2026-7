from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image
from pptx import Presentation
from pptx.util import Inches


DEFAULT_INSET_INCHES = 0.08


@dataclass(frozen=True)
class AssemblyResult:
    output_path: Path
    report_path: Path
    inserted: int
    missing: tuple[str, ...]
    errors: tuple[str, ...]
    slide_count: int


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _resolve_presentation_config(project_root: Path, config: dict[str, Any]) -> tuple[Path, Path]:
    presentation = config.get("presentation", {})
    template_rel = presentation.get(
        "template", "assets/presentation/anuario_estadistico_2026_automatizable.pptx"
    )
    manifest_rel = presentation.get(
        "manifest", "assets/presentation/anuario_estadistico_2026_manifest.json"
    )
    return project_root / template_rel, project_root / manifest_rel


def _shape_by_name(slide, name: str):
    for shape in slide.shapes:
        if shape.name == name:
            return shape
    return None


def _contain_box(
    image_path: Path,
    left: int,
    top: int,
    width: int,
    height: int,
    *,
    inset_inches: float,
) -> tuple[int, int, int, int]:
    inset = int(Inches(inset_inches))
    box_left = left + inset
    box_top = top + inset
    box_width = max(1, width - 2 * inset)
    box_height = max(1, height - 2 * inset)

    with Image.open(image_path) as image:
        pixel_width, pixel_height = image.size
    if pixel_width <= 0 or pixel_height <= 0:
        raise ValueError(f"Dimensiones inválidas en {image_path}")

    image_ratio = pixel_width / pixel_height
    box_ratio = box_width / box_height
    if image_ratio >= box_ratio:
        target_width = box_width
        target_height = max(1, int(round(target_width / image_ratio)))
    else:
        target_height = box_height
        target_width = max(1, int(round(target_height * image_ratio)))

    target_left = box_left + (box_width - target_width) // 2
    target_top = box_top + (box_height - target_height) // 2
    return target_left, target_top, target_width, target_height


def _insert_picture_after_placeholder(slide, placeholder, image_path: Path, figure_id: str) -> None:
    left, top, width, height = _contain_box(
        image_path,
        placeholder.left,
        placeholder.top,
        placeholder.width,
        placeholder.height,
        inset_inches=DEFAULT_INSET_INCHES,
    )

    if getattr(placeholder, "has_text_frame", False):
        placeholder.text_frame.clear()

    sp_tree = slide.shapes._spTree
    placeholder_index = sp_tree.index(placeholder._element)
    picture = slide.shapes.add_picture(str(image_path), left, top, width, height)
    picture.name = "ANUARIO_IMAGE_" + figure_id.replace(".", "_")

    picture_element = picture._element
    sp_tree.remove(picture_element)
    sp_tree.insert(placeholder_index + 1, picture_element)


def assemble_from_template(
    project_root: Path,
    output_path: Path,
    *,
    strict: bool = False,
    run_dir: Path | None = None,
) -> AssemblyResult:
    """Inserta las figuras generadas en la plantilla automatizable del Anuario 2026.

    La posición de cada figura se obtiene del manifest y el objeto de PowerPoint se localiza
    por su nombre estable (por ejemplo, ``ANUARIO_FIGURE_A_1``). La tarjeta de fondo se
    conserva para mantener el diseño; sólo se borra el token visual y se coloca la imagen
    encima respetando proporción (fit=contain).
    """

    config = _load_json(project_root / "config" / "proyecto.json")
    template_path, manifest_path = _resolve_presentation_config(project_root, config)
    if not template_path.is_file():
        raise FileNotFoundError(f"Falta la plantilla PowerPoint automatizable: {template_path}")
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Falta el manifest de la plantilla: {manifest_path}")

    manifest = _load_json(manifest_path)
    entries = manifest.get("entries", [])
    if not entries:
        raise ValueError(f"El manifest no contiene entradas de figuras: {manifest_path}")

    presentation = Presentation(str(template_path))
    expected_slide_count = int(manifest.get("slide_count") or len(presentation.slides))
    if len(presentation.slides) != expected_slide_count:
        raise ValueError(
            "La plantilla no coincide con el manifest: "
            f"{len(presentation.slides)} diapositivas vs {expected_slide_count}."
        )

    inserted = 0
    missing: list[str] = []
    errors: list[str] = []
    inserted_rows: list[dict[str, Any]] = []

    for entry in entries:
        figure_id = str(entry["figure_id"])
        slide_number = int(entry["slide_number"])
        shape_name = str(entry["figure_shape_name"])
        image_rel = Path(str(entry["expected_image"]))
        image_path = project_root / image_rel

        if not image_path.is_file():
            missing.append(figure_id)
            continue
        if slide_number < 1 or slide_number > len(presentation.slides):
            errors.append(f"{figure_id}: diapositiva fuera de rango ({slide_number})")
            continue

        slide = presentation.slides[slide_number - 1]
        placeholder = _shape_by_name(slide, shape_name)
        if placeholder is None:
            errors.append(
                f"{figure_id}: no se encontró el objeto {shape_name!r} en la diapositiva "
                f"{slide_number}"
            )
            continue

        try:
            _insert_picture_after_placeholder(slide, placeholder, image_path, figure_id)
        except Exception as exc:  # noqa: BLE001 - reportar figura específica
            errors.append(f"{figure_id}: {type(exc).__name__}: {exc}")
            continue

        inserted += 1
        inserted_rows.append(
            {
                "figure_id": figure_id,
                "slide_number": slide_number,
                "shape_name": shape_name,
                "image_path": str(image_rel).replace("\\", "/"),
            }
        )

    if strict and (missing or errors):
        details = []
        if missing:
            details.append(f"faltan {len(missing)} figuras: {', '.join(missing)}")
        if errors:
            details.append(f"errores: {'; '.join(errors)}")
        raise RuntimeError("No se generó el PPTX en modo estricto; " + " | ".join(details))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    presentation.save(str(output_path))

    # Verificación mínima del paquete recién escrito.
    reopened = Presentation(str(output_path))
    if len(reopened.slides) != len(presentation.slides):
        raise RuntimeError("La verificación del PPTX detectó un número de diapositivas distinto.")

    report_path = output_path.with_name(output_path.stem + "_ensamblaje.json")
    report = {
        "project": config.get("project_name", "Anuario Estadístico 2026"),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "template": str(template_path.relative_to(project_root)).replace("\\", "/"),
        "manifest": str(manifest_path.relative_to(project_root)).replace("\\", "/"),
        "output": str(output_path.relative_to(project_root)).replace("\\", "/")
        if output_path.is_relative_to(project_root)
        else str(output_path),
        "run_dir": str(run_dir.relative_to(project_root)).replace("\\", "/")
        if run_dir and run_dir.is_relative_to(project_root)
        else (str(run_dir) if run_dir else None),
        "slide_count": len(presentation.slides),
        "manifest_figure_count": len(entries),
        "inserted_count": inserted,
        "missing_count": len(missing),
        "error_count": len(errors),
        "missing_figures": missing,
        "errors": errors,
        "inserted": inserted_rows,
        "fit_policy": "contain",
        "placeholder_policy": "conservar tarjeta, limpiar token y superponer imagen",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return AssemblyResult(
        output_path=output_path,
        report_path=report_path,
        inserted=inserted,
        missing=tuple(missing),
        errors=tuple(errors),
        slide_count=len(presentation.slides),
    )
