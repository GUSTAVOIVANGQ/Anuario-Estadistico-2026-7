"""Figura E.1: Índice General de Satisfacción por servicio."""
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

FIGURE_ID = "E.1"
SOURCES = {
    2023: "ift_tercera_encuesta_usuarios_2023_base",
    2024: "ift_segunda_encuesta_usuarios_2025",
}
SERVICES = ["Telefonía fija", "Telefonía móvil", "Televisión de paga", "Internet fijo"]
REFERENCE = {
    2023: {"Telefonía fija": 76.7, "Telefonía móvil": 75.7, "Televisión de paga": 74.9, "Internet fijo": 74.0},
    2024: {"Telefonía fija": 76.2, "Telefonía móvil": 76.0, "Televisión de paga": 75.7, "Internet fijo": 75.2},
}
TOKENS = {
    "Telefonía fija": ("telefonia", "fija"),
    "Telefonía móvil": ("telefonia", "movil"),
    "Televisión de paga": ("television", "paga"),
    "Internet fijo": ("internet",),
}
TEXT, BG, CORAL = "#4B4B7D", "#FBFBF7", "#F48D7E"
COLORS = ["#A9DADF", "#327BA0", "#4F5082", "#F48D7E"]


def _norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value).replace("\xa0", " ").lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def _find(columns, *tokens: str, reject: tuple[str, ...] = ()) -> str:
    found = [
        str(column)
        for column in columns
        if all(_norm(token) in _norm(column) for token in tokens)
        and not any(_norm(token) in _norm(column) for token in reject)
    ]
    if not found:
        raise KeyError(f"No se encontró una columna con {tokens}")
    return min(found, key=lambda column: len(_norm(column)))


def _member_services(name: str) -> list[str]:
    normalized = _norm(name)
    if "int tv" in normalized or "internet" in normalized:
        return ["Internet fijo", "Televisión de paga"]
    if "fija" in normalized:
        return ["Telefonía fija"]
    if "movil" in normalized:
        return ["Telefonía móvil"]
    return []


def _weight_column(columns, year: int, combined: bool) -> str:
    if combined:
        tokens = ("factor", "expansion", "final", "anual") if year == 2024 else ("factor", "expansion", "final")
    else:
        tokens = ("calibrador", "final", "anual") if year == 2024 else ("calibrador", "final")
    return _find(columns, *tokens, reject=("normalizado", "trimestral"))


def load_metrics(path: Path, year: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith((".xlsx", ".xls"))]
        for member in members:
            services = _member_services(member)
            if not services:
                continue
            payload = archive.read(member)
            header = pd.read_excel(BytesIO(payload), nrows=0)
            weight_column = _weight_column(header.columns, year, len(services) == 2)
            question_columns = {
                service: _find(
                    header.columns,
                    "terminos generales",
                    "satisfech",
                    "ultimos 12 meses",
                    "recodificada",
                    *TOKENS[service],
                )
                for service in services
            }
            wanted = [weight_column, *question_columns.values()]
            frame = pd.read_excel(BytesIO(payload), usecols=wanted)
            weight = pd.to_numeric(frame[weight_column], errors="coerce")
            for service, question_column in question_columns.items():
                value = pd.to_numeric(frame[question_column], errors="coerce")
                valid = value.notna() & value.between(0, 100) & weight.notna() & weight.gt(0)
                denominator = float(weight.loc[valid].sum())
                numerator = float((value.loc[valid] * weight.loc[valid]).sum())
                rows.append(
                    {
                        "anio_dato": year,
                        "servicio": service,
                        "igs": numerator / denominator,
                        "numerador_ponderado": numerator,
                        "denominador_ponderado": denominator,
                        "observaciones": int(valid.sum()),
                        "archivo_interno": member,
                        "columna_igs": question_column,
                        "columna_factor": weight_column,
                    }
                )
    data = pd.DataFrame(rows)
    if set(data["servicio"]) != set(SERVICES):
        raise ValueError(f"Servicios incompletos en {path.name}: {sorted(data['servicio'].tolist())}")
    return data


def validate(data: pd.DataFrame) -> float:
    deviations = []
    for year, expected in REFERENCE.items():
        for service, reference in expected.items():
            actual = float(data.loc[data.anio_dato.eq(year) & data.servicio.eq(service), "igs"].iloc[0])
            deviations.append(abs(round(actual, 1) - reference))
    maximum = max(deviations)
    if maximum > 0.11:
        raise ValueError(f"E.1 no reproduce los resultados oficiales: {maximum:.1f} puntos")
    return maximum


def _font(root: Path) -> str:
    for name in ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"):
        path = root / "assets" / "fonts" / "Noto_Sans" / name
        if path.is_file():
            fm.fontManager.addfont(path)
    return "Noto Sans" if any(item.name == "Noto Sans" for item in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data: pd.DataFrame, output: Path, root: Path) -> None:
    plt.rcParams.update({"font.family": _font(root)})
    current = data.loc[data.anio_dato.eq(2024)].set_index("servicio").loc[SERVICES].reset_index()
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.035, .06), .93, .86, boxstyle="round,pad=.012,rounding_size=.02", fc=BG, ec="none", transform=fig.transFigure, zorder=-2))
    fig.text(.055, .88, "•", color=CORAL, fontsize=20, va="center")
    fig.text(.073, .88, "Figura E.1.", color=TEXT, fontsize=16, fontweight="bold", va="center")
    fig.text(.18, .88, "Índice General de Satisfacción (IGS) por servicio de telecomunicaciones", color=TEXT, fontsize=16, va="center")
    ax = fig.add_axes([.30, .20, .62, .58])
    ax.set_facecolor(BG)
    y = np.arange(len(current))
    for yy, row, color in zip(y, current.itertuples(index=False), COLORS):
        bar = patches.FancyBboxPatch((0, yy - .31), row.igs, .62, boxstyle="round,pad=0,rounding_size=.17", fc=color, ec="none")
        ax.add_patch(bar)
        ax.text(row.igs + 1.5, yy, f"{row.igs:.1f}", va="center", ha="center", color=TEXT, fontsize=13, fontweight="bold", bbox=dict(boxstyle="round,pad=.35", fc="white", ec="none"))
    ax.set_xlim(0, 85)
    ax.set_ylim(-.65, len(current) - .35)
    ax.invert_yaxis()
    ax.set_yticks(y, current.servicio, fontsize=12, color=TEXT)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0, pad=22)
    ax.spines[:].set_visible(False)
    fig.text(.055, .122, "Fuente:", color=TEXT, fontsize=9, fontweight="bold")
    fig.text(.101, .122, "IFT, Segunda Encuesta 2025, Personas Usuarias de Servicios de Telecomunicaciones.", color=TEXT, fontsize=9)
    fig.text(.055, .094, "Nota:", color=TEXT, fontsize=9, fontweight="bold")
    fig.text(.09, .094, "Resultados de entrevistas aplicadas durante 2024. Indicadores medidos en una escala de 0 a 100 puntos.", color=TEXT, fontsize=9)
    output.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output, dpi=200)
    plt.close(fig)


def generate(context):
    frames = []
    for year, source_id in SOURCES.items():
        print(f"  E.1 | Descarga o reutilización de encuesta {year}")
        raw = context.acquire_source(source_id)
        frames.append(load_metrics(raw, year))
        context.record_source_period(source_id, str(year), "ULTIMO_PUBLICADO_COMPATIBLE" if year == 2024 else "HISTORICO")
    data = pd.concat(frames, ignore_index=True)
    deviation = validate(data)
    current = data.loc[data.anio_dato.eq(2024)].copy()
    context.write_data_used(current[["anio_dato", "servicio", "igs"]])
    context.write_data_used(data.loc[data.anio_dato.eq(2023), ["anio_dato", "servicio", "igs"]], "validacion_historica")
    for row in data.itertuples(index=False):
        context.record_calculation(
            f"igs_{row.anio_dato}_{_norm(row.servicio)}",
            "sum(IGS recodificado * factor final) / sum(factor final con IGS válido)",
            {"anio_dato": row.anio_dato, "servicio": row.servicio, "numerador": row.numerador_ponderado, "denominador": row.denominador_ponderado, "observaciones": row.observaciones, "archivo": row.archivo_interno, "columna_igs": row.columna_igs, "columna_factor": row.columna_factor},
            row.igs,
            "puntos",
            1,
        )
    ordered = current.sort_values("igs", ascending=False)
    top, bottom = ordered.iloc[0], ordered.iloc[-1]
    text_path = context.render_text("f_digital.md.j2", {"resumen": f"En 2024, el IGS más alto correspondió a {top.servicio.lower()} ({top.igs:.1f} puntos) y el menor a {bottom.servicio.lower()} ({bottom.igs:.1f} puntos)."})
    print(f"Validación 2023 y 2024: desviación máxima {deviation:.1f} puntos")
    _plot(data, context.expected_figure_path, context.project_root)
    return {"figure_path": str(context.expected_figure_path), "text_path": str(text_path), "source_latest_period": "2024", "rows_used": len(current)}


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "src"))
    from anuario2026.pipeline import run_pipeline

    run_pipeline(root, only=FIGURE_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
