"""Figura D.4: uso de dispositivos inteligentes conectados a Internet."""

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


FIGURE_ID = "D.4"
SOURCE_ID = "inegi_endutih_2025"
SOURCE_YEAR = 2025
SOURCE_URL = "https://www.inegi.org.mx/programas/endutih/2025/"
VARIABLES = [f"P9_1_{number}" for number in range(1, 11)]
ORDER = [
    ("P9_1_8", "Dispositivos de\nentretenimiento"),
    ("P9_1_1", "Bocina o\nasistente del\nhogar"),
    ("P9_1_2", "Sistemas de\nvideovigilancia"),
    ("P9_1_5", "Luces o\ninterruptores"),
    ("P9_1_7", "Electro-\ndomésticos"),
    ("P9_1_6", "Conexión\neléctrica"),
    ("P9_1_3", "Puertas o\nventanas con\ncerrado digital"),
    ("P9_1_9", "Automóvil\no camioneta"),
    ("P9_1_4", "Dispositivos\nde ahorro de\nenergía eléctrica"),
    ("P9_1_10", "Otros\ndispositivos"),
]
COLOR_BAR = "#F2535A"
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


def load_users2(raw_path: Path) -> pd.DataFrame:
    expected = f"tr_endutih_usuarios2_anual_{SOURCE_YEAR}.csv"
    with zipfile.ZipFile(raw_path) as archive:
        member = next((name for name in archive.namelist()
                       if PurePosixPath(name.replace("\\", "/")).name.casefold() == expected.casefold()), None)
        if member is None:
            raise ValueError(f"El ZIP ENDUTIH no contiene {expected}")
        with archive.open(member) as stream:
            frame = pd.read_csv(stream, usecols=VARIABLES + ["FAC_PER"], dtype=str, low_memory=False)
    frame.columns = [str(column).strip().upper() for column in frame.columns]
    missing = sorted(set(VARIABLES + ["FAC_PER"]) - set(frame.columns))
    if missing:
        raise ValueError(f"La tabla usuarios2 no contiene {missing}")
    return frame


def build_metrics(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Porcentaje entre quienes usan al menos un dispositivo P9_1_1..P9_1_10."""
    data = frame.copy()
    for column in VARIABLES:
        data[column] = (
            data[column].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        )
    data["FAC_PER"] = pd.to_numeric(data["FAC_PER"], errors="coerce").fillna(0)
    uses_any = data[VARIABLES].eq("1").any(axis=1)
    denominator = float(data.loc[uses_any, "FAC_PER"].sum())
    if denominator <= 0:
        raise ValueError("No hay personas usuarias de dispositivos inteligentes")
    rows = []
    for variable, label in ORDER:
        expanded = float(data.loc[data[variable].eq("1"), "FAC_PER"].sum())
        rows.append({
            "anio": SOURCE_YEAR,
            "variable": variable,
            "dispositivo": label.replace("\n", " "),
            "usuarios_expandidos": round(expanded),
            "universo_usuarios_iot": round(denominator),
            "porcentaje": expanded / denominator * 100,
        })
    return pd.DataFrame(rows), round(denominator)


def _plot(data: pd.DataFrame, output_path: Path, project_root: Path) -> None:
    _configure_fonts(project_root)
    labels = [label for _, label in ORDER]
    fig, ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(COLOR_BACKGROUND)
    x = np.arange(len(data))
    bars = ax.bar(x, data["porcentaje"], 0.56, color=COLOR_BAR, edgecolor="none", zorder=2)
    ymax = max(70, float(data["porcentaje"].max()) * 1.23)
    ax.set_ylim(0, ymax)
    for bar in bars:
        value = bar.get_height()
        ax.annotate(f"{value:.1f}%", (bar.get_x() + bar.get_width() / 2, value),
                    xytext=(0, 7), textcoords="offset points", ha="center", va="bottom",
                    fontsize=8.5, color=COLOR_TEXT, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.28,rounding_size=0.7",
                              facecolor="white", edgecolor=COLOR_BAR, linewidth=0.8))
    ax.set_xticks(x, labels, fontsize=8.2, color=COLOR_TEXT, linespacing=1.15)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", labelsize=9, colors=COLOR_TEXT, length=0)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(100, decimals=1))
    ax.grid(axis="y", color="#DADAE3", linewidth=0.7, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.text(0.055, 0.93, "   ", fontsize=2, va="center",
             bbox=dict(boxstyle="round,pad=1.6,rounding_size=0.2",
                       facecolor="#F58F82", edgecolor="none"))
    fig.text(0.073, 0.93, "Figura D.4.", fontsize=14, fontweight="bold", color=COLOR_TEXT, va="center")
    fig.text(0.151, 0.93, "Uso de dispositivos inteligentes conectados a Internet",
             fontsize=14, color=COLOR_TEXT, va="center")
    fig.text(0.055, 0.058, "Fuente:", fontsize=8, fontweight="bold", color=COLOR_TEXT)
    fig.text(0.096, 0.058,
             f"IFT con datos de la ENDUTIH {SOURCE_YEAR}, del INEGI. Datos disponibles en {SOURCE_URL}",
             fontsize=8, color=COLOR_TEXT)
    fig.subplots_adjust(left=0.07, right=0.965, top=0.83, bottom=0.25)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output_path, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  D.4 | Adquisición o reutilización del ZIP ENDUTIH 2025")
    raw_path = context.acquire_source(SOURCE_ID)
    print("  D.4 | Lectura de usuarios2 y cálculo ponderado de dispositivos")
    data, denominator = build_metrics(load_users2(raw_path))
    context.record_source_period(SOURCE_ID, str(SOURCE_YEAR), "AL_DIA")
    context.write_data_used(data)
    context.record_calculation(
        "universo_usuarios_iot", "suma(FAC_PER donde cualquier P9_1_1..P9_1_10=1)",
        {"anio": SOURCE_YEAR}, denominator, "personas", 0,
    )
    for row in data.itertuples(index=False):
        context.record_calculation(
            f"uso_{row.variable}",
            "suma(FAC_PER donde variable=1) / suma(FAC_PER donde cualquier dispositivo=1) * 100",
            {"anio": SOURCE_YEAR, "variable": row.variable,
             "usuarios_expandidos": row.usuarios_expandidos, "universo_iot": denominator},
            row.porcentaje, "porcentaje", 1,
        )
    maximum = data.loc[data["porcentaje"].idxmax()]
    minimum = data.loc[data["porcentaje"].idxmin()]
    text_path = context.render_text("d_4.md.j2", {
        "anio": SOURCE_YEAR,
        "dispositivo_max": maximum["dispositivo"], "porcentaje_max": maximum["porcentaje"],
        "dispositivo_min": minimum["dispositivo"], "porcentaje_min": minimum["porcentaje"],
    })
    print("  D.4 | Generación de gráfica PNG")
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
