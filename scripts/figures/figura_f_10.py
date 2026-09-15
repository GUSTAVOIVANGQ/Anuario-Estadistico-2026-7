"""Figura F.10: percepción del riesgo de violencia en Internet."""
from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui

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
import numpy as np
import pandas as pd

FIGURE_ID = "F.10"
SOURCE_ID = "ift_tercera_encuesta_usuarios_2023_base"
PERIOD = "2023"
TEXT = "#4B4B83"
BLUE = "#317DA3"
SALMON = "#F58F82"
BACKGROUND = "#FBFBF7"

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
    family=_font(project_root); plt.rcParams.update({"font.family":family})
    fig,ax=plt.subplots(figsize=(16,8.5)); fig.patch.set_facecolor("white"); ax.set_facecolor("#F8F8FA")
    text="#3c3c3b"; dark="#335a5c"; light="#86adae"
    x=np.arange(len(data)); values=data["porcentaje"].to_numpy(float); colors=[dark if i<2 else light for i in range(len(data))]
    bars=ax.bar(x,values,color=colors,width=.60,edgecolor="none",zorder=2)
    ax.set_ylim(0,max(values)*1.15); ticks=np.arange(0, int(max(values)*1.15//10+1)*10+1,10); ax.set_yticks(ticks,[f"{int(v)}%" for v in ticks])
    ax.set_xticks(x,data["categoria"].astype(str),fontsize=8.3,color=text); ax.tick_params(axis="y",labelsize=9,colors=text,length=0); ax.tick_params(axis="x",length=0)
    ax.grid(axis="y",color="#d1d1d1",linewidth=1,zorder=0); ax.set_axisbelow(True); ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False); ax.spines["left"].set_color("#7c7c7c"); ax.spines["bottom"].set_color("#7c7c7c")
    for bar,value,color in zip(bars,values,colors,strict=True):
        ax.annotate(f"{value:.1f}%",(bar.get_x()+bar.get_width()/2,value),xytext=(0,6),textcoords="offset points",ha="center",va="bottom",fontsize=8.2,color=text,bbox=dict(boxstyle="round,pad=.3,rounding_size=.8",facecolor="white",edgecolor=color,linewidth=.8))
    fig.add_artist(patches.Rectangle((.060,.916),.009,.020,transform=fig.transFigure,facecolor="#4a7d75",edgecolor="none")); fig.text(.075,.926,"Figura F.10.",fontsize=14,fontweight="bold",color=text,va="center"); fig.text(.168,.926,"Personas con mayor riesgo de ser víctimas de violencia en Internet (2023)",fontsize=14,color=text,va="center")
    fig.text(.06,.065,"Fuente:",fontsize=8,fontweight="bold",color=text,va="top"); fig.text(.098,.065,"IFT con información de la Tercera Encuesta 2023, Personas Usuarias de Servicios de Telecomunicaciones.",fontsize=8,color=text,va="top"); fig.text(.06,.043,"Nota:",fontsize=8,fontweight="bold",color=text,va="top"); fig.text(.091,.043,"Porcentajes ponderados; las respuestas son de selección múltiple y no suman 100%.",fontsize=8,color=text,va="top")
    fig.subplots_adjust(left=.075,right=.94,top=.81,bottom=.24); output.parent.mkdir(parents=True,exist_ok=True); apply_reference_ui(fig, FIGURE_ID); fig.savefig(output,dpi=200,facecolor="white"); plt.close(fig)

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
