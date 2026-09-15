"""Figura D.1: disponibilidad de TIC en los hogares, 2010-2025."""

from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui

import math
import sys
import zipfile
from pathlib import Path, PurePosixPath

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import openpyxl
import pandas as pd
from matplotlib import patches


FIGURE_ID = "D.1"
LATEST_YEAR = 2025
HISTORICAL_YEARS = list(range(2010, 2024))
SOURCE_HIST_HOUSEHOLD = "inegi_endutih_2023_tabulado_hnal110"
SOURCE_HIST_TV = "inegi_endutih_2023_tabulado_hnal130"
MICRODATA_SOURCES = {
    2023: "inegi_endutih_2023_reference",
    2024: "inegi_endutih_2024_reference",
    2025: "inegi_endutih_2025",
}

INDICATORS = [
    "Equipo de cómputo",
    "Aparatos de radio",
    "Televisor analógico",
    "Televisor digital",
    "Teléfono celular",
]
COLORS = {
    "Equipo de cómputo": "#F2535A",
    "Aparatos de radio": "#F58F82",
    "Televisor analógico": "#4B4B83",
    "Televisor digital": "#28769B",
    "Teléfono celular": "#A8DADD",
}
TEXT = "#4B4B7D"
BG = "#FBFBF7"

EXPECTED_2023 = {
    "Equipo de cómputo": 44,
    "Aparatos de radio": 43,
    "Televisor analógico": 19,
    "Televisor digital": 82,
    "Teléfono celular": 95,
}


def _round_half_up(value: float) -> int:
    return int(math.floor(float(value) + 0.5))


def load_historical_household(path: Path) -> dict[int, dict[str, float]]:
    """Lee computadora, telefonía celular y radio del tabulado nacional 110."""
    workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
    sheet = workbook.active
    result: dict[int, dict[str, float]] = {}
    for row in sheet.iter_rows(min_row=6, values_only=True):
        digits = "".join(character for character in str(row[0]) if character.isdigit())
        if len(digits) != 4:
            continue
        year = int(digits)
        result[year] = {
            "Equipo de cómputo": float(row[2]),
            "Teléfono celular": float(row[10]),
            "Aparatos de radio": float(row[12]),
        }
    workbook.close()
    return result


def load_historical_tv(path: Path) -> dict[int, dict[str, float]]:
    """Suma las categorías exclusivas y compartidas del tabulado nacional 130."""
    workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
    sheet = workbook.active
    result: dict[int, dict[str, float]] = {}
    for row in sheet.iter_rows(min_row=6, values_only=True):
        digits = "".join(character for character in str(row[0]) if character.isdigit())
        if len(digits) != 4:
            continue
        year = int(digits)
        result[year] = {
            "Televisor digital": float(row[4] or 0) + float(row[8] or 0),
            "Televisor analógico": float(row[6] or 0) + float(row[8] or 0),
        }
    workbook.close()
    return result


def build_historical(path_household: Path, path_tv: Path) -> pd.DataFrame:
    household = load_historical_household(path_household)
    tv = load_historical_tv(path_tv)
    missing = [year for year in HISTORICAL_YEARS if year not in household or year not in tv]
    if missing:
        raise ValueError(f"Los tabulados históricos no contienen los años: {missing}")
    rows = []
    for year in HISTORICAL_YEARS:
        values = {**household[year], **tv[year]}
        rows.extend(
            {"anio": year, "indicador": indicator, "porcentaje": values[indicator],
             "origen_calculo": "tabulado nacional INEGI"}
            for indicator in INDICATORS
        )
    return pd.DataFrame(rows)


def _household_member(archive: zipfile.ZipFile, year: int) -> str:
    expected = f"tr_endutih_hogares_anual_{year}.csv"
    for name in archive.namelist():
        if PurePosixPath(name.replace("\\", "/")).name.casefold() == expected.casefold():
            return name
    raise ValueError(f"El ZIP ENDUTIH {year} no contiene {expected}")


def load_households(path: Path, year: int) -> pd.DataFrame:
    base = [
        "FAC_HOG", "P4_1_1", "P4_1_2", "P4_1_4", "P4_1_6",
        "P4_2_1_1", "P4_2_2_1", "P4_2_3_1",
    ]
    with zipfile.ZipFile(path) as archive:
        member = _household_member(archive, year)
        with archive.open(member) as stream:
            header = pd.read_csv(stream, nrows=0)
        available = {str(column).strip().upper() for column in header.columns}
        parent = ["P4_2_1", "P4_2_2", "P4_2_3"]
        columns = base + [column for column in parent if column in available]
        with archive.open(member) as stream:
            data = pd.read_csv(stream, usecols=columns, low_memory=False)
    data.columns = [str(column).strip().upper() for column in data.columns]
    return data


def _number(data: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(data[column], errors="coerce")


def _yes(data: pd.DataFrame, column: str) -> pd.Series:
    return _number(data, column).eq(1)


def calculate_microdata(data: pd.DataFrame, year: int) -> pd.DataFrame:
    weights = _number(data, "FAC_HOG").fillna(0)
    valid = weights.gt(0)
    denominator = float(weights.loc[valid].sum())
    if denominator <= 0:
        raise ValueError("FAC_HOG no produce un total nacional válido")

    if {"P4_2_1", "P4_2_2", "P4_2_3"}.issubset(data.columns):
        computer = _yes(data, "P4_2_1") | _yes(data, "P4_2_2") | _yes(data, "P4_2_3")
        computer_rule = "P4_2_1=1 o P4_2_2=1 o P4_2_3=1"
    else:
        computer = _yes(data, "P4_2_1_1") | _yes(data, "P4_2_2_1") | _yes(data, "P4_2_3_1")
        computer_rule = "P4_2_1_1=1 o P4_2_2_1=1 o P4_2_3_1=1"

    rules = {
        "Equipo de cómputo": (computer, computer_rule),
        "Aparatos de radio": (_yes(data, "P4_1_1"), "P4_1_1=1"),
        "Televisor analógico": (_yes(data, "P4_1_2"), "P4_1_2=1"),
        "Televisor digital": (_yes(data, "P4_1_4"), "P4_1_4=1"),
        "Teléfono celular": (_yes(data, "P4_1_6"), "P4_1_6=1"),
    }
    rows = []
    for indicator, (mask, rule) in rules.items():
        numerator = float(weights.loc[valid & mask.fillna(False)].sum())
        rows.append({
            "anio": year,
            "indicador": indicator,
            "porcentaje": numerator / denominator * 100,
            "numerador_hogares": round(numerator),
            "denominador_hogares": round(denominator),
            "regla": rule,
            "origen_calculo": "microdatos ENDUTIH",
        })
    return pd.DataFrame(rows)


def validate_reference(data_2023: pd.DataFrame) -> float:
    calculated = data_2023.set_index("indicador")["porcentaje"]
    deviations = []
    for indicator, expected in EXPECTED_2023.items():
        rounded = _round_half_up(calculated[indicator])
        deviations.append(abs(rounded - expected))
        if rounded != expected:
            raise ValueError(
                f"D.1 no reproduce 2023 para {indicator}: {calculated[indicator]:.2f}% "
                f"(redondeado {rounded}%, esperado {expected}%)"
            )
    return float(max(deviations))


def combine_series(historical: pd.DataFrame, calculated: dict[int, pd.DataFrame]) -> pd.DataFrame:
    validation = calculated[2023].set_index("indicador")["porcentaje"]
    result = historical.copy()
    result["validacion_microdatos_2023"] = result["indicador"].map(validation)
    result = pd.concat([result, calculated[2024], calculated[2025]], ignore_index=True)
    result["porcentaje_grafica"] = result["porcentaje"].map(_round_half_up)
    return result


def _configure_font(root: Path) -> str:
    for name in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf"):
        path = root / "assets" / "fonts" / "Noto_Sans" / name
        if path.is_file():
            fm.fontManager.addfont(path)
    return "Noto Sans" if any(item.name == "Noto Sans" for item in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data: pd.DataFrame, output: Path, root: Path) -> None:
    plt.rcParams.update({"font.family": _configure_font(root), "axes.unicode_minus": False})
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.add_artist(patches.FancyBboxPatch(
        (.035, .055), .93, .87, boxstyle="round,pad=.012,rounding_size=.02",
        facecolor=BG, edgecolor="none", transform=fig.transFigure, zorder=-2,
    ))
    fig.text(.055, .885, "•", color="#F58F82", fontsize=20, va="center")
    fig.text(.073, .885, "Figura D.1.", fontsize=16, fontweight="bold", color=TEXT, va="center")
    fig.text(.177, .885, "Disponibilidad de las TIC en los hogares (2010-2025)",
             fontsize=16, color=TEXT, va="center")

    ax = fig.add_axes([.075, .205, .855, .59])
    ax.set_facecolor(BG)
    years = sorted(data["anio"].unique())
    for indicator in INDICATORS:
        subset = data.loc[data.indicador.eq(indicator)].sort_values("anio")
        x = subset["anio"].to_numpy()
        y = subset["porcentaje_grafica"].to_numpy()
        ax.plot(x, y, color=COLORS[indicator], linewidth=1.55, marker="o",
                markersize=3.2, label=indicator, zorder=2)
        offsets = {"Equipo de cómputo": 7, "Aparatos de radio": -11,
                   "Televisor analógico": 7, "Televisor digital": 7,
                   "Teléfono celular": 7}
        for xx, yy in zip(x, y):
            ax.annotate(
                f"{int(yy)}%", (xx, yy), xytext=(0, offsets[indicator]),
                textcoords="offset points", ha="center",
                va="bottom" if offsets[indicator] > 0 else "top",
                fontsize=7.4, color=TEXT, fontweight="bold", zorder=4,
                bbox=dict(boxstyle="round,pad=.24,rounding_size=.65", fc="white", ec="none", alpha=.94),
            )
    ax.set_xlim(min(years) - .35, max(years) + .35)
    ax.set_ylim(0, 105)
    ax.set_xticks(years)
    ax.set_xticklabels(years, fontsize=8, fontweight="bold", color=TEXT)
    ax.set_yticks(np.arange(0, 101, 10), [f"{value}%" for value in range(0, 101, 10)])
    ax.tick_params(axis="both", colors=TEXT, labelsize=8, length=0, pad=7)
    ax.grid(axis="y", color="#E1E2E5", linewidth=.65, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.12), ncol=5, frameon=False,
              fontsize=8.5, labelcolor=TEXT, handlelength=1.5, columnspacing=1.5)

    fig.text(.055, .105, "Fuente:", fontsize=8.4, fontweight="bold", color=TEXT)
    fig.text(.099, .105,
             "IFT con datos del MODUTIH para 2010-2014 y de la ENDUTIH para 2015-2025, del INEGI.",
             fontsize=8.4, color=TEXT)
    fig.text(.055, .077, "Nota:", fontsize=8.4, fontweight="bold", color=TEXT)
    fig.text(.088, .077, "Porcentajes de hogares; las etiquetas se presentan redondeadas al entero más cercano.",
             fontsize=8.4, color=TEXT)
    output.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  D.1 | Descarga o reutilización de tabulados históricos y microdatos ENDUTIH")
    path_household = context.acquire_source(SOURCE_HIST_HOUSEHOLD)
    path_tv = context.acquire_source(SOURCE_HIST_TV)
    historical = build_historical(path_household, path_tv)

    calculated: dict[int, pd.DataFrame] = {}
    for year, source_id in MICRODATA_SOURCES.items():
        raw = context.acquire_source(source_id)
        calculated[year] = calculate_microdata(load_households(raw, year), year)
        context.record_source_period(source_id, str(year), "AL_DIA" if year == LATEST_YEAR else "REFERENCIA")
    context.record_source_period(SOURCE_HIST_HOUSEHOLD, "2010-2023", "REFERENCIA_HISTORICA")
    context.record_source_period(SOURCE_HIST_TV, "2010-2023", "REFERENCIA_HISTORICA")

    deviation = validate_reference(calculated[2023])
    data = combine_series(historical, calculated)
    context.write_data_used(data[["anio", "indicador", "porcentaje", "porcentaje_grafica", "origen_calculo"]])
    context.write_data_used(calculated[2023], "validacion_microdatos_2023")

    for row in data.itertuples(index=False):
        context.record_calculation(
            f"disponibilidad_{row.anio}_{INDICATORS.index(row.indicador) + 1}",
            "sum(FAC_HOG donde el hogar dispone del equipo) / sum(FAC_HOG) * 100",
            {"anio": row.anio, "indicador": row.indicador, "origen": row.origen_calculo},
            row.porcentaje,
            "porcentaje de hogares",
            2,
        )

    current = data.loc[data.anio.eq(LATEST_YEAR)].sort_values("porcentaje", ascending=False)
    maximum, minimum = current.iloc[0], current.iloc[-1]
    text_path = context.render_text("f_digital.md.j2", {
        "resumen": (
            f"En {LATEST_YEAR}, la mayor disponibilidad correspondió a {maximum.indicador.lower()} "
            f"({maximum.porcentaje:.1f}%) y la menor a {minimum.indicador.lower()} "
            f"({minimum.porcentaje:.1f}%)."
        )
    })
    print(f"Validación D.1 contra 2023: desviación máxima {deviation:.0f} puntos tras redondeo")
    print(f"Último periodo calculado: {LATEST_YEAR}")
    print("  D.1 | Generación de gráfica PNG")
    _plot(data, context.expected_figure_path, context.project_root)
    return {
        "figure_path": str(context.expected_figure_path),
        "text_path": str(text_path),
        "source_latest_period": str(LATEST_YEAR),
        "rows_used": len(data),
        "historical_validation_max_deviation_pp": deviation,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "src"))
    from anuario2026.pipeline import run_pipeline

    run_pipeline(root, only=FIGURE_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
