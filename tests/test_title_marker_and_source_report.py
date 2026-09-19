from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pytest

from anuario2026.reports import RunReports
from anuario2026.ui_2024 import (
    TITLE_MARKER,
    TITLE_MARKER_HEIGHT,
    TITLE_MARKER_WIDTH,
    normalize_title_marker,
)


def test_title_marker_matches_a1_geometry_and_is_idempotent() -> None:
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    title = fig.text(.061, .90, "Figura C.5.", fontsize=14, fontweight="bold", va="center")
    legacy_text = fig.text(
        .045,
        .90,
        " ",
        bbox=dict(boxstyle="round,pad=1.5", fc="#4a7d75", ec="none"),
    )
    legacy_patch = mpatches.FancyBboxPatch(
        (.048, .89),
        .020,
        .030,
        transform=fig.transFigure,
        facecolor="#4a7d75",
        edgecolor="none",
    )
    fig.add_artist(legacy_patch)

    normalize_title_marker(fig)
    normalize_title_marker(fig)

    canonical = [
        artist
        for artist in fig.artists
        if getattr(artist, "_anuario_title_marker", False)
    ]
    assert len(canonical) == 1
    marker = canonical[0]
    x, y, width, height = marker.get_bbox().bounds
    assert x == pytest.approx(.047)
    assert y == pytest.approx(.891)
    assert width == pytest.approx(TITLE_MARKER_WIDTH)
    assert height == pytest.approx(TITLE_MARKER_HEIGHT)
    assert mcolors.to_hex(marker.get_facecolor(), keep_alpha=False) == TITLE_MARKER
    assert title.get_visible()
    assert not legacy_text.get_visible()
    assert not legacy_patch.get_visible()
    plt.close(fig)


def test_run_report_copies_figure_source_reference_catalog(tmp_path: Path) -> None:
    source = tmp_path / "referencias_fuentes_figuras.csv"
    fields = [
        "figura",
        "fuente_source_id",
        "fuente_propietario",
        "archivo_descarga_zip",
        "archivo_real_tabla",
        "portal_origen",
    ]
    row = {
        "figura": "figura_a_1.py",
        "fuente_source_id": "inegi_pibt_2026_q2",
        "fuente_propietario": "INEGI",
        "archivo_descarga_zip": "PIBT_2.xlsx",
        "archivo_real_tabla": "PIBT_2.xlsx",
        "portal_origen": "https://www.inegi.org.mx/programas/pib/",
    }
    with source.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)

    reports = RunReports(tmp_path, "corrida_prueba", dry_run=True)
    generated = reports.write_figure_source_reference_report()

    with generated.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows == [row]
