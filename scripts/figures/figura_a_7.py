"""Figura A.7: hogares con telecomunicaciones fijas por decil de ingreso."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path, PurePosixPath

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FIGURE_ID = "A.7"
SOURCE_ID = "inegi_enigh_2024"
SOURCE_YEAR = 2024
SOURCE_URL = "https://www.inegi.org.mx/programas/enigh/nc/2024/"

# Equivalentes CCIF 2018 de R005, R006, R008-R011 de ENIGH 2022.
FIJAS_CLAVES_2024 = {
    "083101", "083102", "083301", "083401", "083402",
    "083403", "083404", "083405", "083924",
}

COLOR_TEXT = "#3c3c3b"
COLOR_BACKGROUND = "#F8F8FA"
COLOR_MARKER = "#4a7d75"
COLOR_PRIMARY = "#335a5c"
COLOR_SECONDARY = "#86adae"


def _configure_fonts(project_root: Path) -> None:
    font_dir = project_root / "assets" / "fonts" / "Noto_Sans"
    for name in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf"):
        path = font_dir / name
        if path.is_file():
            font_manager.fontManager.addfont(path)
    available = {item.name for item in font_manager.fontManager.ttflist}
    plt.rcParams.update({
        "font.family": "Noto Sans" if "Noto Sans" in available else "DejaVu Sans",
        "axes.unicode_minus": False,
    })


def _member(names: list[str], table: str) -> str:
    table_cf = table.casefold()
    candidates: list[tuple[int, int, str]] = []
    for name in names:
        normalized = name.replace("\\", "/")
        if normalized.endswith("/") or PurePosixPath(normalized).suffix.casefold() != ".csv":
            continue
        base = PurePosixPath(normalized).name.casefold()
        if table_cf not in base:
            continue
        score = (100 if base == f"{table_cf}.csv" else 0)
        score += 80 if base.startswith(f"conjunto_de_datos_{table_cf}_enigh2024") else 0
        score += 20 if "/conjunto_de_datos/" in normalized.casefold() else 0
        candidates.append((score, -len(name), name))
    if not candidates:
        raise ValueError(f"No se encontró la tabla {table}.csv")
    return max(candidates)[2]


def _read_table(archive: zipfile.ZipFile, table: str, required: list[str]) -> pd.DataFrame:
    member = _member(archive.namelist(), table)
    required_set = set(required)
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "latin1"):
        try:
            with archive.open(member) as stream:
                frame = pd.read_csv(
                    stream,
                    dtype=str,
                    low_memory=False,
                    encoding=encoding,
                    usecols=lambda column: str(column).strip().casefold() in required_set,
                )
            frame.columns = [str(column).strip().casefold() for column in frame.columns]
            missing = sorted(required_set - set(frame.columns))
            if missing:
                raise ValueError(f"{member}: faltan columnas {missing}")
            return frame[required]
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise RuntimeError(f"No se pudo leer {table}")


def load_enigh_tables(path: Path) -> tuple[pd.DataFrame, ...]:
    """Lee directamente del ZIP las cuatro tablas usadas por la figura."""
    with zipfile.ZipFile(path) as archive:
        concentrado = _read_table(
            archive, "concentradohogar", ["folioviv", "foliohog", "ing_cor", "factor"]
        )
        hogares = _read_table(
            archive, "hogares", ["folioviv", "foliohog", "telefono", "tv_paga", "conex_inte"]
        )
        gastoshogar = _read_table(
            archive, "gastoshogar", ["folioviv", "foliohog", "clave", "gasto_tri", "gas_nm_tri"]
        )
        gastospersona = _read_table(
            archive, "gastospersona", ["folioviv", "foliohog", "clave", "gasto_tri"]
        )
    return concentrado, hogares, gastoshogar, gastospersona


def _fixed_expenses(gh: pd.DataFrame, gp: pd.DataFrame) -> pd.DataFrame:
    gh = gh.copy()
    gp = gp.copy()
    for frame in (gh, gp):
        frame["clave"] = frame["clave"].astype(str).str.strip().str.upper().str.zfill(6)
    gh["gasto"] = (
        pd.to_numeric(gh["gasto_tri"], errors="coerce").fillna(0)
        + pd.to_numeric(gh["gas_nm_tri"], errors="coerce").fillna(0)
    )
    gp["gasto"] = pd.to_numeric(gp["gasto_tri"], errors="coerce").fillna(0)
    expenses = pd.concat(
        [gh[["folioviv", "foliohog", "clave", "gasto"]],
         gp[["folioviv", "foliohog", "clave", "gasto"]]],
        ignore_index=True,
    )
    return (
        expenses.loc[expenses["clave"].isin(FIJAS_CLAVES_2024)]
        .groupby(["folioviv", "foliohog"], as_index=False)["gasto"]
        .sum()
        .rename(columns={"gasto": "gasto_fijas"})
    )


def build_metrics(
    concentrado: pd.DataFrame,
    hogares: pd.DataFrame,
    gh: pd.DataFrame,
    gp: pd.DataFrame,
) -> pd.DataFrame:
    """Reproduce la lógica validada entregada por el usuario con ENIGH 2024."""
    concentrado = concentrado.copy()
    hogares = hogares.copy()
    concentrado["ing_cor"] = pd.to_numeric(concentrado["ing_cor"], errors="coerce").fillna(0)
    concentrado["factor"] = pd.to_numeric(concentrado["factor"], errors="coerce").fillna(0)
    for column in ("telefono", "tv_paga", "conex_inte"):
        hogares[column] = pd.to_numeric(hogares[column], errors="coerce")

    frame = concentrado.merge(hogares, on=["folioviv", "foliohog"], how="left")
    frame = frame.merge(_fixed_expenses(gh, gp), on=["folioviv", "foliohog"], how="left")
    frame["gasto_fijas"] = frame["gasto_fijas"].fillna(0)
    frame = frame.sort_values("ing_cor").reset_index(drop=True)
    total_factor = float(frame["factor"].sum())
    if total_factor <= 0:
        raise ValueError("La ENIGH 2024 no contiene un factor de expansión válido")
    frame["pct_cum"] = frame["factor"].cumsum() / total_factor
    frame["decil"] = pd.cut(
        frame["pct_cum"], np.linspace(0, 1, 11), labels=range(1, 11), include_lowest=True
    ).astype(int)
    frame["tiene_fijas"] = (
        frame["telefono"].eq(1)
        | frame["conex_inte"].eq(1)
        | frame["tv_paga"].eq(1)
        | frame["gasto_fijas"].gt(0)
    ).astype(int)
    frame["tiene_equipo"] = (
        frame["telefono"].eq(1) | frame["conex_inte"].eq(1) | frame["tv_paga"].eq(1)
    ).astype(int)
    frame["dispone_gasta"] = (frame["tiene_equipo"].eq(1) & frame["gasto_fijas"].gt(0)).astype(int)

    rows: list[dict[str, float | int]] = []
    for decile in range(1, 11):
        subset = frame.loc[frame["decil"].eq(decile)]
        weight = float(subset["factor"].sum())
        if weight <= 0:
            raise ValueError(f"El decil {decile} no contiene hogares ponderados")
        rows.append({
            "anio": SOURCE_YEAR,
            "decil": decile,
            "pct_hogares_con_telecom_fijas": round(
                float((subset["tiene_fijas"] * subset["factor"]).sum() / weight * 100), 1
            ),
            "pct_hogares_disponen_y_gastan": round(
                float((subset["dispone_gasta"] * subset["factor"]).sum() / weight * 100), 1
            ),
            "hogares_expandidos": round(weight),
        })
    return pd.DataFrame(rows)


def _plot(data: pd.DataFrame, output_path: Path, project_root: Path) -> None:
    _configure_fonts(project_root)
    fig, ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(COLOR_BACKGROUND)
    y = np.arange(len(data), dtype=float)
    height = 0.38
    ax.barh(
        y - height / 2,
        data["pct_hogares_con_telecom_fijas"],
        height=height,
        color=COLOR_PRIMARY,
        edgecolor="none",
        label="% Hogares con telecomunicaciones fijas",
        zorder=2,
    )
    ax.barh(
        y + height / 2,
        data["pct_hogares_disponen_y_gastan"],
        height=height,
        color=COLOR_SECONDARY,
        edgecolor="none",
        label="% Hogares que disponen y gastan en telecomunicaciones fijas",
        zorder=2,
    )
    for index, row in data.iterrows():
        ax.text(row["pct_hogares_con_telecom_fijas"] + 1.5, y[index] - height / 2,
                f"{row['pct_hogares_con_telecom_fijas']:.1f}%", va="center", fontsize=9,
                fontweight="normal", color=COLOR_TEXT)
        ax.text(row["pct_hogares_disponen_y_gastan"] + 1.5, y[index] + height / 2,
                f"{row['pct_hogares_disponen_y_gastan']:.1f}%", va="center", fontsize=9,
                fontweight="normal", color=COLOR_TEXT)

    ax.set_yticks(y, data["decil"].astype(int), fontsize=9, color=COLOR_TEXT)
    ax.set_ylabel("Decil de ingreso", fontsize=11, fontweight="medium", color=COLOR_TEXT, labelpad=15)
    ax.set_xlim(0, 108)
    ax.set_ylim(-0.65, 9.65)
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0f}%")
    ax.tick_params(axis="x", labelsize=9, colors=COLOR_TEXT)
    ax.grid(axis="x", color="#d1d1d1", linewidth=1, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("#7c7c7c")
    ax.spines["left"].set_color("#7c7c7c")

    fig.add_artist(mpatches.FancyBboxPatch(
        (0.055, 0.918), 0.007, 0.018, transform=fig.transFigure,
        boxstyle="round,pad=0,rounding_size=0.002", facecolor=COLOR_MARKER, edgecolor="none"
    ))
    fig.text(0.069, 0.927, "Figura A.7.", fontsize=14, fontweight="bold", color=COLOR_TEXT, va="center")
    fig.text(0.145, 0.927, "Porcentaje de hogares con servicios de telecomunicaciones fijas por decil de ingreso",
             fontsize=14, fontweight="medium", color=COLOR_TEXT, va="center")

    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles=handles, labels=labels, loc="lower center", bbox_to_anchor=(0.5, 0.12), ncol=2,
               fontsize=10, frameon=False, labelcolor=COLOR_TEXT, handlelength=2.5)
    fig.text(0.055, 0.057, "Fuente:", fontsize=8, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(0.096, 0.057,
             f"IFT con datos de la ENIGH {SOURCE_YEAR}, del INEGI. Datos disponibles en: {SOURCE_URL}",
             fontsize=8, color=COLOR_TEXT, va="top")
    fig.text(0.055, 0.033, "Notas:", fontsize=8, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(0.093, 0.033,
             "El valor de los deciles de ingreso se determina con el factor de expansión de la encuesta.",
             fontsize=8, color=COLOR_TEXT, va="top")
    fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  A.7 | Adquisición o reutilización del ZIP ENIGH 2024")
    raw_path = context.acquire_source(SOURCE_ID)
    print("  A.7 | Lectura de microdatos y cálculo ponderado por decil")
    data = build_metrics(*load_enigh_tables(raw_path))
    context.record_source_period(SOURCE_ID, str(SOURCE_YEAR), "AL_DIA")
    context.write_data_used(data)
    for row in data.itertuples(index=False):
        context.record_calculation(
            f"hogares_fijas_decil_{row.decil}",
            "suma(indicador * factor) / suma(factor) * 100",
            {"anio": SOURCE_YEAR, "decil": row.decil, "hogares_expandidos": row.hogares_expandidos},
            {"con_servicio_pct": row.pct_hogares_con_telecom_fijas,
             "disponen_y_gastan_pct": row.pct_hogares_disponen_y_gastan},
            "porcentaje", 1,
        )
    first, last = data.iloc[0], data.iloc[-1]
    text_path = context.render_text("a_7.md.j2", {
        "anio": SOURCE_YEAR,
        "decil_menor": int(first["decil"]),
        "pct_menor": float(first["pct_hogares_disponen_y_gastan"]),
        "decil_mayor": int(last["decil"]),
        "pct_mayor": float(last["pct_hogares_disponen_y_gastan"]),
    })
    output_path = context.expected_figure_path
    print("  A.7 | Generación de gráfica PNG")
    _plot(data, output_path, context.project_root)
    return {"figure_path": str(output_path), "text_path": str(text_path),
            "source_latest_period": str(SOURCE_YEAR), "rows_used": len(data)}


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
