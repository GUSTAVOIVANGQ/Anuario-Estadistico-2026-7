"""Figura F.2: empleo por sexo en telecomunicaciones y radiodifusión.

El script adquiere o reutiliza los microdatos ENOE, reconstruye primero la
Figura F.2 del Anuario 2024 y sólo entonces aplica el mismo cálculo al último
corte comparable disponible para el Anuario 2026.
"""

from __future__ import annotations

import sys
import textwrap
import zipfile
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd


FIGURE_ID = "F.2"
CURRENT_SOURCE_ID = "inegi_enoe_2026_q2"
REFERENCE_SOURCE_ID = "inegi_enoe_2024_q2_reference"
CURRENT_PERIOD = "2026-T2"
REFERENCE_PERIOD = "2024-T2"
SOURCE_LANDING_PAGE = "https://www.inegi.org.mx/programas/enoe/15ymas/#microdatos"

REFERENCE_2024 = {
    "telecom_total": 247_172,
    "radio_total": 54_694,
    "telecom_mujeres_pct": 32,
    "telecom_hombres_pct": 68,
    "radio_mujeres_pct": 45,
    "radio_hombres_pct": 55,
}

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
COLUMN_ALIASES = {"ent": ("ent", "cve_ent"), "fac_tri": ("fac_tri", "fac")}

TEXT = "#3c3c3b"
RADIO_WOMEN = "#64a0a1"
RADIO_MEN = "#132b2d"
TELECOM_WOMEN = "#64a0a1"
TELECOM_MEN = "#132b2d"
BACKGROUND = "#F8F8FA"
ACCENT = "#4a7d75"
BORDER = "#D1D1DF"


def _configure_fonts(project_root: Path) -> None:
    font_dir = project_root / "assets" / "fonts" / "Noto_Sans"
    for name in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf"):
        path = font_dir / name
        if path.is_file():
            font_manager.fontManager.addfont(path)
    available = {item.name for item in font_manager.fontManager.ttflist}
    plt.rcParams.update(
        {
            "font.family": "Noto Sans" if "Noto Sans" in available else "DejaVu Sans",
            "axes.unicode_minus": False,
        }
    )


def _find_member(archive: zipfile.ZipFile, token: str) -> str:
    matches = [
        name
        for name in archive.namelist()
        if token.upper() in Path(name).name.upper() and name.upper().endswith(".CSV")
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Se esperaba un CSV {token} y se encontraron {len(matches)} en {archive.filename}"
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
    optional = optional or []
    available = _available_columns(archive, member)
    resolved: dict[str, str] = {}
    for canonical in dict.fromkeys(required + optional):
        for candidate in COLUMN_ALIASES.get(canonical, (canonical,)):
            if candidate in available:
                resolved[canonical] = available[candidate]
                break
    missing = [name for name in required if name not in resolved]
    if missing:
        raise ValueError(f"Faltan columnas {missing} en {member}")
    selected = required + [name for name in optional if name in resolved and name not in required]
    with archive.open(member) as stream:
        frame = pd.read_csv(
            stream,
            encoding="latin1",
            usecols=[resolved[name] for name in selected],
            low_memory=False,
        )
    return frame.rename(columns={resolved[name]: name for name in selected})


def load_enoe(path: Path) -> tuple[pd.DataFrame, dict[str, str | int]]:
    """Lee SDEM/COE1 y cruza personas con la llave completa de la ENOE."""
    if not zipfile.is_zipfile(path):
        raise ValueError(f"El insumo ENOE no es un ZIP válido: {path}")
    with zipfile.ZipFile(path) as archive:
        sdem_member = _find_member(archive, "SDEMT")
        coe1_member = _find_member(archive, "COE1T")
        sdem = _read_columns(
            archive,
            sdem_member,
            list(MERGE_KEYS) + ["sex", "clase1", "clase2", "fac_tri"],
            ["r_def", "c_res", "eda"],
        )
        coe1 = _read_columns(archive, coe1_member, list(MERGE_KEYS) + ["p4a"])

    for key in MERGE_KEYS:
        sdem[key] = pd.to_numeric(sdem[key], errors="raise").astype("int64")
        coe1[key] = pd.to_numeric(coe1[key], errors="raise").astype("int64")
    if sdem.duplicated(list(MERGE_KEYS)).any():
        raise ValueError(f"Llave persona duplicada en {sdem_member}")
    if coe1.duplicated(list(MERGE_KEYS)).any():
        raise ValueError(f"Llave persona duplicada en {coe1_member}")

    for column in ("sex", "clase1", "clase2", "fac_tri", "r_def", "c_res", "eda"):
        if column in sdem.columns:
            sdem[column] = pd.to_numeric(sdem[column], errors="coerce")
    merged = sdem.merge(coe1, on=list(MERGE_KEYS), how="inner", validate="one_to_one")
    merged["p4a"] = pd.to_numeric(merged["p4a"], errors="coerce").astype("Int64").astype("string")
    metadata: dict[str, str | int] = {
        "sdem": sdem_member,
        "coe1": coe1_member,
        "filas_sdem": len(sdem),
        "filas_coe1": len(coe1),
        "filas_cruzadas": len(merged),
    }
    return merged, metadata


def _universe_legacy(frame: pd.DataFrame) -> pd.Series:
    return frame["clase1"].eq(1) & frame["clase2"].eq(1) & frame["fac_tri"].gt(0)


def _universe_documented(frame: pd.DataFrame) -> pd.Series:
    mask = frame["clase2"].eq(1) & frame["fac_tri"].gt(0)
    if "r_def" in frame.columns:
        mask &= frame["r_def"].eq(0)
    if "c_res" in frame.columns:
        mask &= frame["c_res"].isin([1, 3])
    if "eda" in frame.columns:
        mask &= frame["eda"].between(15, 98)
    return mask


MODEL_CANDIDATES: tuple[tuple[str, Callable[[pd.DataFrame], pd.Series]], ...] = (
    ("clase1=1, clase2=1 y fac_tri>0", _universe_legacy),
    ("universo ENOE documentado", _universe_documented),
)


def calculate(
    frame: pd.DataFrame, universe_fn: Callable[[pd.DataFrame], pd.Series]
) -> tuple[pd.DataFrame, int]:
    """Suma FAC_TRI por SCIAN 515/517 y sexo declarado en SEX."""
    occupied = frame.loc[universe_fn(frame)].copy()

    def sector_row(name: str, prefix: str) -> dict[str, int | float | str]:
        sector = occupied.loc[occupied["p4a"].str.startswith(prefix, na=False)]
        women = float(sector.loc[sector["sex"].eq(2), "fac_tri"].sum())
        men = float(sector.loc[sector["sex"].eq(1), "fac_tri"].sum())
        total = women + men
        if total <= 0:
            raise ValueError(f"El sector {name} produjo un total ponderado no positivo")
        return {
            "sector": name,
            "scian": prefix,
            "mujeres": int(round(women)),
            "hombres": int(round(men)),
            "total": int(round(total)),
            "mujeres_pct": women / total * 100,
            "hombres_pct": men / total * 100,
        }

    rows = [
        sector_row("Radiodifusión", "515"),
        sector_row("Telecomunicaciones", "517"),
    ]
    return pd.DataFrame(rows), len(occupied)


def reference_matches(data: pd.DataFrame) -> bool:
    rows = data.set_index("sector")
    radio = rows.loc["Radiodifusión"]
    telecom = rows.loc["Telecomunicaciones"]
    return bool(
        int(telecom["total"]) == REFERENCE_2024["telecom_total"]
        and int(radio["total"]) == REFERENCE_2024["radio_total"]
        and round(float(telecom["mujeres_pct"])) == REFERENCE_2024["telecom_mujeres_pct"]
        and round(float(telecom["hombres_pct"])) == REFERENCE_2024["telecom_hombres_pct"]
        and round(float(radio["mujeres_pct"])) == REFERENCE_2024["radio_mujeres_pct"]
        and round(float(radio["hombres_pct"])) == REFERENCE_2024["radio_hombres_pct"]
    )


def choose_model(
    reference_frame: pd.DataFrame,
) -> tuple[str, Callable[[pd.DataFrame], pd.Series], pd.DataFrame, int]:
    """Exige reproducción exacta de 2024 antes de aceptar el modelo."""
    attempts: list[str] = []
    for name, function in MODEL_CANDIDATES:
        data, sample = calculate(reference_frame, function)
        indexed = data.set_index("sector")
        attempts.append(
            f"{name}: telecom={int(indexed.loc['Telecomunicaciones', 'total']):,}; "
            f"radio={int(indexed.loc['Radiodifusión', 'total']):,}"
        )
        if reference_matches(data):
            return name, function, data, sample
    raise RuntimeError(
        "Ningún universo reprodujo exactamente la Figura F.2 de 2024; "
        "se detiene para no generar cifras no comparables. " + " | ".join(attempts)
    )


def _chip(ax: plt.Axes, x: float, y: float, text: str, size: float = 18) -> None:
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=TEXT,
        fontsize=size,
        fontweight="bold",
        bbox={
            "boxstyle": "round,pad=0.48,rounding_size=0.55",
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.98,
        },
        clip_on=False,
        zorder=8,
    )


def _sector_panel(
    fig: plt.Figure,
    rect: tuple[float, float, float, float],
    row: pd.Series,
    women_color: str,
    men_color: str,
) -> None:
    left, bottom, width, height = rect
    fig.add_artist(
        patches.FancyBboxPatch(
            (left, bottom),
            width,
            height,
            transform=fig.transFigure,
            boxstyle="round,pad=0.006,rounding_size=0.018",
            facecolor=BACKGROUND,
            edgecolor=BORDER,
            linewidth=1.0,
            zorder=0,
        )
    )
    fig.text(
        left + width / 2,
        bottom + height + 0.018,
        str(row.name),
        ha="center",
        va="center",
        fontsize=19,
        fontweight="bold",
        color=TEXT,
        bbox={
            "boxstyle": "round,pad=.55,rounding_size=.8",
            "facecolor": "white",
            "edgecolor": "none",
        },
        zorder=10,
    )

    ax = fig.add_axes([left + 0.035, bottom + 0.075, width * 0.60, height * 0.72])
    ax.set_zorder(3)
    ax.patch.set_alpha(0)
    ax.set_aspect("equal")
    ax.axis("off")
    women_pct = float(row["mujeres_pct"])
    boundary = 90 + women_pct / 100 * 180
    ax.add_patch(patches.Wedge((0, 0), 1.0, 90, boundary, facecolor=women_color, edgecolor="white", linewidth=3))
    ax.add_patch(patches.Wedge((0, 0), 1.0, boundary, 270, facecolor=men_color, edgecolor="white", linewidth=3))
    ax.set_xlim(-1.07, 0.50)
    ax.set_ylim(-1.08, 1.08)

    _chip(ax, 0.84, 0.76, f"{women_pct:.0f}%")
    ax.text(0.84, 0.87, "Mujeres", transform=ax.transAxes, ha="center", va="center", color=TEXT, fontsize=10, fontweight="bold", clip_on=False)
    _chip(ax, 0.86, 0.25, f"{float(row['hombres_pct']):.0f}%")
    ax.text(0.86, 0.12, "Hombres", transform=ax.transAxes, ha="center", va="center", color=TEXT, fontsize=10, fontweight="bold", clip_on=False)

    fig.text(
        left + width * 0.76,
        bottom + height * 0.61,
        f"Total de personas\nempleadas en {str(row.name).lower()}:",
        ha="center",
        va="center",
        color=TEXT,
        fontsize=9,
        linespacing=1.15,
    )
    fig.text(
        left + width * 0.76,
        bottom + height * 0.50,
        f"{int(row['total']):,}",
        ha="center",
        va="center",
        color=TEXT,
        fontsize=23,
        fontweight="bold",
        bbox={
            "boxstyle": "round,pad=.62,rounding_size=.7",
            "facecolor": "white",
            "edgecolor": "none",
        },
    )
def _plot(data: pd.DataFrame, output: Path, project_root: Path, period: str) -> None:
    _configure_fonts(project_root)
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.add_artist(
        patches.FancyBboxPatch(
            (0.035, 0.105),
            0.93,
            0.80,
            transform=fig.transFigure,
            boxstyle="round,pad=.006,rounding_size=.02",
            facecolor=BACKGROUND,
            edgecolor="none",
            zorder=-1,
        )
    )
    fig.add_artist(
        patches.FancyBboxPatch(
            (0.052, 0.858),
            0.008,
            0.018,
            transform=fig.transFigure,
            boxstyle="round,pad=0,rounding_size=.003",
            facecolor=ACCENT,
            edgecolor="none",
        )
    )
    fig.text(0.066, 0.867, "Figura F.2.", fontsize=15, fontweight="bold", color=TEXT, va="center")
    fig.text(
        0.153,
        0.867,
        "Porcentaje de personas empleadas en telecomunicaciones y radiodifusión",
        fontsize=15,
        color=TEXT,
        va="center",
    )

    rows = data.set_index("sector")
    _sector_panel(fig, (0.058, 0.205, 0.425, 0.56), rows.loc["Radiodifusión"], RADIO_WOMEN, RADIO_MEN)
    _sector_panel(fig, (0.517, 0.205, 0.425, 0.56), rows.loc["Telecomunicaciones"], TELECOM_WOMEN, TELECOM_MEN)

    year, quarter = period.split("-T")
    month = {"1": "marzo", "2": "junio", "3": "septiembre", "4": "diciembre"}[quarter]
    fig.text(0.052, 0.148, "Fuente:", fontsize=9.2, fontweight="bold", color=TEXT, va="top")
    fig.text(
        0.099,
        0.148,
        textwrap.fill(
            f"IFT con datos de la Encuesta Nacional de Ocupación y Empleo (ENOE) a {month} de {year}, del INEGI. Datos disponibles en {SOURCE_LANDING_PAGE}",
            width=180,
        ),
        fontsize=9.2,
        color=TEXT,
        va="top",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200, facecolor="white", bbox_inches=None)
    plt.close(fig)


def generate(context):
    print("  F.2 | 1/5 Reutilización o descarga de ENOE 2024-T2")
    reference_source = context.acquire_source(REFERENCE_SOURCE_ID)
    print("  F.2 | 2/5 Reutilización o descarga de ENOE 2026-T2")
    current_source = context.acquire_source(CURRENT_SOURCE_ID)

    print("  F.2 | 3/5 Reconstrucción obligatoria de la figura publicada en 2024")
    reference_frame, reference_meta = load_enoe(reference_source)
    model_name, model_fn, reference_data, reference_sample = choose_model(reference_frame)
    del reference_frame
    print("  F.2 | Validación 2024 exacta: APROBADA")
    print(reference_data.to_string(index=False, formatters={"mujeres_pct": lambda x: f"{x:.2f}%", "hombres_pct": lambda x: f"{x:.2f}%"}))

    print("  F.2 | 4/5 Aplicación del mismo modelo a 2026-T2")
    current_frame, current_meta = load_enoe(current_source)
    data, current_sample = calculate(current_frame, model_fn)
    del current_frame
    data.insert(0, "periodo", CURRENT_PERIOD)
    print("\n  F.2 | Datos usados en la gráfica:")
    print(data.to_string(index=False, formatters={"mujeres_pct": lambda x: f"{x:.2f}%", "hombres_pct": lambda x: f"{x:.2f}%"}))

    context.record_source_period(REFERENCE_SOURCE_ID, REFERENCE_PERIOD, "REFERENCIA_REPRODUCIDA")
    context.record_source_period(CURRENT_SOURCE_ID, CURRENT_PERIOD, "AL_DIA")
    context.write_data_used(data)
    context.record_calculation(
        "validacion_modelo_2024",
        "sum(fac_tri) por SCIAN 515/517 y sexo; coincidencia exacta de totales y porcentajes redondeados publicados",
        {"periodo": REFERENCE_PERIOD, "modelo": model_name, "muestra_ocupada": reference_sample, **reference_meta},
        "APROBADA",
        "validación",
    )
    for row in data.itertuples(index=False):
        slug = "radio" if row.sector == "Radiodifusión" else "telecom"
        context.record_calculation(
            f"empleo_{slug}_por_sexo",
            "personas_sexo = sum(fac_tri); porcentaje_sexo = personas_sexo / (mujeres + hombres) * 100",
            {
                "periodo": CURRENT_PERIOD,
                "scian": row.scian,
                "mujeres": row.mujeres,
                "hombres": row.hombres,
                "muestra_ocupada": current_sample,
                **current_meta,
            },
            {"total": row.total, "mujeres_pct": round(row.mujeres_pct, 2), "hombres_pct": round(row.hombres_pct, 2)},
            "personas y porcentaje",
            2,
        )

    indexed = data.set_index("sector")
    summary = (
        f"En junio de 2026, telecomunicaciones registró {int(indexed.loc['Telecomunicaciones', 'total']):,} "
        f"personas empleadas: {indexed.loc['Telecomunicaciones', 'mujeres_pct']:.0f}% mujeres y "
        f"{indexed.loc['Telecomunicaciones', 'hombres_pct']:.0f}% hombres. Radiodifusión registró "
        f"{int(indexed.loc['Radiodifusión', 'total']):,}: {indexed.loc['Radiodifusión', 'mujeres_pct']:.0f}% "
        f"mujeres y {indexed.loc['Radiodifusión', 'hombres_pct']:.0f}% hombres."
    )
    text_path = context.render_text("f_2.md.j2", {"resumen": summary})
    print("  F.2 | 5/5 Generación de gráfica PNG")
    _plot(data, context.expected_figure_path, context.project_root, CURRENT_PERIOD)
    print(f"  F.2 | Gráfica: {context.expected_figure_path}")
    return {
        "figure_path": str(context.expected_figure_path),
        "text_path": str(text_path),
        "detected_period": CURRENT_PERIOD,
        "reference_validation": "exacta",
        "model": model_name,
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
