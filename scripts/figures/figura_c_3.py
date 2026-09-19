"""Figura C.3: uso nacional de servicios móviles de telecomunicaciones.

El estimador se reconstruyó con ENDUTIH 2023: P8_1=1 y P8_4_2=1,
ponderado con FAC_PER, reproduce 78 % nacional, 82 % urbano y 63 % rural
publicados en el Anuario Estadístico 2024. La misma operación se aplica a la
edición más reciente disponible de los microdatos.
"""

from __future__ import annotations

import math
import sys
import zipfile
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path, PurePosixPath

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import pandas as pd


FIGURE_ID = "C.3"
SOURCE_ID = "inegi_endutih_2025"
SOURCE_YEAR = 2025
SOURCE_URL = "https://www.inegi.org.mx/programas/endutih/2025/"
REQUIRED_COLUMNS = ["EDAD", "P8_1", "P8_4_2", "FAC_PER", "DOMINIO"]

COLOR_TEXT = "#3c3c3b"
COLOR_USE = "#3b6667"
COLOR_NO_USE = "#132b2d"
COLOR_BACKGROUND = "#EAF3F2"
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
    """Lee directamente la tabla de personas dentro del ZIP oficial."""
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
    """Calcula el indicador con el estimador que reproduce el referente 2024."""
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
    national = data.loc[data["zona"].eq("Nacional")].iloc[0]
    uses = int(national["porcentaje_uso_grafica"])
    does_not_use = int(national["porcentaje_no_uso_grafica"])

    leader_color = "#8C8C9A"
    chip_border = "#A9A9B8"

    fig = plt.figure(figsize=(6, 9), facecolor="white")
    background = fig.add_axes([0, 0, 1, 1], zorder=0)
    background.axis("off")
    background.set_xlim(0, 1)
    background.set_ylim(0, 1)

    background.annotate(
        " ", xy=(0.04, 0.945), xytext=(0, 0), textcoords="offset points",
        bbox=dict(boxstyle="round,pad=1.6,rounding_size=0.2",
                  facecolor="#4a7d75", edgecolor="none"),
        fontsize=2, va="center",
    )
    background.annotate(
        "Figura C.3.", xy=(0.04, 0.945), xytext=(15, 0), textcoords="offset points",
        fontsize=14, fontweight="bold", color=COLOR_TEXT, va="center",
    )
    background.annotate(
        "Porcentaje del uso de los servicios\nmóviles de telecomunicaciones",
        xy=(0.04, 0.945), xytext=(105, 0), textcoords="offset points",
        fontsize=14, fontweight="medium", color=COLOR_TEXT, va="center",
    )
    background.text(
        0.5, 0.82, "Población de 6 años o más:", ha="center", va="center",
        fontsize=10, fontweight="bold", color=COLOR_TEXT,
        bbox=dict(boxstyle="round,pad=0.55", facecolor="white",
                  edgecolor=chip_border, linewidth=1.15),
    )

    # El pastel se centra y se reserva espacio real para las llamadas.
    pie = fig.add_axes([0.08, 0.22, 0.76, 0.60], zorder=3)
    pie.set_facecolor("none")
<<<<<<< HEAD
    pie.add_patch(plt.Circle((0, 0), 1.17, facecolor=COLOR_BACKGROUND,
                             edgecolor="none", zorder=-2))
=======
    pie.add_patch(plt.Circle((0, 0), 1.17, facecolor=COLOR_BACKGROUND, edgecolor="none", zorder=-2))
>>>>>>> 93f2bf9f8ee9510be3d7cd1817e28eb1b7e51fc4
    wedges, _ = pie.pie(
        [does_not_use, uses],
        colors=[COLOR_NO_USE, COLOR_USE],
        startangle=90,
        counterclock=True,
        wedgeprops={"linewidth": 2.5, "edgecolor": "white"},
    )
    pie.set_aspect("equal")
    pie.set_xlim(-1.42, 1.42)
    pie.set_ylim(-1.30, 1.38)
    pie.axis("off")
    for wedge, target in zip(wedges, ((1.15, 0.45), (1.15, -0.52))):
        angle = math.radians((wedge.theta1 + wedge.theta2) / 2)
        pie.annotate(
            "", xy=(0.78 * math.cos(angle), 0.78 * math.sin(angle)),
            xytext=target,
            arrowprops=dict(arrowstyle="-", color="#8c8c98", linewidth=1.1,
                            connectionstyle="arc3,rad=0"),
        )

    chip = dict(boxstyle="round,pad=0.45,rounding_size=0.28",
                facecolor="white", edgecolor=chip_border, linewidth=1.25)
    arrow = dict(arrowstyle="-", color=leader_color, linewidth=1.35,
                 shrinkA=8, shrinkB=0, connectionstyle="arc3,rad=0")

    callouts = [
        (wedges[0], (-1.08, 1.03), (-1.30, 1.30),
         f"{does_not_use}%", "No hacen uso de\nservicios móviles"),
        (wedges[1], (1.10, -1.00), (0.92, -0.63),
         f"{uses}%", "Hacen uso de\nservicios móviles"),
    ]
    for wedge, chip_xy, label_xy, pct, label in callouts:
        angle = math.radians((wedge.theta1 + wedge.theta2) / 2)
        target = (0.74 * math.cos(angle), 0.74 * math.sin(angle))
        pie.annotate(
            pct, xy=target, xytext=chip_xy,
            ha="center", va="center", fontsize=17, fontweight="bold",
            color=COLOR_TEXT, bbox=chip, arrowprops=arrow,
            annotation_clip=False, zorder=8,
        )
        pie.scatter(*target, s=36, facecolor="#A9A9B8", edgecolor="white",
                    linewidth=0.8, zorder=9, clip_on=False)
        pie.text(label_xy[0], label_xy[1], label, ha="left", va="center",
                 fontsize=9, fontweight="bold", color=COLOR_TEXT,
                 linespacing=1.25, clip_on=False, zorder=9)

    background.text(0.06, 0.105, "Fuente:", fontweight="bold", fontsize=7.5, color=COLOR_TEXT)
    background.text(
        0.137, 0.105,
        f"IFT con datos de la ENDUTIH {SOURCE_YEAR}, del INEGI. Datos disponibles en",
        fontsize=7.5, color=COLOR_TEXT,
    )
    background.text(0.06, 0.085, SOURCE_URL, fontsize=7.5, color=COLOR_TEXT)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)

def generate(context):
    print("  C.3 | Adquisición o reutilización del ZIP ENDUTIH 2025")
    raw_path = context.acquire_source(SOURCE_ID)
    print("  C.3 | Lectura de usuarios2 y cálculo nacional ponderado")
    data = build_metrics(load_users2(raw_path))
    context.record_source_period(SOURCE_ID, str(SOURCE_YEAR), "AL_DIA")
    context.write_data_used(data)
    national = data.loc[data["zona"].eq("Nacional")].iloc[0]
    context.record_calculation(
        "uso_servicios_moviles_nacional",
        "suma(FAC_PER donde EDAD>=6, P8_1=1 y P8_4_2=1) / suma(FAC_PER donde EDAD>=6) * 100",
        {
            "anio": SOURCE_YEAR,
            "universo": "personas de 6 años o más",
            "poblacion_expandida": int(national["poblacion_6_mas_expandida"]),
            "usuarios_expandidos": int(national["usuarios_servicios_moviles_expandidos"]),
        },
        float(national["porcentaje_uso"]),
        "porcentaje",
        0,
    )
    text_path = context.render_text("c_3.md.j2", {
        "anio": SOURCE_YEAR,
        "porcentaje_uso": float(national["porcentaje_uso"]),
        "porcentaje_no_uso": float(national["porcentaje_no_uso"]),
    })
    print("  C.3 | Generación de gráfica PNG")
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
