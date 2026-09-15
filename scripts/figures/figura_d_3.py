"""Figura D.3: horas promedio diarias de uso de Internet por edad."""

from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui

import sys
import zipfile
from pathlib import Path, PurePosixPath

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


FIGURE_ID = "D.3"
SOURCE_ID = "inegi_endutih_2025"
SOURCE_YEAR = 2025
SOURCE_URL = "https://www.inegi.org.mx/programas/endutih/2025/"
GROUPS = ["6 a 11", "12 a 17", "18 a 24", "25 a 34", "35 a 44", "45 a 54", "55 a 64", "65 o más"]
BINS = [5, 11, 17, 24, 34, 44, 54, 64, 999]
DISPLAY_ORDER = ["18 a 24", "25 a 34", "12 a 17", "35 a 44", "45 a 54", "55 a 64", "65 o más", "6 a 11"]
COLORS = ["#F2535A", "#F28D7D", "#4B4B83", "#317DA1", "#A8DCE0", "#646CB0", "#8490C7", "#4CA8CF"]
COLOR_TEXT = "#4B4B7D"
COLOR_BACKGROUND = "#FBFBF7"


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


def load_users(raw_path: Path) -> pd.DataFrame:
    expected = f"tr_endutih_usuarios_anual_{SOURCE_YEAR}.csv"
    with zipfile.ZipFile(raw_path) as archive:
        member = next((name for name in archive.namelist()
                       if PurePosixPath(name.replace("\\", "/")).name.casefold() == expected.casefold()), None)
        if member is None:
            raise ValueError(f"El ZIP ENDUTIH no contiene {expected}")
        with archive.open(member) as stream:
            frame = pd.read_csv(stream, usecols=["EDAD", "P7_4", "FAC_PER"], dtype=str, low_memory=False)
    frame.columns = [str(column).strip().upper() for column in frame.columns]
    return frame


def build_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    """Promedio ponderado de P7_4 con FAC_PER, estimador que reproduce 2023."""
    data = frame.copy()
    data["EDAD"] = pd.to_numeric(data["EDAD"], errors="coerce")
    data["P7_4"] = pd.to_numeric(data["P7_4"], errors="coerce")
    data["FAC_PER"] = pd.to_numeric(data["FAC_PER"], errors="coerce")
    data = data.dropna(subset=["EDAD", "P7_4", "FAC_PER"])
    data = data.loc[data["EDAD"].ge(6) & data["FAC_PER"].gt(0)].copy()
    data["grupo_edad"] = pd.cut(data["EDAD"], BINS, labels=GROUPS)
    rows = []
    for group in GROUPS:
        subset = data.loc[data["grupo_edad"].eq(group)]
        population = float(subset["FAC_PER"].sum())
        if population <= 0:
            raise ValueError(f"El grupo {group} no tiene personas con horas válidas")
        rows.append({
            "anio": SOURCE_YEAR,
            "grupo_edad": group,
            "poblacion_expandida_con_respuesta": round(population),
            "horas_promedio": float(np.average(subset["P7_4"], weights=subset["FAC_PER"])),
        })
    return pd.DataFrame(rows)


def _plot(data: pd.DataFrame, output_path: Path, project_root: Path) -> None:
    _configure_fonts(project_root)
    ordered = data.set_index("grupo_edad").reindex(DISPLAY_ORDER).reset_index()
    fig, ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(COLOR_BACKGROUND)
    x = np.arange(len(ordered))
    bars = ax.bar(x, ordered["horas_promedio"], 0.56, color=COLORS, edgecolor="none", zorder=2)
    for bar, color in zip(bars, COLORS):
        value = bar.get_height()
        ax.annotate(f"{value:.1f}", (bar.get_x() + bar.get_width() / 2, value),
                    xytext=(0, 7), textcoords="offset points", ha="center", va="bottom",
                    fontsize=8.5, color=COLOR_TEXT, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.28,rounding_size=0.7",
                              facecolor="white", edgecolor=color, linewidth=0.8))
    ax.set_xticks(x, [])
    ax.set_ylabel("Horas promedio", fontsize=10, color=COLOR_TEXT)
    ax.set_ylim(0, max(7.1, float(ordered["horas_promedio"].max()) * 1.25))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
    ax.tick_params(axis="y", labelsize=9, colors=COLOR_TEXT, length=0)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="y", color="#DADAE3", linewidth=0.7, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    handles = [mpatches.Patch(facecolor=color, edgecolor="none", label=group)
               for group, color in zip(DISPLAY_ORDER, COLORS)]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.105),
               ncol=8, fontsize=8.5, frameon=False, labelcolor=COLOR_TEXT,
               handlelength=1.5, columnspacing=1.8)
    fig.text(0.055, 0.93, "   ", fontsize=2, va="center",
             bbox=dict(boxstyle="round,pad=1.6,rounding_size=0.2",
                       facecolor="#F58F82", edgecolor="none"))
    fig.text(0.073, 0.93, "Figura D.3.", fontsize=14, fontweight="bold", color=COLOR_TEXT, va="center")
    fig.text(0.151, 0.93, "Horas promedio de uso de internet por grupos de edad",
             fontsize=14, color=COLOR_TEXT, va="center")
    fig.text(0.055, 0.058, "Fuente:", fontsize=8, fontweight="bold", color=COLOR_TEXT)
    fig.text(0.096, 0.058,
             f"IFT con datos de la ENDUTIH {SOURCE_YEAR}, del INEGI. Datos disponibles en {SOURCE_URL}",
             fontsize=8, color=COLOR_TEXT)
    fig.subplots_adjust(left=0.07, right=0.96, top=0.83, bottom=0.22)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output_path, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  D.3 | Adquisición o reutilización del ZIP ENDUTIH 2025")
    raw_path = context.acquire_source(SOURCE_ID)
    print("  D.3 | Lectura de usuarios y promedio ponderado de horas")
    data = build_metrics(load_users(raw_path))
    context.record_source_period(SOURCE_ID, str(SOURCE_YEAR), "AL_DIA")
    context.write_data_used(data)
    for row in data.itertuples(index=False):
        context.record_calculation(
            f"horas_internet_{row.grupo_edad}",
            "suma(P7_4 * FAC_PER) / suma(FAC_PER), sólo P7_4 válido",
            {"anio": SOURCE_YEAR, "grupo_edad": row.grupo_edad,
             "poblacion_expandida_con_respuesta": row.poblacion_expandida_con_respuesta},
            row.horas_promedio, "horas diarias", 1,
        )
    maximum = data.loc[data["horas_promedio"].idxmax()]
    minimum = data.loc[data["horas_promedio"].idxmin()]
    text_path = context.render_text("d_3.md.j2", {
        "anio": SOURCE_YEAR,
        "grupo_max": maximum["grupo_edad"], "horas_max": maximum["horas_promedio"],
        "grupo_min": minimum["grupo_edad"], "horas_min": minimum["horas_promedio"],
    })
    print("  D.3 | Generación de gráfica PNG")
    _plot(data, context.expected_figure_path, context.project_root)
    return {"figure_path": str(context.expected_figure_path), "text_path": str(text_path),
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
