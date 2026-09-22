from __future__ import annotations

import csv
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest
from matplotlib.figure import Figure
from PIL import Image

import anuario2026.figure_outputs as figure_outputs
from anuario2026.exports import ExportUnavailable, create_figure_compendium
from anuario2026.figure_outputs import (
    extract_svg_text,
    inspect_svg,
    install_figure_output_exporter,
    validate_figure_bundle,
)


@pytest.fixture(autouse=True)
def _restore_matplotlib_savefig():
    original_savefig = Figure.savefig
    original_installed = figure_outputs._exporter_installed
    figure_outputs._exporter_installed = False
    yield
    Figure.savefig = original_savefig
    figure_outputs._exporter_installed = original_installed


def _save_sample_bundle(png_path: Path) -> None:
    install_figure_output_exporter()
    fig, ax = plt.subplots(figsize=(4, 2.25))
    ax.bar(["Uno", "Dos"], [1, 2])
    ax.set_title("Figura A.1. Texto seleccionable")
    ax.set_ylabel("Porcentaje")
    fig.savefig(png_path, dpi=100, facecolor="white")
    plt.close(fig)


def _write_run(project_root: Path, run_id: str, output: Path) -> None:
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
        writer.writerow(
            {
                "figure_id": "A.1",
                "status": "OK",
                "output_path": output.relative_to(project_root).as_posix(),
                "script_path": "scripts/figures/figura_a_1.py",
            }
        )


def test_png_save_generates_code_native_jpg_and_editable_svg(tmp_path: Path) -> None:
    png_path = tmp_path / "figura_a_1.png"
    _save_sample_bundle(png_path)

    inspection = validate_figure_bundle(png_path)
    assert inspection.editable_text
    assert inspection.text_elements >= 4
    assert inspection.vector_elements > 0
    assert inspection.embedded_images == 0
    assert inspection.transparent_background

    svg = png_path.with_suffix(".svg").read_text(encoding="utf-8")
    assert "<text" in svg
    assert "Texto seleccionable" in svg
    assert "data:image/png;base64" not in svg
    assert 'id="patch_1"' in svg
    assert "fill: none" in svg
    extracted = extract_svg_text(png_path.with_suffix(".svg"))
    assert any("Texto seleccionable" in text for text in extracted)
    assert "Porcentaje" in extracted

    with Image.open(png_path) as png, Image.open(png_path.with_suffix(".jpg")) as jpg:
        assert jpg.format == "JPEG"
        assert jpg.size == png.size


def test_svg_compendium_contains_origin_manifest_and_text_positions(tmp_path: Path) -> None:
    output = tmp_path / "build" / "figures" / "A" / "figura_a_1.png"
    output.parent.mkdir(parents=True)
    _save_sample_bundle(output)
    fonts = tmp_path / "assets" / "fonts" / "Noto_Sans"
    fonts.mkdir(parents=True)
    (fonts / "OFL.txt").write_text("SIL Open Font License", encoding="utf-8")
    run_id = "corrida_prueba"
    _write_run(tmp_path, run_id, output)

    zip_path = create_figure_compendium(tmp_path, run_id, "svg")
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        assert "A/figura_a_1.svg" in names
        assert "MANIFIESTO_EXPORTACION.csv" in names
        assert "TEXTOS_Y_POSICIONES.csv" in names
        assert "LEEME.txt" in names
        assert "FUENTES/Noto_Sans/OFL.txt" in names

        manifest = archive.read("MANIFIESTO_EXPORTACION.csv").decode("utf-8-sig")
        positions = archive.read("TEXTOS_Y_POSICIONES.csv").decode("utf-8-sig")
        assert "scripts/figures/figura_a_1.py" in manifest
        assert "editable_text" in manifest
        assert "transparent_background" in manifest
        assert "Texto seleccionable" in positions
        assert "transform" in positions
        assert "svg_group_id" in positions


def test_png_and_jpg_compendia_copy_the_code_generated_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "build" / "figures" / "A" / "figura_a_1.png"
    output.parent.mkdir(parents=True)
    _save_sample_bundle(output)
    run_id = "corrida_raster"
    _write_run(tmp_path, run_id, output)

    for kind in ("png", "jpg"):
        zip_path = create_figure_compendium(tmp_path, run_id, kind)
        with zipfile.ZipFile(zip_path) as archive:
            assert archive.read(f"A/figura_a_1.{kind}") == output.with_suffix(
                f".{kind}"
            ).read_bytes()
            manifest = archive.read("MANIFIESTO_EXPORTACION.csv").decode("utf-8-sig")
            assert f",{kind.upper()}," in manifest
            assert "scripts/figures/figura_a_1.py" in manifest


def test_svg_compendium_refuses_raster_wrapper_fallback(tmp_path: Path) -> None:
    output = tmp_path / "build" / "figures" / "A" / "figura_a_1.png"
    output.parent.mkdir(parents=True)
    Image.new("RGB", (100, 50), "white").save(output)
    output.with_suffix(".svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">'
        '<image width="100" height="50" href="data:image/png;base64,AAAA"/>'
        "</svg>",
        encoding="utf-8",
    )
    _write_run(tmp_path, "corrida_sin_svg", output)

    with pytest.raises(ExportUnavailable, match="texto editable y posicionado"):
        create_figure_compendium(tmp_path, "corrida_sin_svg", "svg")


def test_svg_inspection_requires_positioned_text(tmp_path: Path) -> None:
    svg_path = tmp_path / "manual.svg"
    svg_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><text>Sin posición</text></svg>',
        encoding="utf-8",
    )
    inspection = inspect_svg(svg_path)
    assert inspection.text_elements == 1
    assert not inspection.editable_text


def test_editable_svg_validation_rejects_embedded_raster(tmp_path: Path) -> None:
    svg_path = tmp_path / "mixed.svg"
    svg_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">'
        '<rect width="100" height="50" fill="none"/>'
        '<text x="5" y="15">Texto vectorial</text>'
        '<path d="M 0 0 L 10 10" stroke="black"/>'
        '<image x="0" y="0" width="10" height="10" href="data:image/png;base64,AAAA"/>'
        '</svg>',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="raster"):
        figure_outputs.validate_editable_svg(svg_path, require_fully_vector=True)
