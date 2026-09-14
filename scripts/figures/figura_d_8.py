"""Figura D.8: influencia de la confianza en el uso de Internet (ECSI 2024)."""
from __future__ import annotations

import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd

FIGURE_ID, SOURCE_ID, PERIOD = "D.8", "ift_ecsi_2024_base", "2024"
TEXT, BG = "#4B4B7D", "#FBFBF7"
COLORS = ["#327BA0", "#A9DADF", "#4F5082", "#F48D7E", "#F0535A", "#65B9D8"]
CODES = [(1, "Nada"), (2, "Poco"), (3, "Le es indiferente"), (4, "Algo"), (5, "Mucho"), (9, "NS/NR")]
REFERENCE = [13.6, 38.5, 8.5, 29.6, 6.6, 3.2]


def load_and_calculate(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path, usecols=["conf_int", "fac_per"], low_memory=False)
    data["fac_per"] = pd.to_numeric(data["fac_per"], errors="coerce").fillna(0)
    denominator = float(data["fac_per"].sum())
    return pd.DataFrame([{"codigo": code, "percepcion": label,
                          "porcentaje": float(data.loc[data.conf_int.eq(code), "fac_per"].sum()) / denominator * 100,
                          "denominador_ponderado": denominator} for code, label in CODES])


def _font(root: Path) -> str:
    directory = root / "assets" / "fonts" / "Noto_Sans"
    for name in ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"):
        path = directory / name
        if path.is_file(): fm.fontManager.addfont(path)
    return "Noto Sans" if any(item.name == "Noto Sans" for item in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data: pd.DataFrame, output: Path, root: Path) -> None:
    plt.rcParams.update({"font.family": _font(root)})
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.035, .06), .93, .86, boxstyle="round,pad=.012,rounding_size=.02", fc=BG, ec="none", transform=fig.transFigure, zorder=-2))
    fig.text(.055, .88, "•", color="#F58F82", fontsize=20, va="center")
    fig.text(.073, .88, "Figura D.8.", color=TEXT, fontsize=16, fontweight="bold", va="center")
    fig.text(.18, .88, "¿Qué tanto influye la confianza en Internet para decidir usarlo? (2024)", color=TEXT, fontsize=16, va="center")
    ax = fig.add_axes([.10, .20, .80, .58]); ax.set_facecolor(BG)
    bars = ax.bar(range(len(data)), data.porcentaje, color=COLORS, width=.6, zorder=2)
    ax.set_ylim(0, 45); ax.set_yticks(range(0, 46, 5), [f"{x}%" for x in range(0, 46, 5)])
    ax.set_xticks(range(len(data)), data.percepcion, fontsize=11, color=TEXT)
    ax.tick_params(axis="x", length=0, pad=10); ax.tick_params(axis="y", length=0, colors=TEXT)
    ax.grid(axis="y", color="#DADAE3", linewidth=.7, zorder=0); ax.spines[:].set_visible(False)
    for bar, value in zip(bars, data.porcentaje):
        ax.text(bar.get_x()+bar.get_width()/2, value+1, f"{value:.1f}%", ha="center", color=TEXT, fontsize=12,
                fontweight="bold", bbox=dict(boxstyle="round,pad=.28", fc="white", ec="none"))
    fig.text(.055, .09, "Fuente:", color=TEXT, fontsize=9, fontweight="bold")
    fig.text(.101, .09, "IFT, Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.", color=TEXT, fontsize=9)
    output.parent.mkdir(parents=True, exist_ok=True); fig.savefig(output, dpi=200); plt.close(fig)


def generate(context):
    print("  D.8 | Descarga o reutilización de la base oficial ECSI 2024")
    raw = context.acquire_source(SOURCE_ID); data = load_and_calculate(raw)
    deviation = max(abs(round(value, 1)-expected) for value, expected in zip(data.porcentaje, REFERENCE))
    if deviation > .11: raise ValueError(f"D.8 no reproduce la referencia: desviación {deviation:.1f} pp")
    context.record_source_period(SOURCE_ID, PERIOD, "ULTIMO_PUBLICADO")
    context.write_data_used(data.drop(columns="denominador_ponderado"))
    for row in data.itertuples(index=False):
        context.record_calculation(f"conf_int_{row.codigo}", "sum(fac_per por respuesta) / sum(fac_per total) * 100",
                                   {"codigo": row.codigo, "denominador": row.denominador_ponderado}, row.porcentaje, "porcentaje", 1)
    top = data.loc[data.porcentaje.idxmax()]
    text_path = context.render_text("f_digital.md.j2", {"resumen": f"La respuesta más frecuente fue {top.percepcion.lower()} ({top.porcentaje:.1f}%)."})
    print(f"Validación contra el anuario: desviación máxima {deviation:.1f} pp")
    _plot(data, context.expected_figure_path, context.project_root)
    return {"figure_path": str(context.expected_figure_path), "text_path": str(text_path), "source_latest_period": PERIOD, "rows_used": len(data)}


def main() -> int:
    root = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(root / "src"))
    from anuario2026.pipeline import run_pipeline
    run_pipeline(root, only=FIGURE_ID); return 0


if __name__ == "__main__": raise SystemExit(main())
