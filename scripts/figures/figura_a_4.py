"""Figura A.4: inversión privada por tipo a partir del ZIP global de BIT."""

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


FIGURE_ID = "A.4"
SOURCE_ID = "crt_bit_todo_2025_q2"
SOURCE_LANDING_PAGE = "https://bit.crt.gob.mx/BitWebApp/descargaDatos.xhtml"
TABLE_BASENAME = "TD_INVERSION_TELECOM_ITE_VA.csv"

COLOR_TEXT = "#3c3c3b"
COLOR_BACKGROUND = "#F8F8FA"
COLOR_MARKER = "#4a7d75"
CATEGORIES = (
    ("infraestructura", "INV_INFRA_E", "Infraestructura", "#234244"),
    ("otros_activos", "INV_OTRO_ACT_E", "Otros Activos", "#4c7d7e"),
    ("activos_no_tangibles", "INV_ACT_NO_TANG_E", "Activos No Tangibles", "#64a0a1"),
    ("no_especificada", "INV_NO_ESP_E", "No Especificada", "#86adae"),
)
TOTAL_COLUMN = "INV_TOTAL_E"


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
    """Convierte los campos BIT con comas, espacios y guiones a valores numéricos."""
    cleaned = (
        series.astype("string")
        .str.strip()
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .replace({"-": pd.NA, "": pd.NA, "nan": pd.NA, "<NA>": pd.NA})
    )
    return pd.to_numeric(cleaned, errors="coerce").fillna(0.0)


def load_bit_table(path: Path) -> pd.DataFrame:
    """Abre sólo la tabla A.4 dentro de TODO.zip, sin extraer los otros miembros."""
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
                data = pd.read_csv(stream, encoding="utf-8")
            except UnicodeDecodeError:
                stream.seek(0)
                data = pd.read_csv(stream, encoding="latin1")
    data = data.rename(columns={str(column): str(column).strip() for column in data.columns})
    required = {"ANIO", TOTAL_COLUMN, *(column for _, column, _, _ in CATEGORIES)}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Faltan columnas {missing} en {TABLE_BASENAME}")
    return data


def calculate_annual_investment(data: pd.DataFrame) -> pd.DataFrame:
    """Replica la lógica validada y expresa los importes en miles de millones."""
    frame = data.copy()
    frame["ANIO"] = pd.to_numeric(frame["ANIO"], errors="coerce")
    numeric_columns = [column for _, column, _, _ in CATEGORIES] + [TOTAL_COLUMN]
    for column in numeric_columns:
        frame[column] = clean_numeric(frame[column])
    frame = frame.loc[frame["ANIO"].between(2013, 2024)].copy()
    frame["ANIO"] = frame["ANIO"].astype(int)
    if frame.empty:
        raise ValueError("BIT no contiene datos de inversión entre 2013 y 2024")

    grouped = frame.groupby("ANIO", sort=True)[numeric_columns].sum() / 1_000_000_000
    records: list[dict[str, int | float]] = []
    for year, row in grouped.iterrows():
        total = float(row[TOTAL_COLUMN])
        if total <= 0:
            raise ValueError(f"La inversión total de {year} no es positiva")
        record: dict[str, int | float] = {
            "anio": int(year),
            "total_miles_millones_pesos": total,
        }
        component_sum = 0.0
        for output, source, _, _ in CATEGORIES:
            value = float(row[source])
            component_sum += value
            record[f"{output}_miles_millones_pesos"] = value
            record[f"{output}_pct"] = value / total * 100
        record["suma_componentes_miles_millones_pesos"] = component_sum
        record["diferencia_componentes_total"] = component_sum - total
        records.append(record)

    result = pd.DataFrame.from_records(records)
    if int(result.iloc[-1]["anio"]) != 2024:
        raise ValueError("La tabla de inversión no termina en 2024 como se esperaba")
    if result["diferencia_componentes_total"].abs().max() > 0.001:
        raise ValueError("La suma de tipos de inversión no coincide con el total publicado")
    return result


def _plot(data: pd.DataFrame, output_path: Path, project_root: Path) -> None:
    _configure_fonts(project_root)
    fig, ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(COLOR_BACKGROUND)
    x = np.arange(len(data), dtype=float)
    width = 0.45
    totals = data["total_miles_millones_pesos"].to_numpy(dtype=float)
    maximum = float(totals.max())
    bottoms = np.zeros(len(data), dtype=float)
    category_bottoms: dict[str, np.ndarray] = {}

    for output, _, label, color in CATEGORIES:
        values = data[f"{output}_miles_millones_pesos"].to_numpy(dtype=float)
        category_bottoms[output] = bottoms.copy()
        container = ax.bar(
            x,
            values,
            width,
            bottom=bottoms,
            color=color,
            edgecolor="white",
            linewidth=0.5,
            label=label,
            zorder=3,
        )
        bottoms += values

    chip_style = {
        "boxstyle": "round,pad=0.3,rounding_size=0.6",
        "facecolor": "white",
        "edgecolor": "#D1D1DF",
        "linewidth": 1.2,
    }
    minimum_distance = maximum * 0.045
    for index, position in enumerate(x):
        total = totals[index]
        ax.text(
            position,
            total + maximum * 0.015,
            f"${total:.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=COLOR_TEXT,
            zorder=6,
        )
        last_y = -minimum_distance
        for category_index, (output, _, _, color) in enumerate(CATEGORIES):
            value = float(data.iloc[index][f"{output}_miles_millones_pesos"])
            if value <= 0.0005:
                continue
            percentage = float(data.iloc[index][f"{output}_pct"])
            center = float(category_bottoms[output][index]) + value / 2
            text_y = max(center, last_y + minimum_distance)
            last_y = text_y
            text_x = position - width / 2 - 0.12
            elbow_x = text_x + 0.02 + category_index * 0.008
            target_x = position - width / 2
            ax.plot(
                [text_x, elbow_x, elbow_x, target_x],
                [text_y, text_y, center, center],
                color="#A0A0B0",
                linewidth=1.2,
                zorder=4,
            )
            ax.annotate(
                f"{percentage:.1f}%",
                xy=(text_x, text_y),
                ha="right",
                va="center",
                fontsize=8,
                fontweight="bold",
                color=color,
                bbox=chip_style,
                zorder=5,
            )

    ax.set_xticks(
        x,
        data["anio"].astype(int).astype(str),
        fontsize=10,
        fontweight="bold",
        color=COLOR_TEXT,
    )
    ax.tick_params(axis="x", length=0, pad=9)
    ax.set_xlim(-0.8, len(data) - 0.2)
    ax.set_ylim(0, maximum * 1.15)
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#7c7c7c")
    ax.spines["bottom"].set_linewidth(1)
    ax.grid(axis="y", color="#d1d1d1", linewidth=1, zorder=0)

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
        "Figura A.4.",
        fontsize=14,
        fontweight="bold",
        color=COLOR_TEXT,
        va="center",
    )
    fig.text(
        0.151,
        0.927,
        "Inversión privada en Telecomunicaciones por tipo de inversión",
        fontsize=14,
        fontweight="medium",
        color=COLOR_TEXT,
        va="center",
    )
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.08),
        ncol=4,
        frameon=False,
        prop={"weight": "bold", "size": 10},
        labelcolor=COLOR_TEXT,
    )

    source_body = (
        "CRT con datos proporcionados por los operadores de telecomunicaciones. "
        "Para cada año la inversión se presenta acumulada al mes de diciembre."
    )
    notes_body = (
        "Cifras en miles de millones de pesos (pesos corrientes de cada año). "
        "Solo se considera la inversión realizada por operadores de servicios de telecomunicaciones."
    )
    fig.text(0.055, 0.078, "Fuente:", fontsize=8.1, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(
        0.094,
        0.078,
        textwrap.fill(source_body, width=205),
        fontsize=8.1,
        color=COLOR_TEXT,
        va="top",
    )
    fig.text(0.055, 0.046, "Notas:", fontsize=8.1, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(
        0.091,
        0.046,
        textwrap.fill(notes_body, width=205),
        fontsize=8.1,
        color=COLOR_TEXT,
        va="top",
    )

    fig.subplots_adjust(left=0.10, right=0.92, top=0.85, bottom=0.18)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  A.4 | Adquisición del ZIP global compartido de BIT")
    raw_path = context.acquire_source(SOURCE_ID)
    print(f"  A.4 | Lectura selectiva de {TABLE_BASENAME}")
    raw_data = load_bit_table(raw_path)
    data = calculate_annual_investment(raw_data)
    context.record_source_period(SOURCE_ID, "2024", "AL_DIA")
    context.write_data_used(data)

    latest = data.iloc[-1]
    previous = data.iloc[-2]
    total_variation = (
        float(latest["total_miles_millones_pesos"])
        / float(previous["total_miles_millones_pesos"])
        - 1
    ) * 100
    category_percentages = {
        label: float(latest[f"{output}_pct"])
        for output, _, label, _ in CATEGORIES
    }
    largest_category = max(category_percentages, key=category_percentages.get)
    context.record_calculation(
        "inversion_total_ultimo_anio",
        "suma de INV_TOTAL_E / 1,000,000,000",
        {"anio": int(latest["anio"])},
        round(float(latest["total_miles_millones_pesos"]), 3),
        "miles de millones de pesos",
        3,
    )
    context.record_calculation(
        "variacion_anual_inversion_total",
        "(inversión total 2024 / inversión total 2023 - 1) * 100",
        {
            "total_2024": round(float(latest["total_miles_millones_pesos"]), 6),
            "total_2023": round(float(previous["total_miles_millones_pesos"]), 6),
        },
        round(total_variation, 2),
        "porcentaje",
        2,
    )
    context.record_calculation(
        "tipo_inversion_mayor_2024",
        "máximo de participación por tipo en el último año",
        {"anio": int(latest["anio"]), "participaciones": category_percentages},
        {
            "categoria": largest_category,
            "porcentaje": round(category_percentages[largest_category], 2),
        },
        "porcentaje",
        2,
    )

    text_path = context.render_text(
        "a_4.md.j2",
        {
            "anio": int(latest["anio"]),
            "total": float(latest["total_miles_millones_pesos"]),
            "variacion": total_variation,
            "categoria_mayor": largest_category.lower(),
            "porcentaje_mayor": category_percentages[largest_category],
        },
    )

    output_path = context.expected_figure_path
    print("  A.4 | Generación de gráfica PNG")
    _plot(data, output_path, context.project_root)
    print(f"  A.4 | Gráfica: {output_path}")
    return {
        "figure_path": str(output_path),
        "text_path": str(text_path),
        "detected_period": "2024",
        "rows_used": len(data),
        "source_member": TABLE_BASENAME,
        "latest_total": round(float(latest["total_miles_millones_pesos"]), 3),
        "annual_variation": round(total_variation, 2),
        "largest_category": largest_category,
        "largest_category_percentage": round(category_percentages[largest_category], 2),
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
