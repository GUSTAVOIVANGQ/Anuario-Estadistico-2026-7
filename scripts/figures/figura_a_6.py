"""Figura A.6: ingresos, egresos y margen del sector de telecomunicaciones."""

from __future__ import annotations

import sys
import textwrap
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FIGURE_ID = "A.6"
SOURCE_ID = "crt_bit_todo_2025_q2"
TABLE_BASENAME = "TD_INGRESOS_TELECOM_ITE_VA.csv"

COLOR_TEXT = "#3c3c3b"
COLOR_BACKGROUND = "#F8F8FA"
COLOR_MARKER = "#4a7d75"
COLOR_EXPENSES = "#335a5c"
COLOR_MARGIN = "#86adae"
COLOR_INCOME_ONLY = "#afafaf"

# La base BIT (INGRESOS_TOTAL_E) trae ingresos por concesionario, pero no el
# desglose de egresos y margen. Ese desglose sólo existe como "margen neto"
# (utilidad como % del ingreso) en las notas técnicas trimestrales que
# publicaba el IFT ("Indicadores de los sectores de Telecomunicaciones y
# Radiodifusión"), Figura I.1.1 / II.1.1 de cada nota. De ahí salen estos
# valores 2017-2024, verificados uno por uno contra el PDF de cada trimestre:
#   https://www.ift.org.mx/estadisticas/notastecnicas
# 2024 quedó completo con la última tanda de notas técnicas que el IFT llegó
# a publicar antes de su extinción (17-oct-2025):
#   1T2024=32% (notatecnica1t2024.pdf), 2T2024=32% (notatecnica2t2024.pdf),
#   3T2024=32% (notatecnica3t2024.pdf), 4T2024=29% (notatecnica4t2024.pdf).
# La CRT, que sustituyó al IFT, no ha retomado ese indicador: su "Reporte de
# Datos del Sector de Telecomunicaciones" trimestral (portal.crt.gob.mx) sólo
# trae ingresos, líneas y accesos, sin margen ni egresos. Por eso 2025 no
# puede completarse con una fuente oficial y se deja fuera de este diccionario
# a propósito -- ver build_series(), que traza sin desglose cualquier
# trimestre ausente aquí en vez de inventar un valor.
MARGIN_PCT_BY_PERIOD = {
    (year, quarter): value
    for (year, quarter), value in zip(
        ((year, quarter) for year in range(2017, 2025) for quarter in range(1, 5)),
        (
            20, 17, 15, 13,
            21, 20, 17, 17,
            25, 25, 26, 27,
            22, 15, 17, 17,
            17, 17, 29, 32,
            32, 30, 30, 30,
            31, 30, 33, 29,
            32, 32, 32, 29,
        ),
        strict=True,
    )
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


def clean_numeric(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype("string")
        .str.strip()
        .str.replace(",", "", regex=False)
        .replace({"-": pd.NA, "": pd.NA, "nan": pd.NA, "<NA>": pd.NA})
    )
    return pd.to_numeric(cleaned, errors="coerce").fillna(0.0)


def load_income_table(path: Path) -> pd.DataFrame:
    """Abre sólo la tabla de ingresos requerida dentro del ZIP compartido."""
    with zipfile.ZipFile(path) as archive:
        matches = [
            name
            for name in archive.namelist()
            if Path(name).name.upper() == TABLE_BASENAME.upper()
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Se esperaba una tabla {TABLE_BASENAME} y se encontraron {len(matches)}"
            )
        with archive.open(matches[0]) as stream:
            try:
                data = pd.read_csv(stream, encoding="utf-8", low_memory=False)
            except UnicodeDecodeError:
                stream.seek(0)
                data = pd.read_csv(stream, encoding="latin1", low_memory=False)
    data.columns = [str(column).strip() for column in data.columns]
    required = {"ANIO", "TRIM", "INGRESOS_TOTAL_E", "I_ANUAL_TRIM"}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Faltan columnas {missing} en {TABLE_BASENAME}")
    return data


def build_series(data: pd.DataFrame) -> tuple[pd.DataFrame, tuple[int, int]]:
    """Actualiza ingresos hasta el último trimestre y desglosa cuando hay margen."""
    frame = data.copy()
    frame = frame.loc[
        frame["I_ANUAL_TRIM"].astype(str).str.strip().eq("Trimestral")
    ].copy()
    frame["ANIO"] = pd.to_numeric(frame["ANIO"], errors="coerce")
    frame["TRIM"] = pd.to_numeric(frame["TRIM"], errors="coerce")
    frame["INGRESOS_TOTAL_E"] = clean_numeric(frame["INGRESOS_TOTAL_E"])
    frame = frame.dropna(subset=["ANIO", "TRIM"])
    frame["ANIO"] = frame["ANIO"].astype(int)
    frame["TRIM"] = frame["TRIM"].astype(int)
    frame = frame.loc[frame["ANIO"] >= 2017]

    income = (
        frame.groupby(["ANIO", "TRIM"], as_index=False)["INGRESOS_TOTAL_E"]
        .sum()
        .sort_values(["ANIO", "TRIM"])
    )
    if income.empty:
        raise ValueError("BIT no contiene ingresos trimestrales desde 2017")
    source_latest_row = income.iloc[-1]
    source_latest = (int(source_latest_row["ANIO"]), int(source_latest_row["TRIM"]))
    income_by_period = {
        (int(row.ANIO), int(row.TRIM)): float(row.INGRESOS_TOTAL_E)
        for row in income.itertuples(index=False)
    }

    missing = sorted(set(MARGIN_PCT_BY_PERIOD) - set(income_by_period))
    if missing:
        raise ValueError(f"Faltan ingresos para los periodos con margen publicado: {missing}")

    records = []
    for (year, quarter), income_value in sorted(income_by_period.items()):
        if (year, quarter) < min(MARGIN_PCT_BY_PERIOD):
            continue
        income_bn = income_value / 1_000_000_000
        margin_pct = MARGIN_PCT_BY_PERIOD.get((year, quarter))
        margin_bn = income_bn * margin_pct / 100 if margin_pct is not None else np.nan
        expenses_bn = income_bn - margin_bn if margin_pct is not None else np.nan
        records.append(
            {
                "anio": year,
                "trimestre": quarter,
                "ingresos_miles_millones_pesos": income_bn,
                "margen_pct": margin_pct,
                "margen_miles_millones_pesos": margin_bn,
                "egresos_miles_millones_pesos": expenses_bn,
                "desglose_disponible": margin_pct is not None,
            }
        )
    return pd.DataFrame.from_records(records), source_latest


def _plot(data: pd.DataFrame, output_path: Path, project_root: Path) -> None:
    _configure_fonts(project_root)
    fig, ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(COLOR_BACKGROUND)

    x = np.arange(len(data), dtype=float)
    width = 0.72
    complete = data["desglose_disponible"].to_numpy(dtype=bool)
    expenses = data["egresos_miles_millones_pesos"].fillna(0).to_numpy(dtype=float)
    margins = data["margen_miles_millones_pesos"].fillna(0).to_numpy(dtype=float)
    incomes = data["ingresos_miles_millones_pesos"].to_numpy(dtype=float)
    maximum = float(incomes.max())

    expense_bars = ax.bar(
        x,
        expenses,
        width=width,
        color=COLOR_EXPENSES,
        edgecolor="none",
        label="Egresos",
        zorder=3,
    )
    margin_bars = ax.bar(
        x,
        margins,
        width=width,
        bottom=expenses,
        color=COLOR_MARGIN,
        edgecolor="none",
        label="Margen",
        zorder=3,
    )

    for index, total in enumerate(incomes):
        if not complete[index]:
            ax.bar(
                index,
                total,
                width=width,
                color=COLOR_INCOME_ONLY,
                edgecolor=COLOR_EXPENSES,
                linewidth=1.0,
                zorder=3,
            )

    chip_style = {
        "boxstyle": "round,pad=0.3,rounding_size=0.8",
        "facecolor": "white",
        "edgecolor": COLOR_EXPENSES,
        "linewidth": 0.8,
    }
    for index, row in data.iterrows():
        if bool(row["desglose_disponible"]):
            center = float(row["egresos_miles_millones_pesos"]) + float(
                row["margen_miles_millones_pesos"]
            ) / 2
            chip_text = f"{int(row['margen_pct'])}%"
        else:
            center = float(row["ingresos_miles_millones_pesos"]) / 2
            chip_text = "Total"
        ax.text(
            index,
            center,
            chip_text,
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            color=COLOR_TEXT,
            bbox=chip_style,
            zorder=5,
        )
        ax.text(
            index,
            float(row["ingresos_miles_millones_pesos"]) + maximum * 0.025,
            f"{float(row['ingresos_miles_millones_pesos']) * 1000:,.0f}",
            rotation=90,
            ha="center",
            va="bottom",
            fontsize=9,
            color=COLOR_TEXT,
        )

    years = sorted(data["anio"].astype(int).unique())
    ax.set_xticks(
        x,
        ["I", "II", "III", "IV"] * len(years),
        fontsize=8,
        color=COLOR_TEXT,
    )
    ax.tick_params(axis="x", length=3, pad=4, colors=COLOR_TEXT)
    for group, year in enumerate(years):
        ax.text(
            group * 4 + 1.5,
            -9,
            str(year),
            ha="center",
            va="top",
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXT,
            clip_on=False,
        )

    ax.set_xlim(-0.75, len(data) - 0.25)
    ax.set_ylim(0, maximum * 1.25)
    ax.set_ylabel(
        "Miles de millones de pesos",
        fontsize=11,
        fontweight="medium",
        color=COLOR_TEXT,
        labelpad=15,
    )
    ax.tick_params(axis="y", labelsize=9, colors=COLOR_TEXT)
    ax.grid(axis="y", color="#d1d1d1", linewidth=1, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("#7c7c7c")
    ax.spines["left"].set_color("#7c7c7c")

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
        "Figura A.6.",
        fontsize=14,
        fontweight="bold",
        color=COLOR_TEXT,
        va="center",
    )
    fig.text(
        0.151,
        0.927,
        "Ingresos, egresos y margen en el sector de telecomunicaciones",
        fontsize=14,
        fontweight="medium",
        color=COLOR_TEXT,
        va="center",
    )

    handles, labels = ax.get_legend_handles_labels()
    handles.append(
        mpatches.Patch(facecolor=COLOR_INCOME_ONLY, edgecolor=COLOR_EXPENSES, linewidth=1.0)
    )
    labels.append("Ingresos totales (sin desglose)")
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.08),
        ncol=3,
        fontsize=10,
        frameon=False,
        labelcolor=COLOR_TEXT,
        handlelength=2.5,
        columnspacing=4.0,
    )

    last_complete_year = int(data.loc[data["desglose_disponible"], "anio"].max())
    last_row = data.iloc[-1]
    last_income_period = (int(last_row["anio"]), int(last_row["trimestre"]))
    source_body = (
        "CRT con datos proporcionados por los operadores de telecomunicaciones, "
        f"BIT actualizado a diciembre de {last_income_period[0]}."
    )
    notes_body = (
        "Cifras en miles de millones de pesos (pesos corrientes de cada año). "
    )
    fig.text(0.055, 0.073, "Fuente:", fontsize=8.0, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(
        0.094,
        0.073,
        textwrap.fill(source_body, width=205),
        fontsize=8.0,
        color=COLOR_TEXT,
        va="top",
    )
    fig.text(0.055, 0.043, "Notas:", fontsize=8.0, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(
        0.091,
        0.043,
        textwrap.fill(notes_body, width=175),
        fontsize=8.0,
        color=COLOR_TEXT,
        va="top",
    )

    fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  A.6 | Adquisición del ZIP global compartido de BIT")
    raw_path = context.acquire_source(SOURCE_ID)
    print(f"  A.6 | Lectura selectiva de {TABLE_BASENAME}")
    raw_data = load_income_table(raw_path)
    data, source_latest = build_series(raw_data)
    source_period = f"{source_latest[0]}-T{source_latest[1]}"
    figure_latest = data.iloc[-1]
    figure_period = f"{int(figure_latest['anio'])}-T{int(figure_latest['trimestre'])}"
    complete_latest = data.loc[data["desglose_disponible"]].iloc[-1]
    complete_period = (
        f"{int(complete_latest['anio'])}-T{int(complete_latest['trimestre'])}"
    )
    context.record_source_period(SOURCE_ID, source_period, "AL_DIA_EN_TABLA")
    context.write_data_used(data)
    print(f"  A.6 | Último ingreso en BIT: {source_period}")
    print(f"  A.6 | Último corte mostrado en la gráfica: {figure_period}")
    print(f"  A.6 | Último corte con desglose de margen y egresos: {complete_period}")

    latest_income = float(complete_latest["ingresos_miles_millones_pesos"])
    latest_expenses = float(complete_latest["egresos_miles_millones_pesos"])
    latest_margin = float(complete_latest["margen_miles_millones_pesos"])
    latest_margin_pct = float(complete_latest["margen_pct"])
    source_latest_value = float(figure_latest["ingresos_miles_millones_pesos"])
    context.record_calculation(
        "ingresos_ultimo_corte_completo",
        "suma de INGRESOS_TOTAL_E / 1,000,000,000",
        {"periodo": complete_period},
        round(latest_income, 3),
        "miles de millones de pesos",
        3,
    )
    context.record_calculation(
        "margen_ultimo_corte_completo",
        "ingresos * margen porcentual / 100",
        {"ingresos": round(latest_income, 6), "margen_pct": latest_margin_pct},
        round(latest_margin, 3),
        "miles de millones de pesos",
        3,
    )
    context.record_calculation(
        "egresos_ultimo_corte_completo",
        "ingresos - margen",
        {"ingresos": round(latest_income, 6), "margen": round(latest_margin, 6)},
        round(latest_expenses, 3),
        "miles de millones de pesos",
        3,
    )
    context.record_calculation(
        "ingresos_ultimo_corte_bit",
        "suma de INGRESOS_TOTAL_E del último trimestre encontrado / 1,000,000,000",
        {"periodo": source_period},
        round(float(source_latest_value), 3),
        "miles de millones de pesos",
        3,
    )

    text_path = context.render_text(
        "a_6.md.j2",
        {
            "anio": int(complete_latest["anio"]),
            "ingresos": latest_income,
            "egresos": latest_expenses,
            "margen": latest_margin,
            "margen_pct": latest_margin_pct,
            "ultimo_anio": int(figure_latest["anio"]),
            "ultimo_ingreso": source_latest_value,
        },
    )

    output_path = context.expected_figure_path
    print("  A.6 | Generación de gráfica PNG")
    _plot(data, output_path, context.project_root)
    print(f"  A.6 | Gráfica: {output_path}")
    return {
        "figure_path": str(output_path),
        "text_path": str(text_path),
        "source_member": TABLE_BASENAME,
        "source_latest_period": source_period,
        "figure_latest_period": figure_period,
        "figure_latest_complete_period": complete_period,
        "rows_used": len(data),
        "latest_complete_income": round(latest_income, 3),
        "latest_complete_expenses": round(latest_expenses, 3),
        "latest_complete_margin": round(latest_margin, 3),
        "latest_complete_margin_pct": round(latest_margin_pct, 1),
        "source_latest_income": round(float(source_latest_value), 3),
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
