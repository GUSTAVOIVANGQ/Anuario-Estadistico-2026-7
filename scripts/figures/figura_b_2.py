"""Figura B.2: servicios de telecomunicaciones por hogar, ámbito rural."""

from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui

import sys
import zipfile
from pathlib import Path, PurePosixPath

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch


FIGURE_ID = "B.2"
SOURCE_ID = "inegi_endutih_2025"
SOURCE_YEAR = 2025
SOURCE_URL = "https://www.inegi.org.mx/programas/endutih/2025/"
DOMAIN = "R"
TITLE = "Distribución de los Servicios Fijos con respecto del total de hogares en las zonas rurales"
TOTAL_LABEL = "Total de hogares en zonas\nrurales en México:"

C_TRES = "#317DA1"
C_DOS = "#F2535A"
C_UNO = "#A8DCE0"
C_NINGUNO = "#F28D7D"
C_TEXT = "#4B4B7D"


def _configure_fonts(project_root: Path) -> None:
    font_dir = project_root / "assets" / "fonts" / "Noto_Sans"
    for name in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf"):
        path = font_dir / name
        if path.is_file():
            font_manager.fontManager.addfont(path)
    available = {font.name for font in font_manager.fontManager.ttflist}
    plt.rcParams.update({
        "font.family": "Noto Sans" if "Noto Sans" in available else "DejaVu Sans",
        "axes.unicode_minus": False,
    })


def _find_table(archive: zipfile.ZipFile, table: str) -> str:
    expected = f"tr_endutih_{table}_anual_{SOURCE_YEAR}.csv"
    matches = [
        name for name in archive.namelist()
        if PurePosixPath(name.replace("\\", "/")).name.casefold() == expected.casefold()
    ]
    if not matches:
        raise ValueError(f"El ZIP ENDUTIH no contiene {expected}")
    return matches[0]


def load_hogares(raw_path: Path) -> pd.DataFrame:
    required = ["P4_4", "P4_5", "P5_1", "P5_5", "DOMINIO", "FAC_HOG"]
    with zipfile.ZipFile(raw_path) as archive:
        member = _find_table(archive, "hogares")
        with archive.open(member) as stream:
            frame = pd.read_csv(stream, usecols=required, dtype=str, low_memory=False)
    frame.columns = [str(column).strip().upper() for column in frame.columns]
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"La tabla de hogares no contiene {missing}")
    return frame


def build_metrics(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Calcula las ocho combinaciones mutuamente excluyentes con FAC_HOG."""
    data = frame.copy()
    for column in ("P4_4", "P4_5", "P5_1", "P5_5", "DOMINIO"):
        data[column] = (
            data[column].astype(str).str.strip().str.upper()
            .str.replace(r"\.0$", "", regex=True)
        )
    data["FAC_HOG"] = pd.to_numeric(data["FAC_HOG"], errors="coerce").fillna(0)
    if DOMAIN is not None:
        data = data.loc[data["DOMINIO"].eq(DOMAIN)].copy()
    if data.empty:
        raise ValueError(f"ENDUTIH {SOURCE_YEAR} no contiene hogares para DOMINIO={DOMAIN}")

    # La conexión fija es P4_4=1 y P4_5=1 (solo fija) o 3 (fija y móvil).
    data["internet_fijo"] = data["P4_4"].eq("1") & data["P4_5"].isin(["1", "3"])
    data["tv_restringida"] = data["P5_1"].eq("1")
    data["telefonia_fija"] = data["P5_5"].eq("1")
    data["num_servicios"] = data[
        ["internet_fijo", "tv_restringida", "telefonia_fija"]
    ].sum(axis=1)
    total = float(data["FAC_HOG"].sum())
    if total <= 0:
        raise ValueError("La suma de FAC_HOG es cero")

    masks = [
        ("Tres servicios", "total", data["num_servicios"].eq(3)),
        ("Dos servicios", "total", data["num_servicios"].eq(2)),
        ("Un servicio", "total", data["num_servicios"].eq(1)),
        ("Ninguno", "total", data["num_servicios"].eq(0)),
        ("Solo TV Restringida", "un_servicio", data["tv_restringida"] & ~data["internet_fijo"] & ~data["telefonia_fija"]),
        ("Solo Telefonía", "un_servicio", data["telefonia_fija"] & ~data["internet_fijo"] & ~data["tv_restringida"]),
        ("Solo Internet", "un_servicio", data["internet_fijo"] & ~data["tv_restringida"] & ~data["telefonia_fija"]),
        ("Internet + Telefonía", "dos_servicios", data["internet_fijo"] & data["telefonia_fija"] & ~data["tv_restringida"]),
        ("TV Restringida + Internet", "dos_servicios", data["tv_restringida"] & data["internet_fijo"] & ~data["telefonia_fija"]),
        ("TV Restringida + Telefonía", "dos_servicios", data["tv_restringida"] & data["telefonia_fija"] & ~data["internet_fijo"]),
    ]
    rows = []
    for category, group, mask in masks:
        expanded = float(data.loc[mask, "FAC_HOG"].sum())
        rows.append({
            "anio": SOURCE_YEAR,
            "dominio": "Nacional" if DOMAIN is None else DOMAIN,
            "grupo": group,
            "categoria": category,
            "hogares_expandidos": round(expanded),
            "porcentaje": expanded / total * 100,
        })
    return pd.DataFrame(rows), round(total)


def _draw_bubble(ax, bx, by, bw, bh, side="left") -> None:
    mid_x, mid_y = bx + bw / 2, by + bh / 2
    tw, td = min(bw, bh) * 0.22, min(bw, bh) * 0.28
    if side == "left":
        p1, p2, tip = (bx, mid_y + tw / 2), (bx, mid_y - tw / 2), (bx - td, mid_y)
    else:
        p1, p2, tip = (bx + bw, mid_y - tw / 2), (bx + bw, mid_y + tw / 2), (bx + bw + td, mid_y)
    ax.add_patch(FancyBboxPatch(
        (bx, by), bw, bh, boxstyle="round,pad=0,rounding_size=0.06",
        linewidth=0.9, edgecolor="#B7B7C5", facecolor="white", zorder=5,
    ))
    ax.add_patch(plt.Polygon([p1, tip, p2], closed=True, facecolor="white",
                             edgecolor="#B7B7C5", linewidth=0.9, zorder=5))
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="white", lw=2.1, zorder=6)


def _draw_panel(fig, left, bottom, width, height, categories, values, colors, title, title_color) -> None:
    background = fig.add_axes([left, bottom, width, height], zorder=2)
    background.set_xlim(0, 1)
    background.set_ylim(0, 1)
    background.axis("off")
    background.add_patch(FancyBboxPatch(
        (0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.025",
        linewidth=1, edgecolor="#C3C3D0", facecolor="#FBFBF7",
        transform=background.transAxes, clip_on=False,
    ))
    fig.text(left + width * 0.06, bottom + height * 0.91, title,
             fontsize=10, color=C_TEXT, fontweight="bold", va="center")
    ax = fig.add_axes([left + width * 0.08, bottom + height * 0.23,
                       width * 0.86, height * 0.57], zorder=3)
    ax.set_facecolor("none")
    x = np.arange(len(categories))
    bars = ax.bar(x, values, width=0.42, color=colors, edgecolor="none")
    ymax = max(max(values), 1)
    ax.set_ylim(0, ymax * 1.55)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + ymax * 0.05,
                f"{value:.0f}%", ha="center", va="bottom", fontsize=11,
                fontweight="bold", color=C_TEXT,
                bbox=dict(boxstyle="round,pad=0.28,rounding_size=0.6",
                          facecolor="white", edgecolor=title_color, linewidth=0.9))
    ax.set_xticks(x, categories, fontsize=8, color=C_TEXT, linespacing=1.15)
    ax.tick_params(left=False, bottom=False, labelleft=False, length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)


def _plot(metrics: pd.DataFrame, total_hogares: int, output_path: Path, project_root: Path) -> None:
    _configure_fonts(project_root)
    totals = metrics.loc[metrics["grupo"].eq("total")].set_index("categoria")["porcentaje"]
    one = metrics.loc[metrics["grupo"].eq("un_servicio")].set_index("categoria")["porcentaje"]
    two = metrics.loc[metrics["grupo"].eq("dos_servicios")].set_index("categoria")["porcentaje"]

    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.text(0.028, 0.952, "   ", fontsize=2, va="center",
             bbox=dict(boxstyle="round,pad=1.6,rounding_size=0.2",
                       facecolor="#F58F82", edgecolor="none"))
    fig.text(0.046, 0.952, "Figura B.2.", fontsize=13, fontweight="bold", color=C_TEXT, va="center")
    fig.text(0.126, 0.952, TITLE, fontsize=13, color=C_TEXT, va="center")

    ax_pie = fig.add_axes([0.0, 0.11, 0.53, 0.78])
    ax_pie.set_aspect("equal")
    ax_pie.set_xlim(-1.65, 1.65)
    ax_pie.set_ylim(-1.38, 1.38)
    ax_pie.axis("off")
    sizes = [totals["Tres servicios"], totals["Dos servicios"], totals["Un servicio"], totals["Ninguno"]]
    colors = [C_TRES, C_DOS, C_UNO, C_NINGUNO]
    ax_pie.pie(sizes, colors=colors, explode=(0.03,) * 4, startangle=90,
               counterclock=False, radius=0.68,
               wedgeprops=dict(linewidth=2, edgecolor="white"))
    bubbles = [
        (0.60, 0.54, 0.62, 0.52, "left", sizes[0], "Tres servicios\n(Telefonía Fija +\nTV Restringida + Internet)"),
        (0.60, -0.68, 0.50, 0.38, "left", sizes[1], "Dos servicios"),
        (-1.23, -0.56, 0.50, 0.38, "right", sizes[2], "Un servicio"),
        (-1.23, 0.24, 0.50, 0.32, "right", sizes[3], "Ninguno"),
    ]
    for bx, by, bw, bh, side, value, label in bubbles:
        _draw_bubble(ax_pie, bx, by, bw, bh, side)
        ax_pie.text(bx + bw / 2, by + bh * 0.68, f"{value:.0f}%", ha="center",
                    va="center", fontsize=21, fontweight="bold", color=C_TEXT, zorder=7)
        ax_pie.text(bx + bw / 2, by + bh * 0.25, label, ha="center", va="center",
                    fontsize=7, color=C_TEXT, linespacing=1.25, zorder=7)
    ax_pie.add_patch(FancyBboxPatch(
        (-1.22, -1.22), 0.82, 0.38, boxstyle="round,pad=0,rounding_size=0.06",
        linewidth=0.9, edgecolor="#B7B7C5", facecolor="white", zorder=5,
    ))
    ax_pie.text(-0.81, -0.945, TOTAL_LABEL, ha="center", fontsize=7.5, color=C_TEXT, zorder=7)
    ax_pie.text(-0.81, -1.12, f"{total_hogares:,}", ha="center", fontsize=12.5,
                fontweight="bold", color=C_TEXT, zorder=7)

    _draw_panel(fig, 0.527, 0.510, 0.448, 0.388,
                ["Solo\nTV Restringida", "Solo\nTelefonía", "Solo\nInternet"],
                [one["Solo TV Restringida"], one["Solo Telefonía"], one["Solo Internet"]],
                ["#74BEC7", "#8BCDD3", C_UNO], "Un servicio", C_UNO)
    _draw_panel(fig, 0.527, 0.103, 0.448, 0.388,
                ["Internet +\nTelefonía", "TV Restringida\n+ Internet", "TV Restringida\n+ Telefonía"],
                [two["Internet + Telefonía"], two["TV Restringida + Internet"], two["TV Restringida + Telefonía"]],
                [C_DOS, "#F47B75", "#F49A88"], "Dos servicios", C_DOS)

    fig.text(0.040, 0.055, "Fuente:", fontweight="bold", fontsize=8, color=C_TEXT)
    fig.text(0.083, 0.055,
             f"IFT con datos de la ENDUTIH {SOURCE_YEAR}, del INEGI. Datos disponibles en {SOURCE_URL}",
             fontsize=8, color=C_TEXT)
    fig.text(0.040, 0.033, "Nota:", fontweight="bold", fontsize=8, color=C_TEXT)
    fig.text(0.073, 0.033, "Los porcentajes pueden no sumar 100% debido al redondeo.",
             fontsize=8, color=C_TEXT)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output_path, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  B.2 | Adquisición o reutilización del ZIP ENDUTIH 2025")
    raw_path = context.acquire_source(SOURCE_ID)
    print("  B.2 | Lectura de hogares rurales y cálculo ponderado de combinaciones")
    metrics, total_hogares = build_metrics(load_hogares(raw_path))
    context.record_source_period(SOURCE_ID, str(SOURCE_YEAR), "AL_DIA")
    context.write_data_used(metrics)
    context.record_calculation("total_hogares", "suma(FAC_HOG)", {"dominio": "R"},
                               total_hogares, "hogares", 0)
    for row in metrics.itertuples(index=False):
        context.record_calculation(
            f"{row.grupo}_{row.categoria}",
            "suma(FAC_HOG donde se cumple la combinación) / suma(FAC_HOG) * 100",
            {"anio": SOURCE_YEAR, "dominio": row.dominio, "hogares_expandidos": row.hogares_expandidos},
            row.porcentaje, "porcentaje", 1,
        )
    totals = metrics.loc[metrics["grupo"].eq("total")]
    most = totals.loc[totals["porcentaje"].idxmax()]
    text_path = context.render_text("b_2.md.j2", {
        "anio": SOURCE_YEAR, "total_hogares": total_hogares,
        "categoria_mayor": most["categoria"], "porcentaje_mayor": most["porcentaje"],
    })
    print("  B.2 | Generación de gráfica PNG")
    _plot(metrics, total_hogares, context.expected_figure_path, context.project_root)
    return {"figure_path": str(context.expected_figure_path), "text_path": str(text_path),
            "source_latest_period": str(SOURCE_YEAR), "rows_used": len(metrics)}


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    src = project_root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from anuario2026.pipeline import run_pipeline
    run_pipeline(project_root, only=FIGURE_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
