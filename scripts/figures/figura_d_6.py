"""Figura D.6: experiencias negativas en Internet por sexo (ECSI 2024)."""
from __future__ import annotations

import sys, textwrap
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIGURE_ID, SOURCE_ID, PERIOD = "D.6", "ift_ecsi_2024_base", "2024"
TEXT, BG = "#4B4B7D", "#FBFBF7"
COLORS = {"Hombres": "#327BA0", "Mujeres": "#F48D7E", "Total": "#4F5082"}
VARIABLES = [
    ("expp_mensnd", "Recibir mensajes no deseados"),
    ("expp_pubipi", "Publicación de información personal sin permiso"),
    ("expp_datpre", "Uso de datos para préstamos o créditos sin permiso"),
    ("expp_robcon", "Robo de contraseñas"),
]
REFERENCE = {"Hombres": [61.7, 14.4, 11.6, 16.4], "Mujeres": [58.3, 12.7, 10.5, 16.5], "Total": [59.8, 13.5, 11.0, 16.4]}


def load_and_calculate(path: Path) -> pd.DataFrame:
    cols = [x for x, _ in VARIABLES] + ["rescate_internet", "sexo", "fac_per"]
    data = pd.read_csv(path, usecols=cols, low_memory=False)
    data["fac_per"] = pd.to_numeric(data.fac_per, errors="coerce").fillna(0)
    data = data.loc[data.rescate_internet.eq(1)].copy()
    groups = [("Hombres", data.sexo.eq(2)), ("Mujeres", data.sexo.eq(1)), ("Total", pd.Series(True, index=data.index))]
    rows = []
    for group, mask in groups:
        sub = data.loc[mask]; denominator = float(sub.fac_per.sum())
        for variable, label in VARIABLES:
            numerator = float(sub.loc[sub[variable].eq(1), "fac_per"].sum())
            rows.append({"grupo": group, "variable": variable, "experiencia": label,
                         "porcentaje": numerator / denominator * 100, "numerador_ponderado": numerator,
                         "denominador_ponderado": denominator})
    return pd.DataFrame(rows)


def _font(root: Path) -> str:
    for name in ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"):
        path = root / "assets" / "fonts" / "Noto_Sans" / name
        if path.is_file(): fm.fontManager.addfont(path)
    return "Noto Sans" if any(x.name == "Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data: pd.DataFrame, output: Path, root: Path) -> None:
    plt.rcParams.update({"font.family": _font(root)})
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.035, .06), .93, .86, boxstyle="round,pad=.012,rounding_size=.02", fc=BG, ec="none", transform=fig.transFigure, zorder=-2))
    fig.text(.055, .88, "•", color="#F58F82", fontsize=20, va="center")
    fig.text(.073, .88, "Figura D.6.", color=TEXT, fontsize=16, fontweight="bold", va="center")
    fig.text(.18, .88, "Experiencias negativas en Internet por sexo (2024)", color=TEXT, fontsize=16, va="center")
    ax = fig.add_axes([.075, .24, .86, .53]); ax.set_facecolor(BG)
    x = np.arange(len(VARIABLES)); width = .22
    for offset, group in enumerate(("Hombres", "Mujeres", "Total")):
        values = data.loc[data.grupo.eq(group), "porcentaje"].to_numpy()
        bars = ax.bar(x + (offset-1)*width, values, width, color=COLORS[group], label=group, zorder=2)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x()+bar.get_width()/2, value+1.1, f"{value:.1f}%", ha="center", color=TEXT,
                    fontsize=9, fontweight="bold", bbox=dict(boxstyle="round,pad=.22", fc="white", ec="none"))
    ax.set_ylim(0, 72); ax.set_yticks(range(0, 71, 10), [f"{x}%" for x in range(0, 71, 10)])
    ax.set_xticks(x, [textwrap.fill(label, 24) for _, label in VARIABLES], fontsize=9.5, color=TEXT)
    ax.tick_params(axis="x", length=0, pad=10); ax.tick_params(axis="y", length=0, colors=TEXT)
    ax.grid(axis="y", color="#DADAE3", linewidth=.7, zorder=0); ax.spines[:].set_visible(False)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(.5, 1.09), frameon=False, labelcolor=TEXT)
    fig.text(.055, .122, "Fuente:", color=TEXT, fontsize=9, fontweight="bold")
    fig.text(.101, .122, "IFT, Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.", color=TEXT, fontsize=9)
    fig.text(.055, .094, "Nota:", color=TEXT, fontsize=9, fontweight="bold")
    fig.text(.09, .094, "Porcentajes ponderados entre personas usuarias de Internet; las respuestas no son excluyentes.", color=TEXT, fontsize=9)
    output.parent.mkdir(parents=True, exist_ok=True); fig.savefig(output, dpi=200); plt.close(fig)


def generate(context):
    print("  D.6 | Descarga o reutilización de la base oficial ECSI 2024")
    raw = context.acquire_source(SOURCE_ID); data = load_and_calculate(raw)
    deviation = max(abs(round(float(data.loc[(data.grupo.eq(g)) & (data.variable.eq(v)), "porcentaje"].iloc[0]), 1)-REFERENCE[g][i]) for g in REFERENCE for i, (v, _) in enumerate(VARIABLES))
    if deviation > .11: raise ValueError(f"D.6 no reproduce la referencia: desviación {deviation:.1f} pp")
    context.record_source_period(SOURCE_ID, PERIOD, "ULTIMO_PUBLICADO")
    context.write_data_used(data[["grupo", "experiencia", "porcentaje"]])
    for row in data.itertuples(index=False):
        context.record_calculation(f"{row.variable}_{row.grupo.lower()}", "sum(fac_per donde respuesta=1) / sum(fac_per del grupo) * 100",
                                   {"grupo": row.grupo, "numerador": row.numerador_ponderado, "denominador": row.denominador_ponderado}, row.porcentaje, "porcentaje", 1)
    top = data.loc[data.porcentaje.idxmax()]
    text_path = context.render_text("f_digital.md.j2", {"resumen": f"La cifra mayor fue {top.experiencia.lower()} entre {top.grupo.lower()} ({top.porcentaje:.1f}%)."})
    print(f"Validación contra el anuario: desviación máxima {deviation:.1f} pp"); _plot(data, context.expected_figure_path, context.project_root)
    return {"figure_path": str(context.expected_figure_path), "text_path": str(text_path), "source_latest_period": PERIOD, "rows_used": len(data)}


def main() -> int:
    root = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(root / "src"))
    from anuario2026.pipeline import run_pipeline
    run_pipeline(root, only=FIGURE_ID); return 0


if __name__ == "__main__": raise SystemExit(main())
