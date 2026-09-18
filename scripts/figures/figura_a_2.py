"""Figura A.2: microdatos ENOE, cálculo del empleo sectorial y gráfica PNG."""

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
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


FIGURE_ID = "A.2"
SOURCE_LANDING_PAGE = "https://www.inegi.org.mx/programas/enoe/15ymas/#microdatos"
MERGE_KEYS = (
    "cd_a",
    "ent",
    "con",
    "upm",
    "d_sem",
    "n_pro_viv",
    "v_sel",
    "n_hog",
    "h_mud",
    "n_ent",
    "per",
    "n_ren",
)

COLOR_TEXT = "#3c3c3b"
COLOR_TELECOM = "#335a5c"
COLOR_RADIO = "#86adae"
COLOR_BACKGROUND = "#F8F8FA"
COLOR_MARKER = "#4a7d75"
COLOR_TOTAL = "#3c3c3b"
COLUMN_ALIASES = {
    # INEGI cambió esta etiqueta desde 2025-T4; el significado y la llave
    # permanecen iguales en SDEM y COE1.
    "ent": ("ent", "cve_ent"),
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


def _member(archive: zipfile.ZipFile, token: str) -> str:
    matches = [
        name
        for name in archive.namelist()
        if token in name.upper() and name.upper().endswith(".CSV")
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Se esperaba un archivo {token} y se encontraron {len(matches)} en {archive.filename}"
        )
    return matches[0]


def _available_columns(archive: zipfile.ZipFile, member: str) -> dict[str, str]:
    with archive.open(member) as stream:
        header = pd.read_csv(stream, encoding="latin1", nrows=0)
    return {str(column).strip().lower(): str(column) for column in header.columns}


def _read_columns(
    archive: zipfile.ZipFile,
    member: str,
    required: list[str],
    optional: list[str] | None = None,
) -> pd.DataFrame:
    available = _available_columns(archive, member)
    requested = required + [name for name in (optional or []) if name not in required]
    resolved: dict[str, str] = {}
    for name in requested:
        for candidate in COLUMN_ALIASES.get(name, (name,)):
            if candidate in available:
                resolved[name] = available[candidate]
                break
    missing = [name for name in required if name not in resolved]
    if missing:
        raise ValueError(f"Faltan columnas {missing} en {member}")
    selected = required + [name for name in (optional or []) if name in resolved]
    original = [resolved[name] for name in selected]
    with archive.open(member) as stream:
        frame = pd.read_csv(
            stream,
            encoding="latin1",
            usecols=original,
            low_memory=False,
        )
    return frame.rename(columns={resolved[name]: name for name in selected})


def extract_period(path: Path, year: int, quarter: int) -> dict[str, int | float | str]:
    """Calcula A.2 con llaves completas de persona para impedir cruces duplicados."""
    with zipfile.ZipFile(path) as archive:
        sdem_member = _member(archive, "SDEM")
        coe1_member = _member(archive, "COE1")
        sdem = _read_columns(
            archive,
            sdem_member,
            list(MERGE_KEYS) + ["clase1", "clase2"],
            ["fac_tri", "fac"],
        )
        coe1 = _read_columns(archive, coe1_member, list(MERGE_KEYS) + ["p4a"])

    factor = "fac_tri" if "fac_tri" in sdem.columns else "fac"
    if factor not in sdem.columns:
        raise ValueError(f"No se encontró factor trimestral en {path.name}")

    for key in MERGE_KEYS:
        sdem[key] = pd.to_numeric(sdem[key], errors="raise").astype("int64")
        coe1[key] = pd.to_numeric(coe1[key], errors="raise").astype("int64")
    if sdem.duplicated(list(MERGE_KEYS)).any() or coe1.duplicated(list(MERGE_KEYS)).any():
        raise ValueError(f"Las llaves completas de persona no son únicas en {path.name}")

    merged = sdem.merge(
        coe1,
        on=list(MERGE_KEYS),
        how="inner",
        validate="one_to_one",
    )
    occupied = merged.loc[
        pd.to_numeric(merged["clase1"], errors="coerce").eq(1)
        & pd.to_numeric(merged["clase2"], errors="coerce").eq(1)
    ].copy()
    occupied["factor"] = pd.to_numeric(occupied[factor], errors="coerce")
    occupied["sector"] = (
        pd.to_numeric(occupied["p4a"], errors="coerce").astype("Int64").astype("string")
    )
    telecom = float(occupied.loc[occupied["sector"].str.startswith("517"), "factor"].sum())
    radio = float(occupied.loc[occupied["sector"].str.startswith("515"), "factor"].sum())
    telecom_i = int(round(telecom))
    radio_i = int(round(radio))
    total = telecom_i + radio_i
    if telecom_i <= 0 or radio_i <= 0:
        raise ValueError(f"Resultado sectorial no válido en {year}-T{quarter}: {path.name}")
    return {
        "periodo": f"{year}-T{quarter}",
        "anio": year,
        "trimestre": quarter,
        "telecomunicaciones_personas": telecom_i,
        "radiodifusion_personas": radio_i,
        "total_personas": total,
        "telecomunicaciones_pct": round(telecom_i / total * 100, 6),
        "radiodifusion_pct": round(radio_i / total * 100, 6),
        "filas_sdem": len(sdem),
        "filas_coe1": len(coe1),
        "filas_cruzadas": len(merged),
        "personas_ocupadas_muestra": len(occupied),
    }


def _plot(data: pd.DataFrame, output_path: Path, project_root: Path) -> None:
    font_family = _configure_fonts(project_root)
    fig, ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(COLOR_BACKGROUND)
    x = np.arange(len(data), dtype=float)
    width = 0.72

    ax.bar(
        x,
        data["telecomunicaciones_pct"],
        width=width,
        color=COLOR_TELECOM,
        edgecolor="none",
        label="Telecomunicaciones",
        zorder=2,
    )
    ax.bar(
        x,
        data["radiodifusion_pct"],
        width=width,
        bottom=data["telecomunicaciones_pct"],
        color=COLOR_RADIO,
        edgecolor="none",
        label="Radiodifusión",
        zorder=2,
    )

    for position, row in zip(x, data.itertuples(index=False), strict=True):
        telecom_pct = float(row.telecomunicaciones_pct)
        radio_pct = float(row.radiodifusion_pct)
        chip_style = {
            "boxstyle": "round,pad=0.3,rounding_size=0.8",
            "facecolor": "white",
            "edgecolor": COLOR_TELECOM,
            "linewidth": 0.8,
        }
        ax.text(
            position,
            telecom_pct / 2,
            f"{telecom_pct:.0f}%",
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            color=COLOR_TEXT,
            bbox=chip_style,
            zorder=4,
        )
        ax.text(
            position,
            telecom_pct + radio_pct / 2,
            f"{radio_pct:.0f}%",
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            color=COLOR_TEXT,
            bbox=chip_style,
            zorder=4,
        )
        ax.text(
            position,
            102,
            f"{int(row.total_personas):,}",
            rotation=90,
            ha="center",
            va="bottom",
            fontsize=9,
            color=COLOR_TOTAL,
        )

    quarter_labels = {1: "I", 2: "II", 3: "III", 4: "IV"}
    ax.set_xticks(
        x,
        [quarter_labels[int(value)] for value in data["trimestre"]],
        fontsize=8,
        color=COLOR_TEXT,
    )
    ax.tick_params(axis="x", length=3, pad=4, colors=COLOR_TEXT)
    ax.set_ylim(0, 125)
    ax.set_xlim(-0.8, len(data) - 0.2)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(20))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda value, _: f"{int(value)}%"))
    ax.tick_params(axis="y", labelsize=9, colors=COLOR_TEXT)
    ax.set_ylabel(
        "Distribución porcentual del empleo",
        fontsize=11,
        fontweight="medium",
        color=COLOR_TEXT,
        labelpad=15,
        fontfamily=font_family,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("#7c7c7c")
    ax.spines["left"].set_color("#7c7c7c")
    ax.grid(axis="y", color="#d1d1d1", linewidth=1, zorder=0)

    for year, group in data.groupby("anio", sort=True):
        positions = [float(data.index.get_loc(index)) for index in group.index]
        center = sum(positions) / len(positions)
        ax.text(
            center,
            -9,
            str(int(year)),
            ha="center",
            va="top",
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXT,
            clip_on=False,
        )

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
    fig.text(0.071, 0.927, "Figura A.2.", fontsize=14, fontweight="bold", color=COLOR_TEXT, va="center")
    fig.text(
        0.151,
        0.927,
        "Empleo en los sectores de telecomunicaciones y radiodifusión",
        fontsize=14,
        fontweight="medium",
        color=COLOR_TEXT,
        va="center",
    )

    handles, labels = ax.get_legend_handles_labels()
    fig.legend(
        handles=handles,
        labels=labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.08),
        ncol=2,
        fontsize=10,
        frameon=False,
        labelcolor=COLOR_TEXT,
        handlelength=2.5,
    )

    latest = data.iloc[-1]
    month = {1: "marzo", 2: "junio", 3: "septiembre", 4: "diciembre"}[
        int(latest["trimestre"])
    ]
    source_body = (
        "IFT con datos de la Encuesta Nacional de Ocupación y Empleo (ENOE) del INEGI, "
        f"con cifras a {month} {int(latest['anio'])}. Datos disponibles en: "
        f"{SOURCE_LANDING_PAGE}"
    )
    notes_body = "Para el año 2020 se considera la información al primer y cuarto trimestre."
    fig.text(0.055, 0.080, "Fuente:", fontsize=8.2, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(
        0.094,
        0.080,
        textwrap.fill(source_body, width=210),
        fontsize=8.2,
        color=COLOR_TEXT,
        va="top",
        linespacing=1.25,
    )
    fig.text(0.055, 0.048, "Notas:", fontsize=8.2, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(0.091, 0.048, notes_body, fontsize=8.2, color=COLOR_TEXT, va="top")

    fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    downloader_dir = context.project_root / "scripts" / "downloaders"
    if str(downloader_dir) not in sys.path:
        sys.path.insert(0, str(downloader_dir))
    from inegi_enoe_playwright import download

    print("  A.2 | Adquisición y verificación de microdatos ENOE")
    raw_dir = context.project_root / "data" / "raw" / "inegi_enoe_a2"
    downloads = download(raw_dir, context.project_root)
    for item in downloads:
        context.register_raw_source(
            item.spec.source_id,
            item.path,
            owner="INEGI",
            title="ENOE, población de 15 años y más, microdatos CSV",
            expected_period=item.spec.period,
            detected_period=item.spec.period,
            landing_page=SOURCE_LANDING_PAGE,
            exact_url=item.spec.url,
            cache_status=item.cache_status,
            downloaded_at=item.acquired_at,
            source_last_modified=item.source_last_modified,
            content_type=item.content_type,
        )

    records: list[dict[str, int | float | str]] = []
    for index, item in enumerate(downloads, start=1):
        print(f"  A.2 | Cálculo {index:02d}/{len(downloads)}: {item.spec.period}")
        records.append(extract_period(item.path, item.spec.year, item.spec.quarter))
    data = pd.DataFrame.from_records(records).sort_values(["anio", "trimestre"]).reset_index(drop=True)
    context.write_data_used(data)

    latest = data.iloc[-1]
    detected_period = str(latest["periodo"])
    latest_total = int(latest["total_personas"])
    latest_telecom_pct = float(latest["telecomunicaciones_pct"])
    latest_radio_pct = float(latest["radiodifusion_pct"])
    context.record_calculation(
        "empleo_tyr_ultimo_periodo",
        "telecomunicaciones_personas + radiodifusion_personas",
        {
            "periodo": detected_period,
            "telecomunicaciones_personas": int(latest["telecomunicaciones_personas"]),
            "radiodifusion_personas": int(latest["radiodifusion_personas"]),
        },
        latest_total,
        "personas",
        0,
    )
    context.record_calculation(
        "distribucion_ultimo_periodo",
        "personas_sector / total_personas * 100",
        {"periodo": detected_period, "total_personas": latest_total},
        {
            "telecomunicaciones_pct": round(latest_telecom_pct, 2),
            "radiodifusion_pct": round(latest_radio_pct, 2),
        },
        "porcentaje",
        2,
    )

    prior = data.loc[
        (data["trimestre"].eq(int(latest["trimestre"])))
        & (data["anio"].lt(int(latest["anio"])))
    ].iloc[-1]
    variation = (latest_total / int(prior["total_personas"]) - 1) * 100
    context.record_calculation(
        "variacion_anual_empleo_tyr",
        "(total_ultimo / total_mismo_trimestre_previo - 1) * 100",
        {
            "periodo_ultimo": detected_period,
            "total_ultimo": latest_total,
            "periodo_previo": str(prior["periodo"]),
            "total_previo": int(prior["total_personas"]),
        },
        round(variation, 2),
        "porcentaje",
        2,
    )
    max_row = data.loc[data["total_personas"].idxmax()]
    min_row = data.loc[data["total_personas"].idxmin()]
    context.record_calculation(
        "extremos_serie_empleo_tyr",
        "máximo y mínimo de total_personas en los periodos graficados",
        {"periodos": len(data)},
        {
            "mayor_periodo": str(max_row["periodo"]),
            "mayor_total": int(max_row["total_personas"]),
            "menor_periodo": str(min_row["periodo"]),
            "menor_total": int(min_row["total_personas"]),
        },
        "personas",
        0,
    )

    text_path = context.render_text(
        "a_2.md.j2",
        {
            "anio": int(latest["anio"]),
            "trimestre_ordinal": {1: "primer", 2: "segundo", 3: "tercer", 4: "cuarto"}[
                int(latest["trimestre"])
            ],
            "pct_telecom": latest_telecom_pct,
            "pct_radio": latest_radio_pct,
            "total_personas": latest_total,
        },
    )

    output_path = context.expected_figure_path
    print("  A.2 | Generación de gráfica PNG")
    _plot(data, output_path, context.project_root)
    print(f"  A.2 | Gráfica: {output_path}")
    return {
        "figure_path": str(output_path),
        "text_path": str(text_path),
        "detected_period": detected_period,
        "source_files": len(downloads),
        "rows_used": len(data),
        "latest_total_personas": latest_total,
        "latest_telecom_pct": round(latest_telecom_pct, 2),
        "latest_radio_pct": round(latest_radio_pct, 2),
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
