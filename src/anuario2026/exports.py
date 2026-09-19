from __future__ import annotations

import base64
import csv
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

from .pipeline import assemble_pptx


class ExportUnavailable(RuntimeError):
    """La exportación solicitada necesita una herramienta externa no disponible."""


def _run_dir(project_root: Path, run_id: str) -> Path:
    candidate = (project_root / "reportes" / run_id).resolve()
    reports_root = (project_root / "reportes").resolve()
    if reports_root not in candidate.parents or not candidate.is_dir():
        raise FileNotFoundError(f"No existe la corrida: {run_id}")
    return candidate


def successful_figure_paths(project_root: Path, run_id: str) -> list[tuple[str, Path]]:
    run_dir = _run_dir(project_root, run_id)
    status_path = run_dir / "estado_figuras.csv"
    if not status_path.is_file():
        raise FileNotFoundError(f"No existe el estado de la corrida: {status_path}")

    rows: list[tuple[str, Path]] = []
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
            rows.append((figure_id, path))
    if not rows:
        raise FileNotFoundError("La corrida no contiene figuras generadas correctamente.")
    return rows


def _safe_name(figure_id: str) -> str:
    return "figura_" + figure_id.lower().replace(".", "_")


def _write_svg_wrapper(png_path: Path, svg_path: Path) -> None:
    """Crea un SVG válido que conserva exactamente el render final del PNG.

    Si una figura tiene un SVG nativo junto al PNG se usa ese archivo. Este
    wrapper es el respaldo compatible para figuras que hoy sólo producen PNG.
    """
    with Image.open(png_path) as image:
        width, height = image.size
    encoded = base64.b64encode(png_path.read_bytes()).decode("ascii")
    title = escape(png_path.stem)
    svg_path.write_text(
        "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                f"  <title>{title}</title>",
                f'  <image width="{width}" height="{height}" href="data:image/png;base64,{encoded}"/>',
                "</svg>",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def create_figure_compendium(project_root: Path, run_id: str, kind: str) -> Path:
    kind = kind.lower()
    if kind not in {"png", "jpg", "svg"}:
        raise ValueError(f"Formato de compendio no soportado: {kind}")

    rows = successful_figure_paths(project_root, run_id)
    export_dir = project_root / "entrega" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"anuario_estadistico_2026_{run_id}_figuras_{kind}.zip"

    with tempfile.TemporaryDirectory(prefix=f"anuario_{kind}_") as temp_name:
        temp_root = Path(temp_name)
        for figure_id, source_path in rows:
            section_dir = temp_root / figure_id.split(".", 1)[0]
            section_dir.mkdir(parents=True, exist_ok=True)
            base_name = _safe_name(figure_id)
            if kind == "png":
                shutil.copy2(source_path, section_dir / f"{base_name}.png")
            elif kind == "jpg":
                target = section_dir / f"{base_name}.jpg"
                with Image.open(source_path) as image:
                    rgb = image.convert("RGB")
                    rgb.save(target, "JPEG", quality=95, optimize=True)
            else:
                native_svg = source_path.with_suffix(".svg")
                target = section_dir / f"{base_name}.svg"
                if native_svg.is_file():
                    shutil.copy2(native_svg, target)
                else:
                    _write_svg_wrapper(source_path, target)

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


def _convert_with_libreoffice(pptx_path: Path, pdf_path: Path) -> bool:
    executable = shutil.which("soffice") or shutil.which("libreoffice")
    if not executable:
        return False
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            executable,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(pdf_path.parent),
            str(pptx_path),
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    generated = pdf_path.parent / f"{pptx_path.stem}.pdf"
    if completed.returncode == 0 and generated.is_file():
        if generated.resolve() != pdf_path.resolve():
            if pdf_path.exists():
                pdf_path.unlink()
            generated.replace(pdf_path)
        return True
    return False


def _convert_with_powerpoint(pptx_path: Path, pdf_path: Path) -> bool:
    if sys.platform != "win32":
        return False
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        return False

    source = str(pptx_path.resolve()).replace("'", "''")
    destination = str(pdf_path.resolve()).replace("'", "''")
    script = f"""
$ErrorActionPreference = 'Stop'
$powerPoint = New-Object -ComObject PowerPoint.Application
$powerPoint.Visible = [Microsoft.Office.Core.MsoTriState]::msoFalse
$presentation = $powerPoint.Presentations.Open('{source}', $true, $true, $false)
$presentation.SaveAs('{destination}', 32)
$presentation.Close()
$powerPoint.Quit()
"""
    completed = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    return completed.returncode == 0 and pdf_path.is_file()


def ensure_pdf(project_root: Path, run_id: str) -> Path:
    pptx_path = ensure_pptx(project_root, run_id)
    pdf_path = pptx_path.with_suffix(".pdf")
    if pdf_path.is_file() and pdf_path.stat().st_mtime >= pptx_path.stat().st_mtime:
        return pdf_path

    # En Windows, PowerPoint suele ser la vía más rápida y fiel. En otros
    # sistemas se usa LibreOffice; ambos quedan como respaldo mutuo.
    if _convert_with_powerpoint(pptx_path, pdf_path):
        return pdf_path
    if _convert_with_libreoffice(pptx_path, pdf_path):
        return pdf_path
    raise ExportUnavailable(
        "No se encontró LibreOffice ni Microsoft PowerPoint para convertir la presentación a PDF. "
        "Instala LibreOffice o ejecuta la app en un equipo con PowerPoint."
    )
