"""Figura E.9: servicios más importantes para MiPymes importadoras/exportadoras."""
from __future__ import annotations

import re
import sys
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

FIGURE_ID = "E.9"
SOURCE_ID = "ift_mipymes_impexp_2022_base"
PERIOD = "2022"
SERVICES = [
    "Conexión a Internet fijo",
    "Telefonía fija",
    "Telefonía móvil",
    "Conexión a Internet por datos móviles",
    "Televisión de paga",
]
REFERENCE = {
    "Conexión a Internet fijo": 63.4,
    "Telefonía fija": 20.8,
    "Telefonía móvil": 6.6,
    "Conexión a Internet por datos móviles": 6.3,
    "Televisión de paga": 0.7,
}
TEXT, BG, CORAL = "#4B4B7D", "#FBFBF7", "#F48D7E"
COLORS = ["#A9DADF", "#327BA0", "#4F5082", "#F48D7E", "#F0535A"]


def _norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value).replace("\xa0", " ").lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def _find(columns, *tokens: str) -> str:
    found = [str(column) for column in columns if all(_norm(token) in _norm(column) for token in tokens)]
    if not found:
        raise KeyError(f"No se encontró una columna con {tokens}")
    return min(found, key=lambda column: len(_norm(column)))


def load_raw(path: Path) -> tuple[pd.DataFrame, str, str, str]:
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith((".xlsx", ".xls", ".csv"))]
        diagnostics = []
        for member in members:
            payload = archive.read(member)
            try:
                if member.lower().endswith(".csv"):
                    header = pd.read_csv(BytesIO(payload), nrows=0, encoding="utf-8-sig")
                else:
                    header = pd.read_excel(BytesIO(payload), nrows=0)
                question = _find(header.columns, "servicios", "mas importante", "actividades")
                factor = _find(header.columns, "factor", "expansion", "final")
                if member.lower().endswith(".csv"):
                    frame = pd.read_csv(BytesIO(payload), usecols=[question, factor], encoding="utf-8-sig")
                else:
                    frame = pd.read_excel(BytesIO(payload), usecols=[question, factor])
                return frame, member, question, factor
            except Exception as exc:
                diagnostics.append(f"{member}: {exc}")
    raise ValueError("No se localizó la tabla de E.9 dentro del ZIP: " + "; ".join(diagnostics))


def _classify(value: object) -> str | None:
    text = _norm(value)
    if "datos moviles" in text or "internet por datos" in text:
        return "Conexión a Internet por datos móviles"
    if "internet fijo" in text or ("conexion a internet" in text and "wifi" in text):
        return "Conexión a Internet fijo"
    if "telefonia fija" in text:
        return "Telefonía fija"
    if "telefonia movil" in text:
        return "Telefonía móvil"
    if "television de paga" in text or "tv de paga" in text:
        return "Televisión de paga"
    return None


def build_metrics(frame: pd.DataFrame, question: str, factor: str) -> pd.DataFrame:
    work = frame[[question, factor]].copy()
    work[factor] = pd.to_numeric(work[factor], errors="coerce")
    work = work.dropna(subset=[question, factor])
    work = work.loc[work[factor].gt(0)].copy()
    if work.empty:
        raise ValueError("La pregunta de E.9 no contiene respuestas válidas")
    work["servicio"] = work[question].map(_classify)
    denominator = float(work[factor].sum())
    rows = []
    for service in SERVICES:
        numerator = float(work.loc[work.servicio.eq(service), factor].sum())
        rows.append({"periodo": PERIOD, "servicio": service, "porcentaje": numerator / denominator * 100, "numerador_ponderado": numerator, "denominador_ponderado": denominator})
    return pd.DataFrame(rows)


def validate(data: pd.DataFrame) -> float:
    maximum = max(abs(round(float(data.loc[data.servicio.eq(service), "porcentaje"].iloc[0]), 1) - expected) for service, expected in REFERENCE.items())
    if maximum > 0.11:
        raise ValueError(f"E.9 no reproduce el anuario: desviación {maximum:.1f} pp")
    return maximum


def _font(root: Path) -> str:
    for name in ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"):
        path = root / "assets" / "fonts" / "Noto_Sans" / name
        if path.is_file():
            fm.fontManager.addfont(path)
    return "Noto Sans" if any(item.name == "Noto Sans" for item in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data: pd.DataFrame, output: Path, root: Path) -> None:
    plt.rcParams.update({"font.family": _font(root)})
    current = data.set_index("servicio").loc[SERVICES].reset_index()
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.035, .06), .93, .86, boxstyle="round,pad=.012,rounding_size=.02", fc=BG, ec="none", transform=fig.transFigure, zorder=-2))
    fig.text(.055, .88, "•", color=CORAL, fontsize=20, va="center")
    fig.text(.073, .88, "Figura E.9.", color=TEXT, fontsize=16, fontweight="bold", va="center")
    fig.text(.18, .88, "Servicios de telecomunicaciones que consideran más importantes las MiPymes para realizar actividades de importación y/o exportación", color=TEXT, fontsize=14.5, va="center")
    ax = fig.add_axes([.31, .20, .60, .58])
    ax.set_facecolor(BG)
    y = np.arange(len(current))
    for yy, row, color in zip(y, current.itertuples(index=False), COLORS):
        bar = patches.FancyBboxPatch((0, yy - .30), row.porcentaje, .60, boxstyle="round,pad=0,rounding_size=.17", fc=color, ec="none")
        ax.add_patch(bar)
        ax.text(row.porcentaje + 2.3, yy, f"{row.porcentaje:.1f}%", va="center", ha="center", color=TEXT, fontsize=12, fontweight="bold", bbox=dict(boxstyle="round,pad=.35", fc="white", ec="none"))
    ax.set_xlim(0, 72)
    ax.set_ylim(-.65, len(current) - .35)
    ax.invert_yaxis()
    ax.set_yticks(y, [re.sub(r" por ", "\npor ", service, count=1) if len(service) > 30 else service for service in current.servicio], fontsize=11, color=TEXT)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0, pad=20)
    ax.spines[:].set_visible(False)
    fig.text(.055, .122, "Fuente:", color=TEXT, fontsize=9, fontweight="bold")
    fig.text(.101, .122, "IFT, Contratación, percepción y uso de telecomunicaciones por MiPymes importadoras y/o exportadoras.", color=TEXT, fontsize=9)
    fig.text(.055, .094, "Nota:", color=TEXT, fontsize=9, fontweight="bold")
    fig.text(.09, .094, 'Debido a que se excluyen las menciones "No sabe/No contestó", la suma no da 100%.', color=TEXT, fontsize=9)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200)
    plt.close(fig)


def generate(context):
    print("  E.9 | Descarga o reutilización del estudio MiPymes importadoras/exportadoras")
    raw = context.acquire_source(SOURCE_ID)
    frame, member, question, factor = load_raw(raw)
    data = build_metrics(frame, question, factor)
    deviation = validate(data)
    context.record_source_period(SOURCE_ID, PERIOD, "ULTIMO_PUBLICADO_COMPATIBLE")
    context.write_data_used(data[["periodo", "servicio", "porcentaje"]])
    for row in data.itertuples(index=False):
        context.record_calculation(
            f"servicio_importancia_{_norm(row.servicio)}",
            "sum(factor final de la categoría) / sum(factor final de respuestas válidas, incluido NS/NC) * 100",
            {"periodo": PERIOD, "servicio": row.servicio, "numerador": row.numerador_ponderado, "denominador": row.denominador_ponderado, "archivo": member, "pregunta": question, "factor": factor},
            row.porcentaje,
            "porcentaje",
            1,
        )
    ordered = data.sort_values("porcentaje", ascending=False)
    top, bottom = ordered.iloc[0], ordered.iloc[-1]
    text_path = context.render_text("f_digital.md.j2", {"resumen": f"El servicio considerado más importante fue {top.servicio.lower()} ({top.porcentaje:.1f}%) y el de menor importancia fue {bottom.servicio.lower()} ({bottom.porcentaje:.1f}%)."})
    print(f"Validación contra el anuario: desviación máxima {deviation:.1f} pp")
    _plot(data, context.expected_figure_path, context.project_root)
    return {"figure_path": str(context.expected_figure_path), "text_path": str(text_path), "source_latest_period": PERIOD, "rows_used": len(data)}


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "src"))
    from anuario2026.pipeline import run_pipeline

    run_pipeline(root, only=FIGURE_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
