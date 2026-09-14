"""Figura A.5: Inversión Extranjera Directa en telecomunicaciones."""

from __future__ import annotations

import math
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from openpyxl import load_workbook


FIGURE_ID = "A.5"
TOTAL_SOURCE_ID = "se_ied_general_2026_q2"
ACTIVITY_SOURCE_ID = "se_ied_sector_2026_q2"
TOTAL_FILENAME = "Datos_originales_y_actualizacion__1_.xlsx"
ACTIVITY_FILENAME = "2026_2T_Flujos_TI_AC_3.xlsx"
SOURCE_PAGE = (
    "https://www.gob.mx/se/acciones-y-programas/"
    "competitividad-y-normatividad-inversion-extranjera-directa?state=published"
)

COLOR_TEXT = "#565682"
COLOR_BACKGROUND = "#FBFBF7"
COLOR_MARKER = "#F58F82"
COLOR_MEXICO = "#ACDDE0"
COLOR_TELECOM = "#4E4F82"
FIRST_YEAR = 2013
QUARTER_NAMES = {
    1: "enero-marzo",
    2: "enero-junio",
    3: "enero-septiembre",
    4: "enero-diciembre",
}


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


def _year(value: object) -> int | None:
    try:
        result = int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None
    return result if 1900 <= result <= 2100 else None


def _quarter(period: object) -> int | None:
    normalized = str(period or "").lower()
    for word, quarter in (("marzo", 1), ("junio", 2), ("septiembre", 3), ("diciembre", 4)):
        if word in normalized:
            return quarter
    return None


def read_total_ied(path: Path) -> dict[tuple[int, int], float]:
    """Lee todos los cortes numéricos de la columna de datos actualizados."""
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        worksheet = workbook[workbook.sheetnames[0]]
        header = str(worksheet.cell(2, 4).value or "").lower()
        if "actualiz" not in header:
            raise ValueError(f"{path.name} no contiene la columna de datos actualizados")

        selected: dict[tuple[int, int], float] = {}
        for row in worksheet.iter_rows(min_row=3, values_only=True):
            year = _year(row[0] if row else None)
            quarter = _quarter(row[1] if len(row) > 1 else None)
            value = row[3] if len(row) > 3 else None
            if year is None or year < FIRST_YEAR or quarter is None or value is None:
                continue
            try:
                selected[(year, quarter)] = float(value)
            except (TypeError, ValueError):
                continue
    finally:
        workbook.close()

    if not selected:
        raise ValueError("No se encontraron cortes numéricos de IED total")
    return selected


def read_telecom_ied(path: Path) -> dict[tuple[int, int], float]:
    """Lee el subsector 517 y ubica los trimestres mediante los encabezados."""
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet_name = next(
            (name for name in workbook.sheetnames if "actividad" in name.lower()),
            None,
        )
        if not sheet_name:
            raise ValueError(f"{path.name} no contiene la hoja por actividad económica")
        worksheet = workbook[sheet_name]

        year_by_column: dict[int, int] = {}
        current_year: int | None = None
        for column in range(2, worksheet.max_column + 1):
            heading = worksheet.cell(3, column).value
            parsed = _year(heading)
            if parsed is not None:
                current_year = parsed
            quarter = worksheet.cell(4, column).value
            try:
                quarter_number = int(float(str(quarter).strip()))
            except (TypeError, ValueError):
                continue
            if current_year is not None and quarter_number in {1, 2, 3, 4}:
                year_by_column[column] = current_year * 10 + quarter_number

        target_row: int | None = None
        for row in range(5, worksheet.max_row + 1):
            label = str(worksheet.cell(row, 1).value or "").strip()
            if label.startswith("517 "):
                target_row = row
                break
        if target_row is None:
            raise ValueError("No se encontró el renglón 517 Telecomunicaciones")

        selected: dict[tuple[int, int], float] = {}
        for column, encoded_period in year_by_column.items():
            year, quarter = divmod(encoded_period, 10)
            if year < FIRST_YEAR:
                continue
            value = worksheet.cell(target_row, column).value
            if value is None or str(value).strip() == "C":
                continue
            try:
                selected[(year, quarter)] = float(value)
            except (TypeError, ValueError):
                continue
    finally:
        workbook.close()

    if not selected:
        raise ValueError("No se encontraron cortes numéricos de IED de telecomunicaciones")
    return selected


def calculate_series(
    total_ied: dict[tuple[int, int], float],
    telecom_ied: dict[tuple[int, int], float],
) -> pd.DataFrame:
    common_periods = sorted(set(total_ied) & set(telecom_ied))
    if not common_periods:
        raise ValueError("Las dos fuentes de A.5 no tienen un trimestre común")
    latest_year, _ = common_periods[-1]
    records = []
    for year in range(FIRST_YEAR, latest_year + 1):
        available = [quarter for candidate_year, quarter in common_periods if candidate_year == year]
        if not available:
            raise ValueError(f"Las dos fuentes no tienen datos comunes para {year}")
        quarter = max(available)
        total = float(total_ied[(year, quarter)])
        telecom = float(telecom_ied[(year, quarter)])
        if total == 0:
            raise ValueError(f"La IED total de {year} es cero")
        records.append(
            {
                "anio": year,
                "trimestre": quarter,
                "periodo": QUARTER_NAMES[quarter],
                "ied_mexico_millones_usd": total,
                "ied_telecom_millones_usd": telecom,
                "participacion_telecom_pct": telecom / total * 100,
            }
        )
    return pd.DataFrame.from_records(records)


def _input_paths(manual_files: tuple[Path, ...], directory: Path) -> tuple[Path, Path]:
    by_name = {path.name: path for path in manual_files}
    missing = [
        filename
        for filename in (TOTAL_FILENAME, ACTIVITY_FILENAME)
        if filename not in by_name
    ]
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(
            f"A.5 requiere {joined}. Coloca el archivo en {directory} y vuelve a ejecutar. "
            "El programa no descarga estos insumos."
        )
    return by_name[TOTAL_FILENAME], by_name[ACTIVITY_FILENAME]


def _plot(data: pd.DataFrame, output_path: Path, project_root: Path) -> None:
    _configure_fonts(project_root)
    plotted = data.sort_values("anio", ascending=False).reset_index(drop=True)
    years = plotted["anio"].to_numpy(dtype=int)
    mexico = plotted["ied_mexico_millones_usd"].to_numpy(dtype=float)
    telecom = plotted["ied_telecom_millones_usd"].to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(COLOR_BACKGROUND)
    y = np.arange(len(plotted), dtype=float)
    offset = 0.16

    for position, value in zip(y - offset, mexico, strict=True):
        ax.plot(
            [0, value],
            [position, position],
            color=COLOR_MEXICO,
            linewidth=9.2,
            solid_capstyle="round",
            zorder=3,
        )
    for position, value in zip(y + offset, telecom, strict=True):
        ax.plot(
            [0, value],
            [position, position],
            color=COLOR_TELECOM,
            linewidth=9.2,
            solid_capstyle="round",
            zorder=4,
        )

    for index, (total_value, telecom_value) in enumerate(
        zip(mexico, telecom, strict=True)
    ):
        ax.text(
            total_value + 650,
            y[index] - offset,
            f"{total_value:,.0f}",
            va="center",
            ha="left",
            fontsize=8.6,
            color=COLOR_TEXT,
        )
        telecom_x = telecom_value + 650 if telecom_value >= 0 else telecom_value - 650
        ax.text(
            telecom_x,
            y[index] + offset,
            f"{telecom_value:,.2f}",
            va="center",
            ha="left" if telecom_value >= 0 else "right",
            fontsize=8.6,
            color=COLOR_TEXT,
        )

    raw_min = min(float(telecom.min()), 0.0) - 4000
    raw_max = float(mexico.max()) + 5000
    x_min = min(-10000, math.floor(raw_min / 10000) * 10000)
    x_max = max(60000, math.ceil(raw_max / 10000) * 10000)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(-0.72, len(plotted) - 0.28)
    ax.invert_yaxis()
    ax.set_yticks(y, years.astype(str), fontsize=8.8, color=COLOR_TEXT)
    ax.tick_params(axis="y", length=0, pad=10)
    ax.tick_params(axis="x", labelsize=8.6, colors=COLOR_TEXT, length=0, pad=7)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(10000))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda value, _: f"{int(value):,}"))
    ax.set_xlabel("Millones de dólares", fontsize=10, color=COLOR_TEXT, labelpad=12)
    ax.set_ylabel("AÑO", fontsize=9.5, color=COLOR_TEXT, labelpad=16)
    ax.grid(axis="x", color="#DADAE3", linewidth=0.7, zorder=0)
    ax.axvline(0, color="#B3B3C2", linewidth=0.8, zorder=1)
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.add_artist(
        mpatches.FancyBboxPatch(
            (0.057, 0.918),
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
        0.927,
        "Figura A.5.",
        fontsize=14,
        fontweight="bold",
        color=COLOR_TEXT,
        va="center",
    )
    fig.text(
        0.151,
        0.927,
        "Inversión Extranjera Directa (IED) en telecomunicaciones",
        fontsize=14,
        color=COLOR_TEXT,
        va="center",
    )

    legend_handles = [
        mlines.Line2D([], [], color=COLOR_TELECOM, linewidth=8, solid_capstyle="round"),
        mlines.Line2D([], [], color=COLOR_MEXICO, linewidth=8, solid_capstyle="round"),
    ]
    fig.legend(
        legend_handles,
        [
            "Inversión Extranjera Directa en Telecomunicaciones",
            "Inversión Extranjera Directa de México",
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, 0.115),
        ncol=2,
        fontsize=8.8,
        frameon=False,
        labelcolor=COLOR_TEXT,
        handlelength=2.2,
        columnspacing=2.5,
    )

    source_body = (
        "CRT con datos de la Secretaría de Economía, actualizados al segundo trimestre "
        f"de 2026. Datos disponibles en: {SOURCE_PAGE}."
    )
    latest = plotted.iloc[0]
    latest_year = int(latest["anio"])
    latest_period = str(latest["periodo"])
    notes_body = (
        "Cifras en millones de dólares (dólares corrientes). Rama 5151 Transmisión de "
        "programas de radio y televisión, y Subsector 517 Telecomunicaciones. "
        f"Para {latest_year} las cifras son acumuladas de {latest_period}; para los años "
        "anteriores se utiliza el último trimestre común disponible."
    )
    fig.text(0.055, 0.075, "Fuente:", fontsize=8.0, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(
        0.094,
        0.075,
        textwrap.fill(source_body, width=205),
        fontsize=8.0,
        color=COLOR_TEXT,
        va="top",
    )
    fig.text(0.055, 0.043, "Notas:", fontsize=8.0, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(
        0.091,
        0.043,
        textwrap.fill(notes_body, width=205),
        fontsize=8.0,
        color=COLOR_TEXT,
        va="top",
    )

    fig.subplots_adjust(left=0.09, right=0.955, top=0.85, bottom=0.23)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    manual_directory = context.project_root / "data" / "manual" / FIGURE_ID
    total_path, activity_path = _input_paths(context.manual_files, manual_directory)
    print(f"  A.5 | Insumo manual IED total: {total_path}")
    print(f"  A.5 | Insumo manual IED sector 517: {activity_path}")
    print("  A.5 | El programa no descarga ni reemplaza estos archivos")

    total_ied = read_total_ied(total_path)
    telecom_ied = read_telecom_ied(activity_path)
    data = calculate_series(total_ied, telecom_ied)
    latest_total_period = max(total_ied)
    latest_activity_period = max(telecom_ied)
    context.record_source_period(
        TOTAL_SOURCE_ID,
        f"{latest_total_period[0]}-T{latest_total_period[1]}",
        "ULTIMO_DATO_NUMERICO",
    )
    context.record_source_period(
        ACTIVITY_SOURCE_ID,
        f"{latest_activity_period[0]}-T{latest_activity_period[1]}",
        "ULTIMO_DATO_NUMERICO",
    )
    context.write_data_used(data)

    latest = data.iloc[-1]
    telecom_max = data.loc[data["ied_telecom_millones_usd"].idxmax()]
    telecom_min = data.loc[data["ied_telecom_millones_usd"].idxmin()]
    context.record_calculation(
        "participacion_ied_telecom_ultimo_corte",
        "IED telecomunicaciones del último corte / IED México del último corte * 100",
        {
            "anio": int(latest["anio"]),
            "trimestre": int(latest["trimestre"]),
            "ied_telecom": round(float(latest["ied_telecom_millones_usd"]), 6),
            "ied_mexico": round(float(latest["ied_mexico_millones_usd"]), 6),
        },
        round(float(latest["participacion_telecom_pct"]), 2),
        "porcentaje",
        2,
    )
    context.record_calculation(
        "mayor_ied_telecom_periodo_mostrado",
        "máximo de IED en telecomunicaciones en el periodo mostrado",
        {"periodo": f"2013-{int(latest['anio'])}"},
        {
            "anio": int(telecom_max["anio"]),
            "valor": round(float(telecom_max["ied_telecom_millones_usd"]), 2),
        },
        "millones de dólares",
        2,
    )
    context.record_calculation(
        "menor_ied_telecom_periodo_mostrado",
        "mínimo de IED en telecomunicaciones en el periodo mostrado",
        {"periodo": f"2013-{int(latest['anio'])}"},
        {
            "anio": int(telecom_min["anio"]),
            "valor": round(float(telecom_min["ied_telecom_millones_usd"]), 2),
        },
        "millones de dólares",
        2,
    )

    text_path = context.render_text(
        "a_5.md.j2",
        {
            "anio": int(latest["anio"]),
            "periodo": str(latest["periodo"]),
            "ied_telecom": float(latest["ied_telecom_millones_usd"]),
            "ied_mexico": float(latest["ied_mexico_millones_usd"]),
            "participacion": float(latest["participacion_telecom_pct"]),
            "anio_mayor": int(telecom_max["anio"]),
            "ied_mayor": float(telecom_max["ied_telecom_millones_usd"]),
        },
    )

    output_path = context.expected_figure_path
    print("  A.5 | Generación de gráfica PNG")
    _plot(data, output_path, context.project_root)
    print(f"  A.5 | Gráfica: {output_path}")
    return {
        "figure_path": str(output_path),
        "text_path": str(text_path),
        "detected_period": f"{int(latest['anio'])}-T{int(latest['trimestre'])}",
        "rows_used": len(data),
        "total_input": total_path.name,
        "activity_input": activity_path.name,
        "latest_telecom": round(float(latest["ied_telecom_millones_usd"]), 2),
        "latest_mexico": round(float(latest["ied_mexico_millones_usd"]), 2),
        "latest_share": round(float(latest["participacion_telecom_pct"]), 2),
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
