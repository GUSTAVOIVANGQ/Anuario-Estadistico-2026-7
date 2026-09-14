"""Figura A.8: gasto en telecomunicaciones fijas por decil de ingreso."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path, PurePosixPath

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


FIGURE_ID = "A.8"
SOURCE_ID = "inegi_enigh_2024"
SOURCE_YEAR = 2024
SOURCE_URL = "https://www.inegi.org.mx/programas/enigh/nc/2024/"
FIJAS_CLAVES_2024 = {
    "083101", "083102", "083301", "083401", "083402",
    "083403", "083404", "083405", "083924",
}
COLOR_TEXT = "#565682"
COLOR_BACKGROUND = "#FBFBF7"
COLOR_MARKER = "#F58F82"
COLOR_BAR = "#327B9E"
COLOR_POINT = "#565682"


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
                frame = pd.read_csv(stream, dtype=str, low_memory=False, encoding=encoding,
                                    usecols=lambda c: str(c).strip().casefold() in required_set)
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
    with zipfile.ZipFile(path) as archive:
        concentrado = _read_table(archive, "concentradohogar", ["folioviv", "foliohog", "ing_cor", "factor"])
        hogares = _read_table(archive, "hogares", ["folioviv", "foliohog", "telefono", "tv_paga", "conex_inte"])
        gh = _read_table(archive, "gastoshogar", ["folioviv", "foliohog", "clave", "gasto_tri", "gas_nm_tri"])
        gp = _read_table(archive, "gastospersona", ["folioviv", "foliohog", "clave", "gasto_tri"])
    return concentrado, hogares, gh, gp


def _fixed_expenses(gh: pd.DataFrame, gp: pd.DataFrame) -> pd.DataFrame:
    gh, gp = gh.copy(), gp.copy()
    for frame in (gh, gp):
        frame["clave"] = frame["clave"].astype(str).str.strip().str.upper().str.zfill(6)
    gh["gasto"] = pd.to_numeric(gh["gasto_tri"], errors="coerce").fillna(0) + pd.to_numeric(
        gh["gas_nm_tri"], errors="coerce").fillna(0)
    gp["gasto"] = pd.to_numeric(gp["gasto_tri"], errors="coerce").fillna(0)
    expenses = pd.concat([
        gh[["folioviv", "foliohog", "clave", "gasto"]],
        gp[["folioviv", "foliohog", "clave", "gasto"]],
    ], ignore_index=True)
    return (expenses.loc[expenses["clave"].isin(FIJAS_CLAVES_2024)]
            .groupby(["folioviv", "foliohog"], as_index=False)["gasto"].sum()
            .rename(columns={"gasto": "gasto_fijas"}))


def build_metrics(concentrado: pd.DataFrame, hogares: pd.DataFrame,
                  gh: pd.DataFrame, gp: pd.DataFrame) -> pd.DataFrame:
    concentrado, hogares = concentrado.copy(), hogares.copy()
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
    frame["decil"] = pd.cut(frame["pct_cum"], np.linspace(0, 1, 11), labels=range(1, 11),
                            include_lowest=True).astype(int)
    frame["dispone_fijas"] = (
        frame["telefono"].eq(1) | frame["conex_inte"].eq(1) | frame["tv_paga"].eq(1)
    )
    frame["dispone_gasta"] = frame["dispone_fijas"] & frame["gasto_fijas"].gt(0)

    rows: list[dict[str, float | int]] = []
    for decile in range(1, 11):
        subset = frame.loc[frame["decil"].eq(decile) & frame["dispone_gasta"]].copy()
        weight = float(subset["factor"].sum())
        if weight <= 0:
            raise ValueError(f"El decil {decile} no contiene hogares con servicio y gasto")
        expense_monthly = float((subset["gasto_fijas"] * subset["factor"]).sum() / weight / 3)
        income_monthly = float((subset["ing_cor"] * subset["factor"]).sum() / weight / 3)
        rows.append({
            "anio": SOURCE_YEAR, "decil": decile,
            "gasto_promedio_mensual_pesos": round(expense_monthly),
            "ingreso_promedio_mensual_pesos": round(income_monthly, 2),
            "gasto_pct_ingreso": round(expense_monthly / income_monthly * 100, 1) if income_monthly else 0,
            "hogares_expandidos": round(weight),
        })
    return pd.DataFrame(rows)


def _rounded_vertical_bar(ax, center: float, width: float, height: float, maximum: float) -> None:
    left, right = center - width / 2, center + width / 2
    radius_x = width / 2
    radius_y = min(maximum * 0.035, height / 3)

    def shape(offset_x: float = 0) -> mpath.Path:
        return mpath.Path(
            [(left + offset_x, 0), (right - radius_x + offset_x, 0),
             (right + offset_x, 0), (right + offset_x, radius_y),
             (right + offset_x, height - radius_y), (right + offset_x, height),
             (right - radius_x + offset_x, height), (left + offset_x, height),
             (left + offset_x, 0), (left + offset_x, 0)],
            [mpath.Path.MOVETO, mpath.Path.LINETO, mpath.Path.CURVE3, mpath.Path.CURVE3,
             mpath.Path.LINETO, mpath.Path.CURVE3, mpath.Path.CURVE3,
             mpath.Path.LINETO, mpath.Path.LINETO, mpath.Path.CLOSEPOLY],
        )

    ax.add_patch(mpatches.PathPatch(shape(width * 0.10), facecolor="#C8C8C8",
                                    edgecolor="none", alpha=0.22, zorder=1))
    ax.add_patch(mpatches.PathPatch(shape(), facecolor=COLOR_BAR, edgecolor="none", zorder=2))


def _plot(data: pd.DataFrame, output_path: Path, project_root: Path) -> None:
    _configure_fonts(project_root)
    fig, ax_pct = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    ax_pct.set_facecolor(COLOR_BACKGROUND)
    ax_cost = ax_pct.twinx()
    x = np.arange(len(data), dtype=float)
    costs = data["gasto_promedio_mensual_pesos"].to_numpy(float)
    pcts = data["gasto_pct_ingreso"].to_numpy(float)
    for position, cost in zip(x, costs, strict=True):
        _rounded_vertical_bar(ax_cost, position, 0.52, cost, float(costs.max()))
        ax_cost.text(position, max(cost * 0.035, 8), f"${cost:,.0f}",
                     ha="center", va="bottom", fontsize=8, fontweight="bold", color="white", zorder=4)
    ax_pct.scatter(x, pcts, color=COLOR_POINT, s=34, zorder=6)
    for position, pct in zip(x, pcts, strict=True):
        ax_pct.annotate(f"{pct:.1f}%", (position, pct), xytext=(0, 12), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=COLOR_TEXT,
                        bbox={"boxstyle": "round,pad=0.35,rounding_size=0.45", "facecolor": "white",
                              "edgecolor": "#E2E3EA", "linewidth": 0.8}, zorder=7)
    cost_max = max(100, int(np.ceil(costs.max() * 1.18 / 100) * 100))
    pct_max = max(1.0, float(np.ceil(pcts.max() * 1.22 * 2) / 2))
    ax_cost.set_ylim(0, cost_max)
    ax_pct.set_ylim(0, pct_max)
    ax_pct.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.1f}%"))
    ax_cost.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: "$-" if v == 0 else f"${v:,.0f}"))
    ax_pct.set_ylabel("% Gasto con respecto al ingreso", fontsize=9.5, color=COLOR_TEXT, labelpad=12)
    ax_cost.set_ylabel("Gasto promedio mensual", fontsize=9.5, color=COLOR_TEXT, rotation=270, labelpad=17)
    ax_pct.set_xticks(x, data["decil"].astype(int), fontsize=9, color=COLOR_TEXT)
    ax_pct.set_xlabel("Decil de ingreso", fontsize=9.5, fontweight="bold", color=COLOR_TEXT, labelpad=9)
    ax_pct.set_xlim(-0.65, len(data) - 0.35)
    ax_pct.tick_params(axis="both", colors=COLOR_TEXT, labelsize=8.5, length=0)
    ax_cost.tick_params(axis="y", colors=COLOR_TEXT, labelsize=8.5, length=0)
    ax_pct.grid(False); ax_cost.grid(False)
    for axis in (ax_pct, ax_cost):
        for spine in axis.spines.values():
            spine.set_visible(False)

    fig.add_artist(mpatches.FancyBboxPatch(
        (0.055, 0.918), 0.007, 0.018, transform=fig.transFigure,
        boxstyle="round,pad=0,rounding_size=0.002", facecolor=COLOR_MARKER, edgecolor="none"))
    fig.text(0.069, 0.927, "Figura A.8.", fontsize=14, fontweight="bold", color=COLOR_TEXT, va="center")
    fig.text(0.145, 0.927,
             "Gasto promedio y porcentaje de gasto en Servicios de Telecomunicaciones Fijas de los hogares por decil de ingreso",
             fontsize=13.4, color=COLOR_TEXT, va="center")
    handles = [mpatches.Patch(facecolor=COLOR_BAR, edgecolor="none", label="Gasto mensual promedio"),
               plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=COLOR_POINT,
                          markeredgewidth=0, label="% Gasto respecto al ingreso")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.105), ncol=2,
               fontsize=8.8, frameon=False, labelcolor=COLOR_TEXT, columnspacing=4)
    fig.text(0.055, 0.057, "Fuente:", fontsize=8, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(0.096, 0.057,
             f"IFT con datos de la ENIGH {SOURCE_YEAR}, del INEGI. Datos disponibles en: {SOURCE_URL}",
             fontsize=8, color=COLOR_TEXT, va="top")
    fig.text(0.055, 0.033, "Notas:", fontsize=8, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(0.093, 0.033,
             "El gasto e ingreso utilizados son promedios de los hogares de cada decil que disponen del servicio y gastan en él. Las cifras corresponden a 2024 y no se ajustan por inflación.",
             fontsize=7.7, color=COLOR_TEXT, va="top")
    fig.subplots_adjust(left=0.08, right=0.92, top=0.84, bottom=0.22)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  A.8 | Adquisición o reutilización del ZIP ENIGH 2024")
    raw_path = context.acquire_source(SOURCE_ID)
    print("  A.8 | Cálculo de gasto fijo e ingreso por decil")
    data = build_metrics(*load_enigh_tables(raw_path))
    context.record_source_period(SOURCE_ID, str(SOURCE_YEAR), "AL_DIA")
    context.write_data_used(data)
    for row in data.itertuples(index=False):
        context.record_calculation(
            f"gasto_fijas_decil_{row.decil}",
            "promedio ponderado trimestral / 3; porcentaje = gasto mensual / ingreso mensual * 100",
            {"anio": SOURCE_YEAR, "decil": row.decil, "hogares_expandidos": row.hogares_expandidos},
            {"gasto_mensual": row.gasto_promedio_mensual_pesos, "gasto_pct_ingreso": row.gasto_pct_ingreso},
            "pesos mensuales y porcentaje", 1,
        )
    first, last = data.iloc[0], data.iloc[-1]
    text_path = context.render_text("a_8.md.j2", {
        "anio": SOURCE_YEAR, "gasto_decil_1": first["gasto_promedio_mensual_pesos"],
        "pct_decil_1": first["gasto_pct_ingreso"],
        "gasto_decil_10": last["gasto_promedio_mensual_pesos"],
        "pct_decil_10": last["gasto_pct_ingreso"],
    })
    output_path = context.expected_figure_path
    print("  A.8 | Generación de gráfica PNG")
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
