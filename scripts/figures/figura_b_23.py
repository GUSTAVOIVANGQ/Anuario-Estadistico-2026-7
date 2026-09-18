"""Figura B.23: tecnologías de TV restringida por segmento.

El archivo contiene adquisición, lectura del crudo BIT, cálculo, auditoría,
texto y generación del PNG sin depender de código de otras figuras.
"""

from __future__ import annotations

import math
import sys
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FIGURE_ID = "B.23"
SOURCE_ID = "crt_bit_todo_2025_q2"
TABLE = "TD_ACC_TVRES_ITE_VA.csv"
TEXT = "#3c3c3b"
CREAM = "#F8F8FA"
TECHNOLOGIES = [
    "Cable", "Direct-to-home (DTH)", "IPTV Terrestre",
    "Sin información de tecnología",
]
COLORS = {
    "Cable": "#132b2d",
    "Direct-to-home (DTH)": "#3b6667",
    "IPTV Terrestre": "#64a0a1",
    "Sin información de tecnología": "#86adae",
}


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


def _member(archive: zipfile.ZipFile) -> str:
    for name in archive.namelist():
        if PurePosixPath(name.replace("\\", "/")).name.casefold() == TABLE.casefold():
            return name
    raise ValueError(f"TODO.zip no contiene {TABLE}")


def load_raw(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        with archive.open(_member(archive)) as stream:
            return pd.read_csv(
                stream,
                usecols=[
                    "ANIO", "MES", "TECNO_ACCESO_TV",
                    "A_RESIDENCIAL_E", "A_NO_RESIDENCIAL_E",
                ],
                encoding="latin-1",
                low_memory=False,
            )


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype("string").str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )


def _key(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(c for c in text if not unicodedata.combining(c)).upper().strip()


def _technology(value: object) -> str:
    key = _key(value)
    if "CABLE" in key or "HFC" in key:
        return "Cable"
    if "DIRECT-TO-HOME" in key or "DIRECT TO HOME" in key or "DTH" in key:
        return "Direct-to-home (DTH)"
    if "IPTV" in key:
        return "IPTV Terrestre"
    if "SIN INFORMACION" in key:
        return "Sin información de tecnología"
    return str(value).strip()


def build_metrics(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float | int]]:
    data = raw.copy()
    for column in ("ANIO", "MES", "A_RESIDENCIAL_E", "A_NO_RESIDENCIAL_E"):
        data[column] = _numeric(data[column])
    data["tecnologia"] = data["TECNO_ACCESO_TV"].map(_technology)
    years = data.loc[data["MES"].eq(12), "ANIO"].dropna().astype(int)
    if years.empty:
        raise ValueError("BIT no contiene cortes de diciembre para B.23")
    latest = int(years.max())
    previous = latest - 1
    if previous not in set(years):
        raise ValueError(f"BIT no contiene diciembre de {previous}")

    unknown = sorted(set(data["tecnologia"].dropna()) - set(TECHNOLOGIES))
    current_all = data.loc[data["ANIO"].eq(latest) & data["MES"].eq(12)]
    if unknown:
        unknown_total = float(
            current_all.loc[current_all["tecnologia"].isin(unknown),
                            ["A_RESIDENCIAL_E", "A_NO_RESIDENCIAL_E"]].sum().sum()
        )
        overall = max(float(current_all[["A_RESIDENCIAL_E", "A_NO_RESIDENCIAL_E"]].sum().sum()), 1)
        if unknown_total / overall > 0.005:
            raise ValueError("Tecnologías BIT no contempladas: " + ", ".join(unknown))

    rows: list[dict[str, float | int | str]] = []
    metadata: dict[str, float | int] = {"anio": latest, "anio_previo": previous}
    for segment, column in (
        ("Residencial", "A_RESIDENCIAL_E"),
        ("No Residencial", "A_NO_RESIDENCIAL_E"),
    ):
        totals: dict[int, pd.Series] = {}
        for year in (previous, latest):
            grouped = (
                data.loc[data["ANIO"].eq(year) & data["MES"].eq(12)]
                .groupby("tecnologia")[column].sum(min_count=1)
                .reindex(TECHNOLOGIES, fill_value=0).fillna(0)
            )
            totals[year] = grouped
        current_total = float(totals[latest].sum())
        previous_total = float(totals[previous].sum())
        slug = "residencial" if segment == "Residencial" else "no_residencial"
        metadata[f"total_{slug}"] = current_total
        metadata[f"crecimiento_{slug}"] = (
            (current_total / previous_total - 1) * 100 if previous_total else math.nan
        )
        for technology in TECHNOLOGIES:
            current = float(totals[latest][technology])
            prior = float(totals[previous][technology])
            rows.append({
                "segmento": segment,
                "tecnologia": technology,
                "anio": latest,
                "accesos": current,
                "participacion": current / current_total * 100 if current_total else math.nan,
                "anio_previo": previous,
                "accesos_previos": prior,
                "crecimiento_anual": (current / prior - 1) * 100 if prior else math.nan,
            })
    return pd.DataFrame(rows), metadata


def _draw_panel(
    fig: plt.Figure,
    data: pd.DataFrame,
    segment: str,
    total: float,
    x: float,
) -> None:
    fig.add_artist(patches.FancyBboxPatch(
        (x, 0.13), 0.44, 0.70, boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.0, edgecolor="#8D8DB2", facecolor="white",
        transform=fig.transFigure, zorder=0,
    ))
    heading_width = 0.17 if segment == "Residencial" else 0.21
    fig.add_artist(patches.FancyBboxPatch(
        (x + (0.44 - heading_width) / 2, 0.80), heading_width, 0.07,
        boxstyle="round,pad=0.012,rounding_size=0.02", linewidth=0,
        facecolor="white", transform=fig.transFigure, zorder=5,
    ))
    fig.text(x + 0.22, 0.833, segment, ha="center", va="center",
             fontsize=18, fontweight="bold", color=TEXT, zorder=6)

    panel = data.loc[data["segmento"].eq(segment)]
    positive = panel.loc[panel["accesos"].gt(0)].copy()
    ax = fig.add_axes([x + 0.025, 0.19, 0.29, 0.56], zorder=2)
    wedges, _ = ax.pie(
        positive["accesos"], colors=[COLORS[t] for t in positive["tecnologia"]],
        startangle=90, counterclock=False,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    ax.set_aspect("equal")
    ax.axis("off")
    for wedge, row in zip(wedges, positive.itertuples(index=False)):
        angle = math.radians((wedge.theta1 + wedge.theta2) / 2)
        ex, ey = math.cos(angle), math.sin(angle)
        tx = 0.98 * (1 if ex >= 0 else -1)
        ty = float(np.clip(1.02 * ey, -0.92, 0.92))
        if segment == "No Residencial":
            if row.tecnologia == "Cable":
                tx, ty = 0.98, -0.88
            elif row.tecnologia == "IPTV Terrestre":
                tx, ty = -0.98, 0.88
            else:
                tx, ty = -0.98, 0.52
        inward_alignment = "right" if tx > 0 else "left"
        ax.annotate(
            f"{row.participacion:.1f}%", xy=(0.82 * ex, 0.82 * ey), xytext=(tx, ty),
            ha=inward_alignment, va="center", fontsize=12,
            fontweight="bold", color=TEXT,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="none"),
            arrowprops=dict(arrowstyle="-", color="#A0A0B0", linewidth=1.0),
            annotation_clip=True,
        )
        label = row.tecnologia.replace("Direct-to-home (DTH)", "Direct-to-home\n(DTH)")
        ax.text(tx, ty + (-0.18 if ty < 0 else 0.18), label,
                ha=inward_alignment, va="center",
                fontsize=8.5, fontweight="bold", color=TEXT, clip_on=True)

    bx, by, bw, bh = x + 0.285, 0.57, 0.135, 0.135
    fig.add_artist(patches.FancyBboxPatch(
        (bx, by), bw, bh, boxstyle="round,pad=0.012,rounding_size=0.025",
        linewidth=0, facecolor=CREAM, transform=fig.transFigure, zorder=4,
    ))
    fig.text(bx + bw / 2, by + bh * 0.66,
             f"Accesos {segment.lower()}es\na nivel nacional:",
             ha="center", va="center", fontsize=8, color=TEXT, zorder=5)
    fig.text(bx + bw / 2, by + bh * 0.30, f"{total:,.0f}",
             ha="center", va="center", fontsize=18, fontweight="bold",
             color=TEXT, zorder=5)


def _plot(data: pd.DataFrame, metadata: dict[str, float | int], output: Path,
          project_root: Path) -> None:
    _configure_fonts(project_root)
    fig = plt.figure(figsize=(16, 8.5), facecolor="white")
    fig.add_artist(patches.FancyBboxPatch(
        (0.025, 0.045), 0.95, 0.89, boxstyle="round,pad=0.01,rounding_size=0.018",
        linewidth=0, facecolor=CREAM, transform=fig.transFigure, zorder=-1,
    ))
    fig.text(0.045, 0.90, " ", fontsize=2, va="center",
             bbox=dict(boxstyle="round,pad=1.5", facecolor="#4a7d75", edgecolor="none"))
    fig.text(0.061, 0.90, "Figura B.23.", fontsize=14, fontweight="bold", color=TEXT, va="center")
    fig.text(0.151, 0.90, "Tecnologías de conexión del Servicio de Televisión Restringida por segmento",
             fontsize=14, fontweight="medium", color=TEXT, va="center")
    _draw_panel(fig, data, "Residencial", float(metadata["total_residencial"]), 0.035)
    _draw_panel(fig, data, "No Residencial", float(metadata["total_no_residencial"]), 0.525)
    fig.text(0.045, 0.078, "Fuente:", fontsize=8, fontweight="bold", color=TEXT)
    fig.text(0.086, 0.078,
             f"CRT con datos de los operadores de telecomunicaciones a diciembre de {int(metadata['anio'])}.",
             fontsize=8, color=TEXT)
    fig.text(0.045, 0.057, "Nota:", fontsize=8, fontweight="bold", color=TEXT)
    fig.text(0.077, 0.057, "La suma de los porcentajes puede no sumar 100% por cuestiones de redondeo.",
             fontsize=8, color=TEXT)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  B.23 | Adquisición o reutilización de TODO.zip de BIT/CRT")
    source = context.acquire_source(SOURCE_ID)
    print("  B.23 | Lectura, agregación por tecnología y cálculo de participaciones")
    data, metadata = build_metrics(load_raw(source))
    period = f"{int(metadata['anio'])}-12"
    context.record_source_period(SOURCE_ID, period, "ULTIMO_DISPONIBLE")
    context.write_data_used(data)
    for row in data.itertuples(index=False):
        context.record_calculation(
            f"participacion_{row.segmento}_{row.tecnologia}",
            "accesos de la tecnología / total de accesos del segmento * 100",
            {"segmento": row.segmento, "tecnologia": row.tecnologia,
             "anio": row.anio, "accesos": row.accesos},
            row.participacion, "%", 1,
        )
        context.record_calculation(
            f"crecimiento_{row.segmento}_{row.tecnologia}",
            "(accesos actuales / accesos del diciembre previo - 1) * 100",
            {"actual": row.accesos, "previo": row.accesos_previos},
            row.crecimiento_anual, "%", 1,
        )
    residential = data.loc[data["segmento"].eq("Residencial")].sort_values("participacion", ascending=False)
    nonres = data.loc[data["segmento"].eq("No Residencial")].sort_values("participacion", ascending=False)
    text_path = context.render_text("b_23.md.j2", {
        "anio": int(metadata["anio"]),
        "total_residencial": float(metadata["total_residencial"]),
        "total_no_residencial": float(metadata["total_no_residencial"]),
        "residencial": residential.to_dict("records"),
        "no_residencial": nonres.to_dict("records"),
    })
    print("  B.23 | Generación del PNG")
    _plot(data, metadata, context.expected_figure_path, context.project_root)
    return {"figure_path": str(context.expected_figure_path), "text_path": str(text_path),
            "source_latest_period": period, "rows_used": len(data)}


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
