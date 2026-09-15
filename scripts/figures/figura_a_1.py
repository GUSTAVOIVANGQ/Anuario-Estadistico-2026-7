"""Figura A.1: descarga, verifica, calcula y genera la gráfica del PIB y TyR."""

from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui

import re
import sys
import textwrap
import unicodedata
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


FIGURE_ID = "A.1"
SOURCE_ID = "inegi_pibt_2026_q2"
START_YEAR = 2013
SOURCE_LANDING_PAGE = "https://www.inegi.org.mx/programas/pib/"

COLOR_TEXT = "#3c3c3b"
COLOR_BAR = "#86adae"
COLOR_LINE = "#2c3e40"
COLOR_GRID = "#d1d1d1"
COLOR_BACKGROUND = "#F8F8FA"
COLOR_MARKER = "#4a7d75"


def _normalize(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text).strip().lower()


def _find_row(frame: pd.DataFrame, start: int, phrase: str) -> int:
    target = _normalize(phrase)
    for row in range(start, frame.shape[0]):
        label = _normalize(frame.iat[row, 0])
        if target in label:
            return row
    raise ValueError(f"No se encontró la fila requerida: {phrase}")


def _find_constant_price_block(frame: pd.DataFrame) -> int:
    for row in range(frame.shape[0]):
        label = _normalize(frame.iat[row, 0])
        if "millones de pesos a precios de 2018" in label:
            return row
    raise ValueError("El tabulado no contiene el bloque a precios constantes de 2018")


def _parse_year(value: object) -> int | None:
    match = re.search(r"(19|20)\d{2}", _normalize(value))
    return int(match.group(0)) if match else None


def _parse_quarter(value: object) -> int | None:
    match = re.search(r"\bt\s*([1-4])", _normalize(value))
    return int(match.group(1)) if match else None


def extract_quarterly_data(frame: pd.DataFrame, start_year: int = START_YEAR) -> pd.DataFrame:
    """Extrae los trimestres del primer bloque sin depender de filas fijas."""
    block = _find_constant_price_block(frame)
    row_pib = _find_row(frame, block + 1, "producto interno bruto")
    row_radio = _find_row(frame, block + 1, "515 - radio y television")
    row_telecom = _find_row(frame, block + 1, "517 - telecomunicaciones")

    # En el tabulado oficial, el año ocupa una celda combinada y los nombres
    # T1/T2/T3/T4 están en la fila siguiente. Se propaga el año sólo al leer.
    year_row = block - 2
    quarter_row = block - 1
    current_year: int | None = None
    records: list[dict[str, float | int | str]] = []
    for column in range(1, frame.shape[1]):
        parsed_year = _parse_year(frame.iat[year_row, column])
        if parsed_year is not None:
            current_year = parsed_year
        quarter = _parse_quarter(frame.iat[quarter_row, column])
        if current_year is None or current_year < start_year or quarter is None:
            continue

        pib = pd.to_numeric(frame.iat[row_pib, column], errors="coerce")
        telecom = pd.to_numeric(frame.iat[row_telecom, column], errors="coerce")
        radio_tv = pd.to_numeric(frame.iat[row_radio, column], errors="coerce")
        if pd.isna(pib):
            continue
        if pd.isna(telecom) or pd.isna(radio_tv):
            raise ValueError(
                f"El tabulado tiene PIB pero no todos los componentes de TyR en "
                f"{current_year}-T{quarter}"
            )
        records.append(
            {
                "periodo": f"{current_year}-T{quarter}",
                "anio": current_year,
                "trimestre": quarter,
                "pib_millones_pesos": float(pib),
                "telecom_millones_pesos": float(telecom),
                "radio_tv_millones_pesos": float(radio_tv),
            }
        )

    if not records:
        raise ValueError("No se encontraron datos trimestrales desde 2013")
    result = pd.DataFrame.from_records(records).drop_duplicates(
        subset=["anio", "trimestre"], keep="last"
    )
    result = result.sort_values(["anio", "trimestre"]).reset_index(drop=True)
    result["pib_miles_millones_pesos"] = result["pib_millones_pesos"] / 1_000
    result["tyr_millones_pesos"] = (
        result["telecom_millones_pesos"] + result["radio_tv_millones_pesos"]
    )
    result["tyr_miles_millones_pesos"] = result["tyr_millones_pesos"] / 1_000
    result["participacion_tyr_pct"] = (
        result["tyr_millones_pesos"] / result["pib_millones_pesos"] * 100
    )
    result = result.round(
        {
            "pib_millones_pesos": 3,
            "telecom_millones_pesos": 3,
            "radio_tv_millones_pesos": 3,
            "pib_miles_millones_pesos": 6,
            "tyr_millones_pesos": 3,
            "tyr_miles_millones_pesos": 6,
            "participacion_tyr_pct": 6,
        }
    )
    return result


def _configure_fonts(project_root: Path) -> str:
    font_dir = project_root / "assets" / "fonts" / "Noto_Sans"
    for name in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf"):
        path = font_dir / name
        if path.is_file():
            font_manager.fontManager.addfont(path)
    available = {item.name for item in font_manager.fontManager.ttflist}
    family = "Noto Sans" if "Noto Sans" in available else "DejaVu Sans"
    plt.rcParams.update({"font.family": family, "axes.unicode_minus": False})
    return family


def _latest_period_text(year: int, quarter: int) -> tuple[str, str]:
    ordinal = {1: "primer", 2: "segundo", 3: "tercer", 4: "cuarto"}[quarter]
    month = {1: "marzo", 2: "junio", 3: "septiembre", 4: "diciembre"}[quarter]
    return ordinal, month


def _plot(reference_data: pd.DataFrame, output_path: Path, project_root: Path) -> None:
    font_family = _configure_fonts(project_root)
    plotted = reference_data[reference_data["trimestre"].isin([2, 4])].copy()
    if plotted.empty:
        raise ValueError("No existen observaciones T2/T4 para reproducir el diseño de A.1")

    fig, ax1 = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    ax1.set_facecolor(COLOR_BACKGROUND)
    x = np.arange(len(plotted), dtype=float)

    ax1.bar(
        x,
        plotted["pib_miles_millones_pesos"].to_numpy(dtype=float),
        width=0.68,
        color=COLOR_BAR,
        edgecolor="none",
        linewidth=0,
        zorder=2,
    )

    ax1.set_ylabel(
        "PIB Nacional en miles de millones de pesos",
        fontsize=11,
        color=COLOR_TEXT,
        labelpad=14,
        fontfamily=font_family,
    )
    ax1.set_ylim(0, 30_000)
    ax1.yaxis.set_major_locator(mticker.MultipleLocator(5_000))
    ax1.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda value, _: f"{int(value):,}")
    )
    ax1.tick_params(axis="y", colors=COLOR_TEXT, labelsize=9, length=0)
    ax1.grid(axis="y", color=COLOR_GRID, linewidth=0.8, zorder=0)

    quarter_labels = ["II" if value == 2 else "IV" for value in plotted["trimestre"]]
    ax1.set_xticks(x, quarter_labels, fontsize=9, color=COLOR_TEXT)
    ax1.tick_params(axis="x", length=0, pad=8)

    for year, group in plotted.groupby("anio", sort=True):
        visible = [float(plotted.index.get_loc(index)) for index in group.index]
        center = sum(visible) / len(visible)
        ax1.text(
            center,
            -3_650,
            str(int(year)),
            ha="center",
            va="top",
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXT,
            clip_on=False,
        )
        if max(visible) < len(plotted) - 1:
            ax1.vlines(
                max(visible) + 0.5,
                -3_250,
                -1_550,
                color=COLOR_TEXT,
                linewidth=0.6,
                clip_on=False,
            )

    ax2 = ax1.twinx()
    percentages = plotted["participacion_tyr_pct"].to_numpy(dtype=float)
    ax2.plot(
        x,
        percentages,
        color=COLOR_LINE,
        linewidth=1.2,
        marker="o",
        markersize=4.5,
        markerfacecolor=COLOR_LINE,
        markeredgecolor=COLOR_LINE,
        zorder=4,
    )
    ax2.set_ylabel(
        "Porcentaje de participación de los subsectores de las TyR",
        fontsize=11,
        color=COLOR_TEXT,
        labelpad=16,
        fontfamily=font_family,
    )
    ax2.set_ylim(0, 1.8)
    ax2.yaxis.set_major_locator(mticker.MultipleLocator(0.2))
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda value, _: f"{value:.1f}%"))
    ax2.tick_params(axis="y", colors=COLOR_TEXT, labelsize=9, length=0)

    for position, percentage in zip(x, percentages, strict=True):
        ax2.annotate(
            f"{percentage:.1f}%",
            xy=(position, percentage),
            xytext=(0, 13),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color=COLOR_TEXT,
            bbox={
                "boxstyle": "round,pad=0.45,rounding_size=0.7",
                "facecolor": "white",
                "edgecolor": COLOR_LINE,
                "linewidth": 0.8,
                "alpha": 0.98,
            },
            zorder=5,
        )

    for axis in (ax1, ax2):
        for spine in axis.spines.values():
            spine.set_visible(False)
    ax1.set_xlim(-0.65, len(plotted) - 0.35)

    fig.add_artist(
        mpatches.FancyBboxPatch(
            (0.057, 0.916),
            0.007,
            0.018,
            transform=fig.transFigure,
            boxstyle="round,pad=0,rounding_size=0.002",
            facecolor=COLOR_MARKER,
            edgecolor="none",
        )
    )
    fig.text(
        0.071,
        0.925,
        "Figura A.1.",
        fontsize=14,
        fontweight="bold",
        color=COLOR_TEXT,
        va="center",
    )
    fig.text(
        0.151,
        0.925,
        "Producto Interno Bruto (PIB) y contribución del PIB de los subsectores de telecomunicaciones y radiodifusión",
        fontsize=14,
        color=COLOR_TEXT,
        va="center",
    )

    legend_bar = mpatches.Patch(facecolor=COLOR_BAR, edgecolor="none", label="PIB nacional")
    legend_line = plt.Line2D(
        [0],
        [0],
        color=COLOR_LINE,
        marker="o",
        markersize=5,
        linewidth=1.2,
        label="Participación TyR",
    )
    fig.legend(
        handles=[legend_bar, legend_line],
        loc="lower center",
        bbox_to_anchor=(0.5, 0.112),
        ncol=2,
        fontsize=10,
        frameon=False,
        labelcolor=COLOR_TEXT,
        handlelength=1.8,
        columnspacing=5,
    )

    latest = reference_data.iloc[-1]
    _, source_month = _latest_period_text(int(latest["anio"]), int(latest["trimestre"]))
    source_body = (
        f"IFT con datos del INEGI a {source_month} de {int(latest['anio'])}. "
        f"Datos disponibles en: {SOURCE_LANDING_PAGE}."
    )
    notes_body = (
        "PIB a precios constantes de 2018. La participación de los subsectores de TyR "
        "corresponde a la contribución del sector 51 (Información en medios masivos) de "
        "acuerdo con el Sistema de Clasificación Industrial de América del Norte, México "
        "SCIAN 2023, el cual puede consultarse en Clasificadores - Catálogo SCIAN."
    )
    fig.text(
        0.055,
        0.084,
        "Fuente:",
        fontsize=8.2,
        fontweight="bold",
        color=COLOR_TEXT,
        va="top",
    )
    fig.text(0.094, 0.084, source_body, fontsize=8.2, color=COLOR_TEXT, va="top")
    fig.text(
        0.055,
        0.061,
        "Notas:",
        fontsize=8.2,
        fontweight="bold",
        color=COLOR_TEXT,
        va="top",
    )
    fig.text(
        0.091,
        0.061,
        textwrap.fill(notes_body, width=210),
        fontsize=8.2,
        color=COLOR_TEXT,
        va="top",
        linespacing=1.35,
    )

    fig.subplots_adjust(left=0.075, right=0.93, top=0.82, bottom=0.25)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output_path, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  A.1 | Descarga y verificación del tabulado PIBT_2.xlsx")
    raw_path = context.acquire_source(SOURCE_ID)
    frame = pd.read_excel(raw_path, sheet_name="Tabulado", header=None)
    data = extract_quarterly_data(frame)

    latest = data.iloc[-1]
    latest_year = int(latest["anio"])
    latest_quarter = int(latest["trimestre"])
    detected_period = f"{latest_year}-T{latest_quarter}"
    expected_period = "2026-T2"
    assessment = "AL_DIA" if detected_period == expected_period else "REVISAR_PERIODO"
    context.record_source_period(SOURCE_ID, detected_period, assessment)

    print(
        f"  A.1 | Periodo detectado: {detected_period} | "
        f"{len(data):,} observaciones trimestrales desde {START_YEAR}"
    )
    context.write_data_used(data)

    context.record_calculation(
        "pib_miles_millones_ultimo_periodo",
        "pib_millones_pesos / 1000",
        {"periodo": detected_period, "pib_millones_pesos": latest["pib_millones_pesos"]},
        round(float(latest["pib_miles_millones_pesos"]), 2),
        "miles de millones de pesos",
        2,
    )
    context.record_calculation(
        "tyr_miles_millones_ultimo_periodo",
        "(telecom_millones_pesos + radio_tv_millones_pesos) / 1000",
        {
            "periodo": detected_period,
            "telecom_millones_pesos": latest["telecom_millones_pesos"],
            "radio_tv_millones_pesos": latest["radio_tv_millones_pesos"],
        },
        round(float(latest["tyr_miles_millones_pesos"]), 2),
        "miles de millones de pesos",
        2,
    )
    context.record_calculation(
        "participacion_tyr_ultimo_periodo",
        "(telecom_millones_pesos + radio_tv_millones_pesos) / pib_millones_pesos * 100",
        {
            "periodo": detected_period,
            "tyr_millones_pesos": latest["tyr_millones_pesos"],
            "pib_millones_pesos": latest["pib_millones_pesos"],
        },
        round(float(latest["participacion_tyr_pct"]), 4),
        "porcentaje",
        4,
    )

    ordinal, _ = _latest_period_text(latest_year, latest_quarter)
    text_path = context.render_text(
        "a_1.md.j2",
        {
            "trimestre_ordinal": ordinal,
            "anio": latest_year,
            "pib_mmdp": float(latest["pib_miles_millones_pesos"]),
            "tyr_mmdp": float(latest["tyr_miles_millones_pesos"]),
            "pct_tyr": float(latest["participacion_tyr_pct"]),
        },
    )

    output_path = context.expected_figure_path
    print("  A.1 | Generación de gráfica PNG")
    _plot(data, output_path, context.project_root)
    print(f"  A.1 | Gráfica: {output_path}")
    return {
        "figure_path": str(output_path),
        "text_path": str(text_path),
        "source_id": SOURCE_ID,
        "source_file": str(raw_path),
        "detected_period": detected_period,
        "rows_used": len(data),
        "latest_pib_mmdp": round(float(latest["pib_miles_millones_pesos"]), 2),
        "latest_tyr_mmdp": round(float(latest["tyr_miles_millones_pesos"]), 2),
        "latest_tyr_pct": round(float(latest["participacion_tyr_pct"]), 4),
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
