"""Figura C.4: uso de servicios móviles por zona geográfica.

Cada ejecución adquiere o reutiliza el ZIP oficial ENDUTIH 2025, lee los
microdatos, calcula los porcentajes con FAC_PER y genera el PNG.
"""

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
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path, PurePosixPath

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd


FIGURE_ID = "C.4"
SOURCE_ID = "inegi_endutih_2025"
SOURCE_YEAR = 2025
SOURCE_URL = "https://www.inegi.org.mx/programas/endutih/2025/"
REQUIRED_COLUMNS = ["EDAD", "P8_1", "P8_4_2", "FAC_PER", "DOMINIO"]

COLOR_TEXT = "#4B4B83"
COLOR_PANEL = "#FCFCF8"
COLOR_BORDER = "#8A8AAF"
COLOR_URBAN_USE = "#F58F82"
COLOR_URBAN_NO_USE = "#F2535A"
COLOR_RURAL_USE = "#ADDCDF"
COLOR_RURAL_NO_USE = "#317DA3"
COLOR_CHIP_BORDER = "#E6E6EA"


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


def _member(archive: zipfile.ZipFile) -> str:
    expected = f"tr_endutih_usuarios2_anual_{SOURCE_YEAR}.csv"
    for name in archive.namelist():
        candidate = PurePosixPath(name.replace("\\", "/")).name
        if candidate.casefold() == expected.casefold():
            return name
    raise ValueError(f"El ZIP ENDUTIH no contiene {expected}")


def load_users2(raw_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(raw_path) as archive:
        with archive.open(_member(archive)) as stream:
            frame = pd.read_csv(
                stream,
                usecols=REQUIRED_COLUMNS,
                dtype=str,
                low_memory=False,
            )
    frame.columns = [str(column).strip().upper() for column in frame.columns]
    missing = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"La tabla usuarios2 no contiene {missing}")
    return frame


def _round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def build_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    """Aplica el estimador validado contra 78/82/63 del anuario 2024."""
    data = frame.copy()
    for column in ("P8_1", "P8_4_2", "DOMINIO"):
        data[column] = (
            data[column].astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
        )
    data["EDAD"] = pd.to_numeric(data["EDAD"], errors="coerce")
    data["FAC_PER"] = pd.to_numeric(data["FAC_PER"], errors="coerce")
    data = data.loc[data["EDAD"].ge(6) & data["FAC_PER"].gt(0)].copy()
    data["usa_servicios_moviles"] = data["P8_1"].eq("1") & data["P8_4_2"].eq("1")

    rows: list[dict[str, object]] = []
    domains = (
        ("Nacional", data["DOMINIO"].isin(["U", "R"])),
        ("Urbano", data["DOMINIO"].eq("U")),
        ("Rural", data["DOMINIO"].eq("R")),
    )
    for zone, mask in domains:
        subset = data.loc[mask]
        population = float(subset["FAC_PER"].sum())
        users = float(
            subset.loc[subset["usa_servicios_moviles"], "FAC_PER"].sum()
        )
        if population <= 0:
            raise ValueError(f"La zona {zone} no tiene población ponderada")
        percentage = users / population * 100
        rounded = _round_half_up(percentage)
        rows.append({
            "anio": SOURCE_YEAR,
            "zona": zone,
            "n_muestral": len(subset),
            "poblacion_6_mas_expandida": round(population),
            "usuarios_servicios_moviles_expandidos": round(users),
            "porcentaje_uso": percentage,
            "porcentaje_no_uso": 100.0 - percentage,
            "porcentaje_uso_grafica": rounded,
            "porcentaje_no_uso_grafica": 100 - rounded,
        })
    return pd.DataFrame(rows)


def _plot(data: pd.DataFrame, output_path: Path, project_root: Path) -> None:
    _configure_fonts(project_root)
    values = data.set_index("zona")
    urban_use = int(values.loc["Urbano", "porcentaje_uso_grafica"])
    urban_no_use = int(values.loc["Urbano", "porcentaje_no_uso_grafica"])
    rural_use = int(values.loc["Rural", "porcentaje_uso_grafica"])
    rural_no_use = int(values.loc["Rural", "porcentaje_no_uso_grafica"])

    fig = plt.figure(figsize=(16, 8.5), facecolor="white")
    background = fig.add_axes([0, 0, 1, 1], zorder=0)
    background.axis("off")
    background.set_xlim(0, 1)
    background.set_ylim(0, 1)

    for x in (0.02, 0.50):
        background.add_patch(patches.FancyBboxPatch(
            (x, 0.08), 0.46, 0.80,
            boxstyle="round,pad=0,rounding_size=0.03",
            facecolor=COLOR_PANEL, edgecolor=COLOR_BORDER, linewidth=1.2,
        ))

    fig.text(
        0.02, 0.93, " ", fontsize=2, va="center",
        bbox=dict(boxstyle="round,pad=1.6,rounding_size=0.2",
                  facecolor="#F58F82", edgecolor="none"),
    )
    fig.text(0.036, 0.93, "Figura C.4.", fontsize=16, fontweight="bold",
             color=COLOR_TEXT, va="center")
    fig.text(
        0.123, 0.93,
        "Porcentaje del uso de los servicios móviles de telecomunicaciones por zona geográfica",
        fontsize=16, fontweight="medium", color=COLOR_TEXT, va="center",
    )

    fig.text(
        0.355, 0.77,
        "Porcentaje de la población de 6\naños o más en zonas urbanas\n"
        "que usan servicios móviles de\nTelecomunicaciones",
        fontsize=14, fontweight="bold", color=COLOR_TEXT, ha="center", va="center",
        linespacing=1.35,
    )
    fig.text(
        0.835, 0.77,
        "Porcentaje de la población de 6\naños o más en zonas rurales\n"
        "que usan servicios móviles de\nTelecomunicaciones",
        fontsize=14, fontweight="bold", color=COLOR_TEXT, ha="center", va="center",
        linespacing=1.35,
    )

    urban_ax = fig.add_axes([0.015, 0.16, 0.33, 0.57], zorder=4)
    rural_ax = fig.add_axes([0.495, 0.16, 0.33, 0.57], zorder=4)
    for axis in (urban_ax, rural_ax):
        axis.axis("off")
        axis.set_facecolor("none")

    urban_ax.pie(
        [urban_no_use, urban_use], colors=[COLOR_URBAN_NO_USE, COLOR_URBAN_USE],
        startangle=90, counterclock=True, explode=(0, 0.025),
        wedgeprops={"linewidth": 2.5, "edgecolor": "white"},
    )
    rural_ax.pie(
        [rural_no_use, rural_use], colors=[COLOR_RURAL_NO_USE, COLOR_RURAL_USE],
        startangle=90, counterclock=True, explode=(0, 0.025),
        wedgeprops={"linewidth": 2.5, "edgecolor": "white"},
    )

    chip = dict(boxstyle="round,pad=0.5", facecolor="white",
                edgecolor=COLOR_CHIP_BORDER, linewidth=1.2)
    label = dict(ha="center", va="center", fontweight="bold", color=COLOR_TEXT)
    fig.text(0.18, 0.805, "No hacen uso de\nservicios móviles", fontsize=12, **label)
    fig.text(0.18, 0.725, f"{urban_no_use}%", fontsize=28, bbox=chip, **label)
    fig.text(0.285, 0.22, f"{urban_use}%", fontsize=31, bbox=chip, **label)
    fig.text(0.285, 0.145, "Hacen uso de\nservicios móviles", fontsize=12, **label)

    fig.text(0.66, 0.805, "No hacen uso de\nservicios móviles", fontsize=12, **label)
    fig.text(0.66, 0.725, f"{rural_no_use}%", fontsize=28, bbox=chip, **label)
    fig.text(0.765, 0.22, f"{rural_use}%", fontsize=31, bbox=chip, **label)
    fig.text(0.765, 0.145, "Hacen uso de\nservicios móviles", fontsize=12, **label)

    fig.text(0.02, 0.03, "Fuente:", fontweight="bold", fontsize=10, color=COLOR_TEXT)
    fig.text(
        0.061, 0.03,
        f"IFT con datos de la ENDUTIH {SOURCE_YEAR}, del INEGI. Datos disponibles en {SOURCE_URL}",
        fontweight="normal", fontsize=10, color=COLOR_TEXT,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  C.4 | Adquisición o reutilización del ZIP ENDUTIH 2025")
    raw_path = context.acquire_source(SOURCE_ID)
    print("  C.4 | Lectura de usuarios2 y cálculo ponderado por zona")
    data = build_metrics(load_users2(raw_path))
    context.record_source_period(SOURCE_ID, str(SOURCE_YEAR), "AL_DIA")
    context.write_data_used(data)
    for row in data.loc[data["zona"].isin(["Urbano", "Rural"])].itertuples(index=False):
        context.record_calculation(
            f"uso_servicios_moviles_{row.zona.lower()}",
            "suma(FAC_PER donde EDAD>=6, P8_1=1 y P8_4_2=1) / suma(FAC_PER de la zona donde EDAD>=6) * 100",
            {
                "anio": SOURCE_YEAR,
                "zona": row.zona,
                "poblacion_expandida": row.poblacion_6_mas_expandida,
                "usuarios_expandidos": row.usuarios_servicios_moviles_expandidos,
            },
            row.porcentaje_uso,
            "porcentaje",
            0,
        )
    urban = data.loc[data["zona"].eq("Urbano")].iloc[0]
    rural = data.loc[data["zona"].eq("Rural")].iloc[0]
    text_path = context.render_text("c_4.md.j2", {
        "anio": SOURCE_YEAR,
        "porcentaje_urbano": float(urban["porcentaje_uso"]),
        "porcentaje_rural": float(rural["porcentaje_uso"]),
        "brecha": float(urban["porcentaje_uso"] - rural["porcentaje_uso"]),
    })
    print("  C.4 | Generación de gráfica PNG")
    _plot(data, context.expected_figure_path, context.project_root)
    return {
        "figure_path": str(context.expected_figure_path),
        "text_path": str(text_path),
        "source_latest_period": str(SOURCE_YEAR),
        "rows_used": len(data),
    }


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
