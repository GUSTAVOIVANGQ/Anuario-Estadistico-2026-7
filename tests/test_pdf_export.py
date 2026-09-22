from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw
from pypdf import PdfReader

from anuario2026.exports import ensure_pdf


def _figure(path: Path, title: str, color: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1600, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((60, 55, 1540, 845), radius=28, fill="#F5F7F6")
    draw.rectangle((90, 92, 105, 126), fill=color)
    draw.text((126, 92), title, fill="#253532")
    draw.rectangle((180, 245, 1420, 670), fill=color)
    draw.text((90, 782), "Fuente: datos de prueba", fill="#253532")
    image.save(path)


def _run_status(project_root: Path, run_id: str, figures: list[tuple[str, Path]]) -> None:
    run_dir = project_root / "reportes" / run_id
    run_dir.mkdir(parents=True)
    with (run_dir / "estado_figuras.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["figure_id", "status", "output_path", "script_path"],
        )
        writer.writeheader()
        for figure_id, path in figures:
            writer.writerow(
                {
                    "figure_id": figure_id,
                    "status": "OK",
                    "output_path": path.relative_to(project_root).as_posix(),
                    "script_path": f"scripts/figures/figura_{figure_id.lower().replace('.', '_')}.py",
                }
            )


def test_portable_pdf_needs_no_pptx_or_office(tmp_path: Path) -> None:
    first = tmp_path / "build" / "figures" / "A" / "figura_a_1.png"
    second = tmp_path / "build" / "figures" / "B" / "figura_b_1.png"
    _figure(first, "Figura A.1. Indicador económico", "#335A5C")
    _figure(second, "Figura B.1. Servicio fijo", "#86ADAE")
    run_id = "corrida_portatil"
    _run_status(tmp_path, run_id, [("A.1", first), ("B.1", second)])

    pdf_path = ensure_pdf(tmp_path, run_id)

    assert pdf_path.is_file()
    assert not list(tmp_path.rglob("*.pptx"))
    reader = PdfReader(str(pdf_path))
    # Portada, contenido, introducción, dos separadores, dos figuras y cierre.
    assert len(reader.pages) == 8
    assert float(reader.pages[0].mediabox.width) == 720
    assert float(reader.pages[0].mediabox.height) == 405
    assert "Anuario Estadístico 2026" in reader.pages[0].extract_text()
    assert "Presentación completa" in reader.pages[0].extract_text()
    assert reader.outline

    sidecar = pdf_path.with_name(pdf_path.stem + "_pdf.json")
    payload = sidecar.read_text(encoding="utf-8")
    assert '"external_office_required": false' in payload
    assert '"page_count": 8' in payload


def test_pdf_uses_only_successful_figures_from_the_run(tmp_path: Path) -> None:
    success = tmp_path / "build" / "figures" / "A" / "figura_a_1.png"
    ignored = tmp_path / "build" / "figures" / "A" / "figura_a_2.png"
    _figure(success, "Figura A.1. Incluida", "#335A5C")
    _figure(ignored, "Figura A.2. No incluida", "#86ADAE")
    run_id = "corrida_seleccion"
    _run_status(tmp_path, run_id, [("A.1", success)])

    reader = PdfReader(str(ensure_pdf(tmp_path, run_id)))

    # Portada, contenido, introducción, separador A, A.1 y cierre.
    assert len(reader.pages) == 6


def test_pdf_contents_supports_all_annual_sections(tmp_path: Path) -> None:
    image_path = tmp_path / "build" / "figures" / "A" / "figura_a_1.png"
    _figure(image_path, "Figura de control", "#335A5C")
    figures = [(f"{section}.1", image_path) for section in "ABCDEFG"]
    run_id = "corrida_siete_secciones"
    _run_status(tmp_path, run_id, figures)

    reader = PdfReader(str(ensure_pdf(tmp_path, run_id)))

    # Portada, contenido, introducción, siete separadores, siete figuras y cierre.
    assert len(reader.pages) == 18
    contents = reader.pages[1].extract_text()
    assert "INDICADORES ECONÓMICOS" in contents
    assert "INDICADORES DE RADIODIFUSIÓN" in contents
