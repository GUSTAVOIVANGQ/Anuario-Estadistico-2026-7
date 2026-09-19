"""Figura F.10: percepción del riesgo de violencia en Internet."""
from __future__ import annotations

import re
import sys
import textwrap
import unicodedata
import zipfile
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd

FIGURE_ID = "F.10"
SOURCE_ID = "ift_tercera_encuesta_usuarios_2023_base"
PERIOD = "2023"
TEXT = "#3c3c3b"
BLUE = "#335a5c"
SALMON = "#4a7d75"
BACKGROUND = "#F8F8FA"

OPTIONS = [
    ("Menores de edad", "Niños, niñas y adolescentes"),
    ("Mujeres", "Mujeres"),
    ("Todas las personas son vulnerables", "Todas las personas son vulnerables"),
    ("Adultos mayores / Personas de la tercera edad", "Personas adultas mayores"),
    ("Personas con discapacidad", "Personas con discapacidad"),
    ("Integrantes de la comunidad LGBTIQ+", "Personas de la comunidad LGBTIQ+"),
    ("Personas indígenas", "Personas indígenas"),
    ("Hombres", "Hombres"),
    ("Personas negras o afrodescendientes", "Personas afrodescendientes"),
]
REFERENCE = [56.3, 43.3, 29.1, 10.8, 9.9, 9.0, 5.3, 5.0, 3.7]


def _norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value).replace("\xa0", " ").strip().lower())
    return re.sub(r"\s+", " ", "".join(c for c in text if not unicodedata.combining(c)))


def _find_col(frame: pd.DataFrame, *tokens: str) -> str:
    wanted = [_norm(token) for token in tokens]
    for column in frame.columns:
        if all(token in _norm(column) for token in wanted):
            return str(column)
    raise KeyError(f"No se encontró columna con {tokens}")


def _find_option(frame: pd.DataFrame, question: str, option: str) -> str:
    q, target = _norm(question), _norm(option)
    for column in frame.columns:
        normalized = _norm(column)
        if q in normalized and target in normalized:
            return str(column)
    raise KeyError(f"No se encontró la opción {option!r}")


def _yes(series: pd.Series) -> pd.Series:
    return series.astype("string").map(_norm).str.startswith("si", na=False)


def load_raw(source: Path) -> tuple[pd.DataFrame, str]:
    with zipfile.ZipFile(source) as archive:
        member = next(
            (name for name in archive.namelist() if "int&tv" in _norm(Path(name).name) and name.lower().endswith(".xlsx")),
            None,
        )
        if not member:
            raise ValueError("La descarga no contiene la base de Internet y TV")
        frame = pd.read_excel(BytesIO(archive.read(member)))
    return frame, member


def build_metrics(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float | int | str]]:
    weight = _find_col(raw, "factor de expansion final normalizado")
    internet = _find_col(raw, "internet fijo en su hogar")
    data = raw.copy()
    data[weight] = pd.to_numeric(data[weight], errors="coerce")
    eligible = data.loc[_yes(data[internet]) & data[weight].notna()].copy()
    denominator = float(eligible[weight].sum())
    rows = []
    for option, label in OPTIONS:
        column = _find_option(raw, "mayor riesgo", option)
        selected = _yes(eligible[column])
        numerator = float(eligible.loc[selected, weight].sum())
        rows.append({"categoria": label, "porcentaje": numerator / denominator * 100, "numerador_ponderado": numerator})
    result = pd.DataFrame(rows).sort_values("porcentaje", ascending=False).reset_index(drop=True)
    return result, {"columna_factor": weight, "denominador_ponderado": denominator, "casos_elegibles": len(eligible)}


def validate_reference(data: pd.DataFrame) -> float:
    actual = dict(zip(data["categoria"], data["porcentaje"]))
    expected = dict(zip([label for _, label in OPTIONS], REFERENCE))
    maximum = max(abs(round(actual[label], 1) - value) for label, value in expected.items())
    if maximum > 0.11:
        raise ValueError(f"F.10 no reproduce la referencia 2023: desviación {maximum:.1f} pp")
    return maximum


def _font(project_root: Path) -> str:
    directory = project_root / "assets" / "fonts" / "Noto_Sans"
    for name in ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"):
        path = directory / name
        if path.is_file():
            fm.fontManager.addfont(path)
    return "Noto Sans" if any(item.name == "Noto Sans" for item in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data: pd.DataFrame, output: Path, project_root: Path) -> None:
    family = _font(project_root)
    plt.rcParams.update({"font.family": family})
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.025, .055), .95, .87, boxstyle="round,pad=.012,rounding_size=.02", fc=BACKGROUND, ec="none", transform=fig.transFigure, zorder=-2))
    fig.text(.047,.887,"   ",fontsize=2,va="center",bbox=dict(boxstyle="round,pad=1.6,rounding_size=.2",fc="#4a7d75",ec="none"))
    fig.text(.064, .887, "Figura F.10.", color=TEXT, fontsize=16, fontweight="bold", va="center")
    fig.text(.171, .887, "Personas con mayor riesgo de ser víctimas de violencia en Internet (2023)", color=TEXT, fontsize=16, va="center")
    top = data.iloc[0]
    narrative = (f"La percepción de mayor riesgo se concentra en {top.categoria.lower()} "
                 f"({top.porcentaje:.1f}%). Los porcentajes se calcularon con el factor de expansión "
                 "normalizado entre personas usuarias de Internet fijo.")
    fig.add_artist(patches.FancyBboxPatch((.045, .245), .19, .46, boxstyle="round,pad=.012,rounding_size=.02", fc="white", ec="none", transform=fig.transFigure, zorder=-1))
    fig.text(.063, .64, "VIOLENCIA DIGITAL", color=TEXT, fontsize=16, fontweight="bold")
    fig.text(.063, .59, textwrap.fill(narrative, width=31), color="#222222", fontsize=11.5, va="top", linespacing=1.4)
    ax = fig.add_axes([.44, .17, .49, .63])
    ordered = data.sort_values("porcentaje", ascending=True)
    colors = ["#335a5c" if index >= len(ordered) - 2 else "#86adae" for index in range(len(ordered))]
    bars = ax.barh(ordered["categoria"], ordered["porcentaje"], color=colors, height=.62)
    ax.set_xlim(0, max(60, ordered["porcentaje"].max() * 1.16)); ax.set_xticks([])
    ax.tick_params(axis="y", length=0, labelsize=11, colors=TEXT, pad=10)
    ax.spines[:].set_visible(False); ax.set_facecolor(BACKGROUND)
    for bar, value in zip(bars, ordered["porcentaje"]):
        ax.text(value + .8, bar.get_y() + bar.get_height()/2, f"{value:.1f}%", va="center", color=TEXT, fontsize=12, fontweight="bold", bbox=dict(boxstyle="round,pad=.25,rounding_size=.8", fc="white", ec=bar.get_facecolor(), lw=.8))
    fig.text(.047, .09, "Fuente:", color=TEXT, fontsize=9, fontweight="bold")
    fig.text(.094, .09, "IFT con información de la Tercera Encuesta 2023, Personas Usuarias de Servicios de Telecomunicaciones.", color=TEXT, fontsize=9)
    fig.text(.047, .067, "Nota:", color=TEXT, fontsize=9, fontweight="bold")
    fig.text(.081, .067, "Porcentajes ponderados; las respuestas son de selección múltiple y no suman 100%.", color=TEXT, fontsize=9)
    output.parent.mkdir(parents=True, exist_ok=True); fig.savefig(output, dpi=200); plt.close(fig)


def generate(context):
    print("  F.10 | Reutilización o descarga de la base oficial IFT")
    source = context.acquire_source(SOURCE_ID)
    raw, member = load_raw(source)
    data, meta = build_metrics(raw)
    deviation = validate_reference(data)
    context.record_source_period(SOURCE_ID, PERIOD, "ULTIMO_COMPATIBLE")
    context.write_data_used(data.drop(columns="numerador_ponderado"))
    for row in data.itertuples(index=False):
        context.record_calculation(f"riesgo_{_norm(row.categoria).replace(' ', '_')}", "sum(factor de casos Sí) / sum(factor de población elegible) * 100", {"archivo": member, "numerador_ponderado": row.numerador_ponderado, "denominador_ponderado": meta["denominador_ponderado"]}, row.porcentaje, "porcentaje", 1)
    summary = f"La categoría con mayor porcentaje fue {data.iloc[0].categoria} ({data.iloc[0].porcentaje:.1f}%)."
    text_path = context.render_text("f_digital.md.j2", {"resumen": summary})
    print(data.drop(columns="numerador_ponderado").to_string(index=False, formatters={"porcentaje": lambda x: f"{x:.1f}%"}))
    print(f"Validación contra la referencia publicada: desviación máxima {deviation:.1f} puntos porcentuales.")
    _plot(data, context.expected_figure_path, context.project_root)
    return {"figure_path": str(context.expected_figure_path), "text_path": str(text_path), "source_latest_period": PERIOD, "rows_used": len(data)}


def main() -> int:
    root = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(root / "src"))
    from anuario2026.pipeline import run_pipeline
    run_pipeline(root, only=FIGURE_ID); return 0


if __name__ == "__main__":
    raise SystemExit(main())
