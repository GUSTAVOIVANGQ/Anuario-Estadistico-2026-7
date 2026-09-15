"""Figura D.5: forma de aprendizaje del uso de Internet (ECSI 2024)."""
from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui

import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd

FIGURE_ID = "D.5"
SOURCE_ID = "ift_ecsi_2024_base"
PERIOD = "2024"
TEXT, CORAL, BG = "#4B4B7D", "#F2535A", "#FBFBF7"
VARIABLES = [
    ("apren_uso_int_1", "Por su cuenta"),
    ("apren_uso_int_2", "Capacitación en el trabajo"),
    ("apren_uso_int_3", "Curso en la escuela"),
    ("apren_uso_int_4", "Curso en centro comunitario"),
    ("apren_uso_int_5", "Curso particular"),
    ("apren_uso_int_6", "Amigos o familiares"),
    ("apren_uso_int_8", "Otros"),
    ("apren_uso_int_9", "NS/NR"),
]
REFERENCE = [50.7, 4.1, 14.9, 0.3, 2.0, 26.2, 1.0, 0.9]


def load_raw(path: Path) -> pd.DataFrame:
    columns = [name for name, _ in VARIABLES] + ["rescate_internet", "fac_per"]
    data = pd.read_csv(path, usecols=columns, low_memory=False)
    data["fac_per"] = pd.to_numeric(data["fac_per"], errors="coerce").fillna(0)
    return data.loc[data["rescate_internet"].eq(1)].copy()


def build_metrics(data: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    denominator = float(data["fac_per"].sum())
    if denominator <= 0:
        raise ValueError("ECSI no contiene población usuaria de Internet ponderable")
    rows = []
    for variable, label in VARIABLES:
        numerator = float(data.loc[data[variable].eq(1), "fac_per"].sum())
        rows.append({"variable": variable, "categoria": label, "porcentaje": numerator / denominator * 100,
                     "numerador_ponderado": numerator, "denominador_ponderado": denominator})
    return pd.DataFrame(rows), denominator


def validate_reference(data: pd.DataFrame) -> float:
    deviation = max(abs(round(value, 1) - expected) for value, expected in zip(data["porcentaje"], REFERENCE))
    if deviation > 0.11:
        raise ValueError(f"D.5 no reproduce la referencia: desviación {deviation:.1f} pp")
    return deviation


def _font(root: Path) -> str:
    directory = root / "assets" / "fonts" / "Noto_Sans"
    for name in ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"):
        path = directory / name
        if path.is_file(): fm.fontManager.addfont(path)
    return "Noto Sans" if any(item.name == "Noto Sans" for item in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data: pd.DataFrame, output: Path, root: Path) -> None:
    plt.rcParams.update({"font.family": _font(root)})
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.035, .06), .93, .86, boxstyle="round,pad=.012,rounding_size=.02",
                                          fc=BG, ec="none", transform=fig.transFigure, zorder=-2))
    fig.text(.055, .88, "•", color="#F58F82", fontsize=20, va="center")
    fig.text(.073, .88, "Figura D.5.", color=TEXT, fontsize=16, fontweight="bold", va="center")
    fig.text(.18, .88, "¿Cómo aprendió a buscar información o usar Internet? (2024)", color=TEXT, fontsize=16, va="center")
    ax = fig.add_axes([.075, .21, .86, .57]); ax.set_facecolor(BG)
    bars = ax.bar(range(len(data)), data["porcentaje"], color=CORAL, width=.58, zorder=2)
    ax.set_ylim(0, 60); ax.set_yticks(range(0, 61, 10), [f"{n}%" for n in range(0, 61, 10)])
    ax.set_xticks(range(len(data)), [textwrap.fill(x, 16) for x in data["categoria"]], fontsize=10, color=TEXT)
    ax.tick_params(axis="x", length=0, pad=10); ax.tick_params(axis="y", length=0, colors=TEXT)
    ax.grid(axis="y", color="#DADAE3", linewidth=.7, zorder=0); ax.spines[:].set_visible(False)
    for bar, value in zip(bars, data["porcentaje"]):
        ax.text(bar.get_x()+bar.get_width()/2, value+1, f"{value:.1f}%", ha="center", color=TEXT,
                fontsize=11, fontweight="bold", bbox=dict(boxstyle="round,pad=.28", fc="white", ec="none"))
    fig.text(.055, .112, "Fuente:", color=TEXT, fontsize=9, fontweight="bold")
    fig.text(.101, .112, "IFT, Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.", color=TEXT, fontsize=9)
    fig.text(.055, .086, "Nota:", color=TEXT, fontsize=9, fontweight="bold")
    fig.text(.09, .086, "Porcentajes ponderados entre personas usuarias de Internet; la respuesta admite más de una opción.", color=TEXT, fontsize=9)
    output.parent.mkdir(parents=True, exist_ok=True); apply_reference_ui(fig, FIGURE_ID); fig.savefig(output, dpi=200); plt.close(fig)


def generate(context):
    print("  D.5 | Descarga o reutilización de la base oficial ECSI 2024")
    raw = context.acquire_source(SOURCE_ID); data, denominator = build_metrics(load_raw(raw)); deviation = validate_reference(data)
    context.record_source_period(SOURCE_ID, PERIOD, "ULTIMO_PUBLICADO")
    context.write_data_used(data.drop(columns=["numerador_ponderado", "denominador_ponderado"]))
    for row in data.itertuples(index=False):
        context.record_calculation(row.variable, "sum(fac_per donde opción=1) / sum(fac_per de usuarios de Internet) * 100",
                                   {"numerador": row.numerador_ponderado, "denominador": denominator}, row.porcentaje, "porcentaje", 1)
    summary = f"La forma principal de aprendizaje fue {data.loc[data.porcentaje.idxmax(), 'categoria'].lower()} ({data.porcentaje.max():.1f}%)."
    text_path = context.render_text("f_digital.md.j2", {"resumen": summary})
    print(f"Validación contra el anuario: desviación máxima {deviation:.1f} pp")
    _plot(data, context.expected_figure_path, context.project_root)
    return {"figure_path": str(context.expected_figure_path), "text_path": str(text_path), "source_latest_period": PERIOD, "rows_used": len(data)}


def main() -> int:
    root = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(root / "src"))
    from anuario2026.pipeline import run_pipeline
    run_pipeline(root, only=FIGURE_ID); return 0


if __name__ == "__main__": raise SystemExit(main())
