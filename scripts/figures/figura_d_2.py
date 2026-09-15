"""Figura D.2: uso de smartphone e Internet por grupos de edad."""

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
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


FIGURE_ID = "D.2"
SOURCE_ID = "inegi_endutih_2025"
SOURCE_YEAR = 2025
SOURCE_URL = "https://www.inegi.org.mx/programas/endutih/2025/"
GROUPS = ["6 a 11", "12 a 17", "18 a 24", "25 a 34", "35 a 44", "45 a 54", "55 o más"]
BINS = [5, 11, 17, 24, 34, 44, 54, 999]
KEYS = ["UPM", "VIV_SEL", "HOGAR", "NUM_REN"]

COLOR_SMARTPHONE = "#4B4B83"
COLOR_INTERNET = "#F2535A"
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


def _member(archive: zipfile.ZipFile, table: str) -> str:
    expected = f"tr_endutih_{table}_anual_{SOURCE_YEAR}.csv"
    for name in archive.namelist():
        if PurePosixPath(name.replace("\\", "/")).name.casefold() == expected.casefold():
            return name
    raise ValueError(f"El ZIP ENDUTIH no contiene {expected}")


def _read(archive: zipfile.ZipFile, table: str, columns: list[str]) -> pd.DataFrame:
    with archive.open(_member(archive, table)) as stream:
        frame = pd.read_csv(stream, usecols=columns, dtype=str, low_memory=False)
    frame.columns = [str(column).strip().upper() for column in frame.columns]
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"La tabla {table} no contiene {missing}")
    return frame


def load_microdata(raw_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    with zipfile.ZipFile(raw_path) as archive:
        users = _read(archive, "usuarios", KEYS + ["EDAD", "P7_1", "FAC_PER"])
        users2 = _read(archive, "usuarios2", KEYS + ["P8_1", "P8_4_2"])
    return users, users2


def build_metrics(users: pd.DataFrame, users2: pd.DataFrame) -> pd.DataFrame:
    """Reproduce 2023 exactamente y aplica el mismo estimador a 2025."""
    merged = users.merge(users2, on=KEYS, how="inner", validate="one_to_one")
    if len(merged) != len(users) or len(merged) != len(users2):
        raise ValueError("Las tablas usuarios y usuarios2 no tienen correspondencia uno a uno")
    for column in ("P7_1", "P8_1", "P8_4_2"):
        merged[column] = (
            merged[column].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        )
    merged["EDAD"] = pd.to_numeric(merged["EDAD"], errors="coerce")
    merged["FAC_PER"] = pd.to_numeric(merged["FAC_PER"], errors="coerce").fillna(0)
    merged = merged.loc[merged["EDAD"].ge(6) & merged["FAC_PER"].gt(0)].copy()
    merged["grupo_edad"] = pd.cut(merged["EDAD"], BINS, labels=GROUPS)
    merged["usa_internet"] = merged["P7_1"].eq("1")
    # ENDUTIH: dispone de celular (P8_1) y el celular usado es inteligente (P8_4_2).
    # Esta conjunción reproduce a una decimal todos los valores de la Figura D.2 de 2024.
    merged["usa_smartphone"] = merged["P8_1"].eq("1") & merged["P8_4_2"].eq("1")

    rows = []
    for group in GROUPS:
        subset = merged.loc[merged["grupo_edad"].eq(group)]
        population = float(subset["FAC_PER"].sum())
        if population <= 0:
            raise ValueError(f"El grupo {group} no tiene población ponderada")
        rows.append({
            "anio": SOURCE_YEAR,
            "grupo_edad": group,
            "poblacion_expandida": round(population),
            "smartphone_pct": float((subset["usa_smartphone"] * subset["FAC_PER"]).sum() / population * 100),
            "internet_pct": float((subset["usa_internet"] * subset["FAC_PER"]).sum() / population * 100),
        })
    return pd.DataFrame(rows)


def _plot(data: pd.DataFrame, output_path: Path, project_root: Path) -> None:
    _configure_fonts(project_root)
    fig, ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(COLOR_BACKGROUND)
    x = np.arange(len(data))
    width = 0.28
    first = ax.bar(x - width / 2, data["smartphone_pct"], width,
                   label="% de usuarios de Smartphone", color=COLOR_SMARTPHONE,
                   edgecolor="none", zorder=2)
    second = ax.bar(x + width / 2, data["internet_pct"], width,
                    label="% de usuarios de Internet", color=COLOR_INTERNET,
                    edgecolor="none", zorder=2)
    for bars, color in ((first, COLOR_SMARTPHONE), (second, COLOR_INTERNET)):
        for bar in bars:
            value = bar.get_height()
            ax.annotate(f"{value:.1f}%", (bar.get_x() + bar.get_width() / 2, value),
                        xytext=(0, 7), textcoords="offset points", ha="center", va="bottom",
                        fontsize=8.5, color=COLOR_TEXT, fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.28,rounding_size=0.7",
                                  facecolor="white", edgecolor=color, linewidth=0.8))
    ax.set_xticks(x, [f"{group}\naños" if group != "55 o más" else "55 o\nmás"
                      for group in data["grupo_edad"]], fontsize=9, color=COLOR_TEXT)
    ax.set_ylim(0, 112)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(100, decimals=0))
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", labelsize=8.5, colors=COLOR_TEXT, length=0)
    ax.grid(axis="y", color="#DADAE3", linewidth=0.7, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.text(0.055, 0.93, "   ", fontsize=2, va="center",
             bbox=dict(boxstyle="round,pad=1.6,rounding_size=0.2",
                       facecolor="#F58F82", edgecolor="none"))
    fig.text(0.073, 0.93, "Figura D.2.", fontsize=14, fontweight="bold", color=COLOR_TEXT, va="center")
    fig.text(0.151, 0.93, "Uso de Smartphone e Internet por grupos de edad",
             fontsize=14, color=COLOR_TEXT, va="center")
    fig.legend(loc="lower center", bbox_to_anchor=(0.5, 0.105), ncol=2,
               fontsize=9.5, frameon=False, labelcolor=COLOR_TEXT, handlelength=2.5)
    fig.text(0.055, 0.058, "Fuente:", fontsize=8, fontweight="bold", color=COLOR_TEXT)
    fig.text(0.096, 0.058,
             f"IFT con datos de la ENDUTIH {SOURCE_YEAR}, del INEGI. Datos disponibles en {SOURCE_URL}",
             fontsize=8, color=COLOR_TEXT)
    fig.subplots_adjust(left=0.07, right=0.96, top=0.83, bottom=0.22)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output_path, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  D.2 | Adquisición o reutilización del ZIP ENDUTIH 2025")
    raw_path = context.acquire_source(SOURCE_ID)
    print("  D.2 | Lectura de usuarios y cálculo ponderado por grupo de edad")
    data = build_metrics(*load_microdata(raw_path))
    context.record_source_period(SOURCE_ID, str(SOURCE_YEAR), "AL_DIA")
    context.write_data_used(data)
    for row in data.itertuples(index=False):
        context.record_calculation(
            f"uso_tic_{row.grupo_edad}",
            "suma(indicador * FAC_PER) / suma(FAC_PER) * 100",
            {"anio": SOURCE_YEAR, "grupo_edad": row.grupo_edad,
             "poblacion_expandida": row.poblacion_expandida,
             "smartphone": "P8_1=1 y P8_4_2=1", "internet": "P7_1=1"},
            {"smartphone_pct": row.smartphone_pct, "internet_pct": row.internet_pct},
            "porcentaje", 1,
        )
    smart_max = data.loc[data["smartphone_pct"].idxmax()]
    internet_min = data.loc[data["internet_pct"].idxmin()]
    text_path = context.render_text("d_2.md.j2", {
        "anio": SOURCE_YEAR,
        "grupo_smartphone_max": smart_max["grupo_edad"],
        "smartphone_max": smart_max["smartphone_pct"],
        "grupo_internet_min": internet_min["grupo_edad"],
        "internet_min": internet_min["internet_pct"],
    })
    print("  D.2 | Generación de gráfica PNG")
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
