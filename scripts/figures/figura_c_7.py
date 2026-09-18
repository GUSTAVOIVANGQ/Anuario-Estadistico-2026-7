"""Figura C.7: teledensidad de telefonía móvil por entidad federativa."""
from __future__ import annotations

import json
import math
import sys
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PatchCollection

FIGURE_ID = "C.7"
SOURCE_ID = "crt_bit_todo_2025_q2"
MAP_SOURCE_ID = "mexico_geojson_legacy"
TABLE = "TD_TELEDENSIDAD_TELMOVIL_ITE_VA.csv"
NATIONAL_TABLE = "TD_TELEDENSIDAD_H_TMOVIL_ITE_VA.csv"
TEXT = "#3c3c3b"
COLORS = ["#afafaf", "#737f7c", "#63918b", "#2d4f4b", "#012f2a"]


def _member(archive: zipfile.ZipFile, table: str) -> str:
    matches = [name for name in archive.namelist()
               if PurePosixPath(name.replace("\\", "/")).name.casefold() == table.casefold()]
    if len(matches) != 1:
        raise ValueError(f"Se esperaba una tabla {table} en TODO.zip y se encontraron {len(matches)}")
    return matches[0]


def load_raw(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    with zipfile.ZipFile(path) as archive:
        with archive.open(_member(archive, TABLE)) as stream:
            states = pd.read_csv(stream, encoding="latin-1", low_memory=False)
        with archive.open(_member(archive, NATIONAL_TABLE)) as stream:
            national = pd.read_csv(stream, encoding="latin-1", low_memory=False)
    return states, national


def _num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype("string").str.replace(",", "", regex=False), errors="coerce")


def build_metrics(raw: pd.DataFrame, national_raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    data = raw.copy()
    for column in ("ANIO", "MES", "K_ENTIDAD", "T_TELMOVIL_E"):
        data[column] = _num(data[column])
    latest = int(data.loc[data["MES"].eq(12), "ANIO"].max())
    result = data.loc[
        data["ANIO"].eq(latest) & data["MES"].eq(12) & data["K_ENTIDAD"].between(1, 32),
        ["K_ENTIDAD", "ENTIDAD", "T_TELMOVIL_E"],
    ].rename(columns={"T_TELMOVIL_E": "valor"}).sort_values("K_ENTIDAD")
    if len(result) != 32:
        raise ValueError(f"C.7 requiere 32 entidades y encontró {len(result)}")
    result["K_ENTIDAD"] = result["K_ENTIDAD"].astype(int)
    national_raw = national_raw.copy()
    for column in ("ANIO", "MES", "T_H_TELMOVIL_E"):
        national_raw[column] = _num(national_raw[column])
    series = national_raw.loc[national_raw["MES"].eq(12) & national_raw["ANIO"].le(latest)].sort_values("ANIO").dropna(subset=["T_H_TELMOVIL_E"])
    current = float(series.iloc[-1]["T_H_TELMOVIL_E"])
    previous = float(series.iloc[-2]["T_H_TELMOVIL_E"]) if len(series) > 1 else math.nan
    growth = (current / previous - 1) * 100 if previous else math.nan
    return result.reset_index(drop=True), {"anio": latest, "nacional": current, "crecimiento": growth}


def _norm(value: str) -> str:
    text = "".join(c for c in unicodedata.normalize("NFKD", str(value)) if not unicodedata.combining(c))
    return " ".join(text.casefold().replace(".", "").split())


def _shapes(path: Path, values: dict[str, float], bounds: np.ndarray):
    payload = json.loads(path.read_text(encoding="utf-8"))
    lookup = {_norm(name): (name, value) for name, value in values.items()}
    aliases = {
        "coahuila": "coahuila de zaragoza", "michoacan": "michoacan de ocampo",
        "veracruz": "veracruz de ignacio de la llave", "distrito federal": "ciudad de mexico",
        "estado de mexico": "mexico",
    }
    output, facecolors, found = [], [], set()
    for feature in payload.get("features", []):
        key = aliases.get(_norm(feature.get("properties", {}).get("name", "")),
                          _norm(feature.get("properties", {}).get("name", "")))
        if key not in lookup:
            continue
        original, value = lookup[key]
        found.add(original)
        color_index = min(4, int(np.searchsorted(bounds[1:-1], value, side="right")))
        geometry = feature.get("geometry", {})
        polygons = [geometry.get("coordinates", [])] if geometry.get("type") == "Polygon" else geometry.get("coordinates", [])
        for polygon in polygons:
            if polygon:
                output.append(patches.Polygon(np.asarray(polygon[0], dtype=float), closed=True))
                facecolors.append(COLORS[color_index])
    if len(found) != 32:
        raise ValueError(f"No se empataron las 32 entidades: {sorted(set(values) - found)}")
    return output, facecolors


def _plot(data: pd.DataFrame, meta: dict, map_path: Path, output: Path) -> None:
    values = dict(zip(data["ENTIDAD"], data["valor"]))
    bounds = np.unique(np.quantile(data["valor"], [0, .2, .4, .6, .8, 1]))
    if len(bounds) != 6:
        bounds = np.linspace(float(data.valor.min()), float(data.valor.max()) + .01, 6)
    shape_list, facecolors = _shapes(map_path, values, bounds)
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.025, .045), .95, .89, boxstyle="round,pad=.01,rounding_size=.018",
                                          lw=0, fc="#F8F8FA", transform=fig.transFigure, zorder=-1))
    fig.text(.045, .9, " ", bbox=dict(boxstyle="round,pad=1.5", fc="#4a7d75", ec="none"))
    fig.text(.061, .9, "Figura C.7.", fontsize=14, fontweight="bold", color=TEXT, va="center")
    fig.text(.145, .9, f"Líneas del servicio móvil de telefonía por cada 100 habitantes ({meta['anio']})",
             fontsize=14, color=TEXT, va="center")
    ax = fig.add_axes([.18, .18, .61, .65])
    ax.add_collection(PatchCollection(shape_list, facecolor=facecolors, edgecolor="white", linewidth=.7))
    ax.set_xlim(-119.5, -85); ax.set_ylim(14, 33.5); ax.set_aspect(1 / np.cos(np.deg2rad(23.5))); ax.axis("off")
    labels = [f"{bounds[i]:.0f} a {bounds[i+1]:.0f}" for i in range(5)]
    handles = [patches.Patch(facecolor=color, label=label) for color, label in zip(COLORS, labels)]
    legend = fig.legend(handles=handles, title="Líneas por cada 100 habitantes:", loc="lower left",
                        bbox_to_anchor=(.06, .18), frameon=False, fontsize=9, title_fontsize=9)
    legend._legend_box.align = "left"; legend.get_title().set_fontweight("bold"); legend.get_title().set_color(TEXT)
    fig.add_artist(patches.FancyBboxPatch((.76, .54), .18, .22, transform=fig.transFigure,
                   boxstyle="round,pad=.015,rounding_size=.02", fc="white", ec="#E4E4E8"))
    fig.text(.85, .69, "Líneas por cada\n100 habitantes:", ha="center", fontsize=10, color=TEXT)
    fig.text(.85, .585, f"{meta['nacional']:.0f}", ha="center", fontsize=43, fontweight="bold", color=TEXT)
    if not math.isnan(meta["crecimiento"]):
        fig.text(.51, .18, f"Tasa de crecimiento\nanual de {meta['crecimiento']:.1f}%", ha="center", va="center",
                 fontsize=10, fontweight="bold", color="white", bbox=dict(boxstyle="round,pad=.8", fc=TEXT, ec="none"))
    fig.text(.05, .07, "Fuente:", fontsize=8, fontweight="bold", color=TEXT)
    fig.text(.091, .07, f"CRT con datos de los operadores de telecomunicaciones a diciembre de {meta['anio']}.", fontsize=8, color=TEXT)
    fig.text(.05, .05, "Nota:", fontsize=8, fontweight="bold", color=TEXT)
    fig.text(.082, .05, "El indicador nacional proviene de la serie nacional publicada por el CRT.", fontsize=8, color=TEXT)
    output.parent.mkdir(parents=True, exist_ok=True); fig.savefig(output, dpi=200, facecolor="white"); plt.close(fig)


def generate(context):
    print("  C.7 | Adquisición o reutilización de TODO.zip y mapa estatal")
    source = context.acquire_source(SOURCE_ID); map_path = context.acquire_source(MAP_SOURCE_ID)
    states, national = load_raw(source); data, meta = build_metrics(states, national); period = f"{meta['anio']}-12"
    context.record_source_period(SOURCE_ID, period, "ULTIMO_DISPONIBLE"); context.record_source_period(MAP_SOURCE_ID, "geometría estatal", "REFERENCIA")
    context.write_data_used(data)
    for row in data.itertuples(index=False):
        context.record_calculation(f"teledensidad_{row.K_ENTIDAD:02d}", "T_TELMOVIL_E publicado por BIT",
                                   {"anio": meta["anio"], "entidad": row.ENTIDAD}, row.valor, "líneas por cada 100 habitantes", 0)
    context.record_calculation("teledensidad_nacional", "T_H_TELMOVIL_E nacional publicado por BIT",
                               {"anio": meta["anio"]}, meta["nacional"], "líneas por cada 100 habitantes", 0)
    high = data.loc[data.valor.idxmax()]; low = data.loc[data.valor.idxmin()]
    text = context.render_text("c_mobile.md.j2", {"resumen": f"En {meta['anio']}, {high.ENTIDAD} tuvo el valor estatal más alto ({high.valor:.0f}) y {low.ENTIDAD} el menor ({low.valor:.0f})."})
    print(data.to_string(index=False)); _plot(data, meta, map_path, context.expected_figure_path)
    return {"figure_path": str(context.expected_figure_path), "text_path": str(text), "source_latest_period": period, "rows_used": len(data)}


def main() -> int:
    root = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(root / "src"))
    from anuario2026.pipeline import run_pipeline
    run_pipeline(root, only=FIGURE_ID); return 0


if __name__ == "__main__": raise SystemExit(main())
