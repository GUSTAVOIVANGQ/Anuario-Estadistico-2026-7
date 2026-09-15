"""B.20: script autónomo de adquisición, cálculo, reporte, texto y gráfica."""

from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui

import json
import math
import textwrap
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
from matplotlib.collections import PatchCollection
from matplotlib.ticker import FuncFormatter


BIT_SOURCE_ID = "crt_bit_todo_2025_q2"
ENDUTIH_SOURCE_ID = "inegi_endutih_2025"
DENUE_SOURCE_ID = "inegi_denue_2023_state_counts"
MAP_SOURCE_ID = "mexico_geojson_legacy"

TEXT = "#4B4B83"
TEAL = "#317DA3"
LIGHT = "#ADDCDF"
CORAL = "#F2535A"
SALMON = "#F58F82"
CREAM = "#FBFBF7"
GRID = "#DCEFF0"
MAP_COLORS = [LIGHT, TEAL, TEXT, SALMON, CORAL]
STACK_COLORS = [TEAL, LIGHT, TEXT, SALMON, CORAL, "#6CBFC4", "#9A9ABC"]

MONTHS = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo",
    6: "junio", 7: "julio", 8: "agosto", 9: "septiembre",
    10: "octubre", 11: "noviembre", 12: "diciembre",
}

TITLES = {
    "B.4": "Líneas del Servicio Fijo de Telefonía",
    "B.5": "Líneas del Servicio Fijo de Telefonía por cada 100 hogares",
    "B.6": "Líneas del Servicio Fijo de Telefonía Residencial por cada 100 hogares por entidad federativa",
    "B.7": "Líneas del Servicio Fijo de Telefonía No Residencial por cada 100 unidades económicas por entidad federativa",
    "B.8": "Tráfico de minutos del Servicio Fijo de Telefonía",
    "B.9": "Participación de mercado del Servicio Fijo de Telefonía",
    "B.10": "Herfindahl-Hirschman (IHH). Concentración de mercado del Servicio Fijo de Telefonía",
    "B.11": "Accesos del Servicio Fijo de Internet",
    "B.12": "Accesos del Servicio Fijo de Internet por cada 100 hogares",
    "B.13": "Accesos del Servicio Fijo de Acceso a Internet Residencial por cada 100 hogares por entidad federativa",
    "B.14": "Accesos del Servicio Fijo de Internet No Residencial por cada 100 unidades económicas por entidad federativa",
    "B.15": "Distribución de los accesos del Servicio Fijo de Internet por rangos de velocidad",
    "B.16": "Distribución de los accesos al servicio fijo de Internet por tecnología de conexión y por segmento",
    "B.17": "Participación de mercado del servicio fijo de Internet",
    "B.18": "Herfindahl-Hirschman (IHH). Concentración de mercado del Servicio Fijo de Internet",
    "B.19": "Accesos del Servicio de Televisión Restringida",
    "B.20": "Accesos del Servicio de Televisión Restringida por cada 100 hogares",
}


def _configure_fonts(project_root: Path) -> None:
    font_dir = project_root / "assets" / "fonts" / "Noto_Sans"
    for name in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf"):
        path = font_dir / name
        if path.is_file():
            font_manager.fontManager.addfont(path)
    available = {item.name for item in font_manager.fontManager.ttflist}
    plt.rcParams.update({
        "font.family": "Noto Sans" if "Noto Sans" in available else "DejaVu Sans",
        "axes.unicode_minus": False,
    })


def _member(archive: zipfile.ZipFile, basename: str) -> str:
    matches = [
        name for name in archive.namelist()
        if PurePosixPath(name.replace("\\", "/")).name.casefold() == basename.casefold()
    ]
    if len(matches) != 1:
        raise ValueError(f"Se esperaba una tabla {basename} dentro de TODO.zip y se encontraron {len(matches)}")
    return matches[0]


def read_bit_table(path: Path, basename: str) -> pd.DataFrame:
    """Lee una sola tabla cruda del ZIP compartido sin extraer el resto."""
    with zipfile.ZipFile(path) as archive:
        with archive.open(_member(archive, basename)) as stream:
            frame = pd.read_csv(stream, encoding="latin-1", low_memory=False)
    frame.columns = [str(column).strip() for column in frame.columns]
    return frame


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype("string")
        .str.strip()
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .replace({"": pd.NA, "-": pd.NA, "nan": pd.NA, "<NA>": pd.NA}),
        errors="coerce",
    )


def _latest_december(frame: pd.DataFrame) -> int:
    years = numeric(frame.loc[numeric(frame["MES"]).eq(12), "ANIO"]).dropna().astype(int)
    if years.empty:
        raise ValueError("La tabla BIT no contiene un corte de diciembre")
    return int(years.max())


def _series_sum(frame: pd.DataFrame, column: str, start: int) -> tuple[pd.DataFrame, dict]:
    data = frame.copy()
    for field in ("ANIO", "MES", column):
        data[field] = numeric(data[field])
    latest = _latest_december(data)
    result = (
        data.loc[data["MES"].eq(12)]
        .groupby("ANIO", as_index=False)[column]
        .sum(min_count=1)
        .loc[lambda x: x["ANIO"].between(start, latest)]
        .sort_values("ANIO")
        .reset_index(drop=True)
    )
    result["ANIO"] = result["ANIO"].astype(int)
    return result, {"year": latest, "month": 12, "value": float(result.iloc[-1][column])}


def _series_field(frame: pd.DataFrame, column: str, start: int) -> tuple[pd.DataFrame, dict]:
    data = frame.copy()
    for field in ("ANIO", "MES", column):
        data[field] = numeric(data[field])
    latest = _latest_december(data)
    result = (
        data.loc[data["MES"].eq(12) & data["ANIO"].between(start, latest), ["ANIO", column]]
        .dropna()
        .sort_values("ANIO")
        .drop_duplicates("ANIO", keep="last")
        .reset_index(drop=True)
    )
    result["ANIO"] = result["ANIO"].astype(int)
    return result, {"year": latest, "month": 12, "value": float(result.iloc[-1][column])}


def _normalize_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", str(value))
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold().strip().replace(".", "")


def _load_households(path: Path) -> pd.DataFrame:
    table = "tr_endutih_hogares_anual_2025.csv"
    with zipfile.ZipFile(path) as archive:
        name = _member(archive, table)
        with archive.open(name) as stream:
            header = pd.read_csv(stream, nrows=0)
        entity = "CVE_ENT" if "CVE_ENT" in header.columns else "ENT"
        with archive.open(name) as stream:
            frame = pd.read_csv(stream, usecols=[entity, "FAC_HOG"], dtype=str, low_memory=False)
    frame = frame.rename(columns={entity: "K_ENTIDAD"})
    frame["K_ENTIDAD"] = numeric(frame["K_ENTIDAD"])
    frame["FAC_HOG"] = numeric(frame["FAC_HOG"])
    return frame.loc[frame["K_ENTIDAD"].between(1, 32)].groupby("K_ENTIDAD", as_index=False)["FAC_HOG"].sum()


def _map_from_bit_fields(bit_path: Path, figure_id: str) -> tuple[pd.DataFrame, dict]:
    configs = {
        "B.6": ("P_RES_H_TELFIJA_E", "P_RES_H_TELFIJA_E"),
        "B.7": ("P_NRES_H_TELFIJA_E", "P_NRES_H_TELFIJA_E"),
    }
    column, national_column = configs[figure_id]
    states = read_bit_table(bit_path, "TD_PENETRACIONES_TELFIJA_ITE_VA.csv")
    national = read_bit_table(bit_path, "TD_PENETRACION_H_TELFIJA_ITE_VA.csv")
    for data in (states, national):
        data["ANIO"] = numeric(data["ANIO"])
        data["MES"] = numeric(data["MES"])
    states[column] = numeric(states[column])
    national[national_column] = numeric(national[national_column])
    latest = _latest_december(states)
    current = states.loc[states["ANIO"].eq(latest) & states["MES"].eq(12), ["K_ENTIDAD", "ENTIDAD", column]].copy()
    current["K_ENTIDAD"] = numeric(current["K_ENTIDAD"]).astype(int)
    current = current.rename(columns={column: "valor"}).sort_values("K_ENTIDAD")
    national_series = national.loc[national["MES"].eq(12)].set_index("ANIO")[national_column]
    value = float(national_series.loc[latest])
    previous = float(national_series.loc[latest - 1]) if latest - 1 in national_series.index else math.nan
    growth = (value / previous - 1) * 100 if previous and not math.isnan(previous) else math.nan
    return current, {"year": latest, "month": 12, "value": value, "previous": previous, "growth": growth}


def _map_baf_residential(bit_path: Path, households_path: Path) -> tuple[pd.DataFrame, dict]:
    raw = read_bit_table(bit_path, "TD_ACC_BAF_XT_XC_VA.csv")
    for column in ("ANIO", "MES", "K_ENTIDAD", "A_RESIDENCIAL_E"):
        raw[column] = numeric(raw[column])
    latest = _latest_december(raw)
    grouped = (
        raw.loc[raw["ANIO"].eq(latest) & raw["MES"].eq(12) & raw["K_ENTIDAD"].between(1, 32)]
        .groupby(["K_ENTIDAD", "ENTIDAD"], as_index=False)["A_RESIDENCIAL_E"]
        .sum(min_count=1)
    )
    homes = _load_households(households_path)
    result = grouped.merge(homes, on="K_ENTIDAD", validate="one_to_one")
    result["valor"] = result["A_RESIDENCIAL_E"] / result["FAC_HOG"] * 100
    current_total = float(result["A_RESIDENCIAL_E"].sum())
    home_total = float(result["FAC_HOG"].sum())
    previous_total = numeric(raw.loc[raw["ANIO"].eq(latest - 1) & raw["MES"].eq(12) & raw["K_ENTIDAD"].between(1, 32), "A_RESIDENCIAL_E"]).sum()
    growth = (current_total / previous_total - 1) * 100 if previous_total else math.nan
    result["K_ENTIDAD"] = result["K_ENTIDAD"].astype(int)
    return result.sort_values("K_ENTIDAD"), {
        "year": latest, "month": 12, "denominator_year": 2025,
        "value": current_total / home_total * 100, "growth": growth,
        "numerator": current_total, "denominator": home_total,
    }


def _map_baf_nonresidential(bit_path: Path, denue_path: Path) -> tuple[pd.DataFrame, dict]:
    raw = read_bit_table(bit_path, "TD_ACC_BAF_XT_XC_VA.csv")
    for column in ("ANIO", "MES", "K_ENTIDAD", "A_NO_RESIDENCIAL_E"):
        raw[column] = numeric(raw[column])
    latest = _latest_december(raw)
    grouped = (
        raw.loc[raw["ANIO"].eq(latest) & raw["MES"].eq(12) & raw["K_ENTIDAD"].between(1, 32)]
        .groupby(["K_ENTIDAD", "ENTIDAD"], as_index=False)["A_NO_RESIDENCIAL_E"]
        .sum(min_count=1)
    )
    units = pd.read_csv(denue_path, encoding="utf-8-sig")
    units["UNIDADES"] = numeric(units["UNIDADES"])
    units["key"] = units["ENTIDAD"].map(_normalize_name)
    grouped["key"] = grouped["ENTIDAD"].map(_normalize_name)
    result = grouped.merge(units[["key", "UNIDADES"]], on="key", validate="one_to_one")
    result["valor"] = result["A_NO_RESIDENCIAL_E"] / result["UNIDADES"] * 100
    current_total = float(result["A_NO_RESIDENCIAL_E"].sum())
    unit_total = float(result["UNIDADES"].sum())
    previous_total = numeric(raw.loc[raw["ANIO"].eq(latest - 1) & raw["MES"].eq(12) & raw["K_ENTIDAD"].between(1, 32), "A_NO_RESIDENCIAL_E"]).sum()
    growth = (current_total / previous_total - 1) * 100 if previous_total else math.nan
    result["K_ENTIDAD"] = result["K_ENTIDAD"].astype(int)
    return result.sort_values("K_ENTIDAD"), {
        "year": latest, "month": 12, "denominator_year": 2023,
        "value": current_total / unit_total * 100, "growth": growth,
        "numerator": current_total, "denominator": unit_total,
    }


def _market_share(frame: pd.DataFrame, figure_id: str) -> tuple[pd.DataFrame, dict]:
    data = frame.copy()
    for column in ("ANIO", "MES", "MARKET_SHARE"):
        data[column] = numeric(data[column])
    latest = _latest_december(data)
    data = data.loc[data["MES"].eq(12) & data["ANIO"].between(2013, latest)].copy()

    def group_name(value: str) -> str:
        key = _normalize_name(value).upper()
        if any(word in key for word in ("AMERICA MOVIL", "TELMEX", "TELNOR")):
            return "América Móvil"
        if any(word in key for word in ("GRUPO TELEVISA", "CABLEVISION")):
            return "Grupo Televisa"
        if "MEGACABLE" in key:
            return "Megacable-MCM"
        if any(word in key for word in ("GRUPO SALINAS", "TOTALPLAY")):
            return "Grupo Salinas"
        if "AXTEL" in key:
            return "Axtel"
        if "TELEFONICA" in key:
            return "Telefónica"
        if "MAXCOM" in key:
            return "Maxcom"
        return "Otros"

    data["grupo"] = data["GRUPO"].map(group_name)
    pivot = data.groupby(["ANIO", "grupo"])["MARKET_SHARE"].sum().unstack(fill_value=0)
    order = ["América Móvil", "Grupo Televisa", "Megacable-MCM", "Grupo Salinas", "Axtel", "Telefónica", "Maxcom", "Otros"]
    pivot = pivot.reindex(columns=[name for name in order if name in pivot.columns], fill_value=0)
    pivot.index = pivot.index.astype(int)
    result = pivot.reset_index()
    leader = pivot.loc[latest].idxmax()
    return result, {"year": latest, "month": 12, "value": float(pivot.loc[latest, leader]), "leader": leader}


def _ihh(frame: pd.DataFrame, column: str) -> tuple[pd.DataFrame, dict]:
    data = frame.copy()
    for field in ("ANIO", "MES", column):
        data[field] = numeric(data[field])
    latest = _latest_december(data)
    result = data.loc[data["MES"].eq(12) & data["ANIO"].between(2013, latest), ["ANIO", column]].dropna().sort_values("ANIO")
    result["ANIO"] = result["ANIO"].astype(int)
    return result.reset_index(drop=True), {"year": latest, "month": 12, "value": float(result.iloc[-1][column])}


def _speed(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    columns = ["A_V1_E", "A_V2_E", "A_V3_E", "A_V4_E", "A_NO_ESPECIFICADO_E", "A_TOTAL_E"]
    data = frame.copy()
    for field in ("ANIO", "MES", *columns):
        data[field] = numeric(data[field])
    latest = _latest_december(data)
    annual = data.loc[data["MES"].eq(12) & data["ANIO"].between(2013, latest)].groupby("ANIO")[columns].sum(min_count=1)
    component_total = annual[columns[:-1]].sum(axis=1)
    annual["total_validado"] = annual["A_TOTAL_E"].where(annual["A_TOTAL_E"].gt(0), component_total)
    labels = {
        "A_V1_E": "256 Kbps a 1.99 Mbps", "A_V2_E": "2 a 9.99 Mbps",
        "A_V3_E": "10 a 100 Mbps", "A_V4_E": "Mayores a 100 Mbps",
        "A_NO_ESPECIFICADO_E": "Sin información de velocidad",
    }
    result = pd.DataFrame({"ANIO": annual.index.astype(int)})
    for field, label in labels.items():
        result[label] = annual[field].to_numpy() / annual["total_validado"].to_numpy() * 100
    total = float(annual.loc[latest, "total_validado"])
    return result.reset_index(drop=True), {"year": latest, "month": 12, "value": total}


def _technology(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    data = frame.copy()
    for field in ("ANIO", "MES", "A_RESIDENCIAL_E", "A_NO_RESIDENCIAL_E"):
        data[field] = numeric(data[field])
    latest = _latest_december(data)

    def category(value: str) -> str | None:
        key = _normalize_name(value)
        if "fibra" in key:
            return "Fibra óptica"
        if "coaxial" in key:
            return "Cable coaxial"
        if key == "dsl" or "cobre" in key:
            return "DSL"
        if "movil" in key:
            return "Tecnología móvil"
        if "satel" in key:
            return "Satelital"
        return None

    data["tecnologia"] = data["TECNO_ACCESO_INTERNET"].map(category)
    data = data.loc[data["tecnologia"].notna() & data["MES"].eq(12) & data["ANIO"].isin([latest - 1, latest])]
    grouped = data.groupby(["ANIO", "tecnologia"])[["A_RESIDENCIAL_E", "A_NO_RESIDENCIAL_E"]].sum(min_count=1).fillna(0)
    order = ["Fibra óptica", "Cable coaxial", "DSL", "Tecnología móvil", "Satelital"]
    rows = []
    for technology in order:
        row = {"tecnologia": technology}
        for year, suffix in ((latest - 1, "previo"), (latest, "actual")):
            values = grouped.loc[(year, technology)] if (year, technology) in grouped.index else pd.Series(dtype=float)
            row[f"residencial_{suffix}"] = float(values.get("A_RESIDENCIAL_E", 0))
            row[f"no_residencial_{suffix}"] = float(values.get("A_NO_RESIDENCIAL_E", 0))
        rows.append(row)
    result = pd.DataFrame(rows)
    res_total = result["residencial_actual"].sum()
    nores_total = result["no_residencial_actual"].sum()
    for prefix, total in (("residencial", res_total), ("no_residencial", nores_total)):
        result[f"{prefix}_pct"] = result[f"{prefix}_actual"] / total * 100 if total else 0
        result[f"{prefix}_crecimiento"] = np.where(
            result[f"{prefix}_previo"].gt(0),
            (result[f"{prefix}_actual"] / result[f"{prefix}_previo"] - 1) * 100,
            np.nan,
        )
    res_previous = result["residencial_previo"].sum()
    nores_previous = result["no_residencial_previo"].sum()
    return result, {
        "year": latest, "month": 12, "value": res_total + nores_total,
        "res_total": res_total, "nores_total": nores_total,
        "res_growth": (res_total / res_previous - 1) * 100 if res_previous else math.nan,
        "nores_growth": (nores_total / nores_previous - 1) * 100 if nores_previous else math.nan,
    }


def calculate(figure_id: str, bit_path: Path, endutih_path: Path | None = None, denue_path: Path | None = None) -> tuple[pd.DataFrame, dict]:
    if figure_id == "B.4":
        return _series_sum(read_bit_table(bit_path, "TD_LINEAS_HIST_TELFIJA_ITE_VA.csv"), "L_TOTAL_E", 2000)
    if figure_id == "B.5":
        return _series_field(read_bit_table(bit_path, "TD_PENETRACION_H_TELFIJA_ITE_VA.csv"), "P_H_TELFIJA_E", 1971)
    if figure_id in {"B.6", "B.7"}:
        return _map_from_bit_fields(bit_path, figure_id)
    if figure_id == "B.8":
        data, meta = _series_sum(read_bit_table(bit_path, "TD_TRAF_HIST_TELFIJA_ITE_VA.csv"), "TRAF_E", 2000)
        data["TRAFICO_MILLONES_MINUTOS"] = data["TRAF_E"] / 1_000_000
        meta["value_raw"] = meta["value"]
        meta["value"] /= 1_000_000
        return data, meta
    if figure_id == "B.9":
        return _market_share(read_bit_table(bit_path, "TD_MARKET_SHARE_TELFIJA_ITE_VA.csv"), figure_id)
    if figure_id == "B.10":
        return _ihh(read_bit_table(bit_path, "TD_IHH_TELFIJA_ITE_VA.csv"), "IHH_TELFIJA_E")
    if figure_id == "B.11":
        return _series_sum(read_bit_table(bit_path, "TD_ACC_INTER_HIS_ITE_VA.csv"), "A_TOTAL_E", 2000)
    if figure_id == "B.12":
        return _series_field(read_bit_table(bit_path, "TD_PENETRACION_H_BAF_ITE_VA.csv"), "P_BAF_E", 2000)
    if figure_id == "B.13":
        if endutih_path is None:
            raise ValueError("B.13 requiere el ZIP ENDUTIH 2025")
        return _map_baf_residential(bit_path, endutih_path)
    if figure_id == "B.14":
        if denue_path is None:
            raise ValueError("B.14 requiere el desglose estatal DENUE")
        return _map_baf_nonresidential(bit_path, denue_path)
    if figure_id == "B.15":
        return _speed(read_bit_table(bit_path, "TD_ACC_BAFXV_ITE_VA.csv"))
    if figure_id == "B.16":
        return _technology(read_bit_table(bit_path, "TD_ACC_BAF_XT_XC_VA.csv"))
    if figure_id == "B.17":
        return _market_share(read_bit_table(bit_path, "TD_MARKET_SHARE_BAF_ITE_VA.csv"), figure_id)
    if figure_id == "B.18":
        return _ihh(read_bit_table(bit_path, "TD_IHH_BAF_ITE_VA.csv"), "IHH_BAF_E")
    if figure_id == "B.19":
        return _series_sum(read_bit_table(bit_path, "TD_ACC_TVRES_HIS_ITE_VA.csv"), "A_TOTAL_E", 1998)
    if figure_id == "B.20":
        return _series_field(read_bit_table(bit_path, "TD_PENETRACION_H_TVRES_ITE_VA.csv"), "P_H_TVRES_E", 1998)
    raise ValueError(f"Figura no soportada: {figure_id}")


def _base(figure_id: str, year: int, start: int | None = None) -> tuple[plt.Figure, plt.Axes]:
    """Lienzo editorial equivalente al usado por las figuras B del Anuario 2024."""
    fig = plt.figure(figsize=(16, 8.5), facecolor="white")
    ax = fig.add_axes([0.075, 0.205, 0.88, 0.61])
    fig.add_artist(patches.Rectangle(
        (0.055, 0.918), 0.009, 0.020, transform=fig.transFigure,
        facecolor="#4a7d75", edgecolor="none", linewidth=0,
    ))
    fig.text(0.069, 0.927, f"Figura {figure_id}.", fontsize=13.2, fontweight="bold", color="#3c3c3b", va="center")
    period = f" ({start}-{year})" if start else ""
    fig.text(0.145 if len(figure_id) == 3 else 0.153, 0.927, TITLES[figure_id] + period,
             fontsize=11.8 if len(TITLES[figure_id]) > 82 else 13.2, color="#3c3c3b", va="center")
    ax.set_facecolor("#F8F8FA")
    for spine in ax.spines.values():
        spine.set_color("#7c7c7c")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors="#3c3c3b", length=0)
    return fig, ax


def _footer(fig: plt.Figure, source: str, note: str = "") -> None:
    fig.text(0.055, 0.075, "Fuente:", fontsize=8, fontweight="bold", color=TEXT, va="top")
    fig.text(0.095, 0.075, textwrap.fill(source, 205), fontsize=8, color=TEXT, va="top")
    if note:
        fig.text(0.055, 0.045, "Nota:", fontsize=8, fontweight="bold", color=TEXT, va="top")
        fig.text(0.086, 0.045, textwrap.fill(note, 210), fontsize=8, color=TEXT, va="top")


def _plot_series(figure_id: str, data: pd.DataFrame, meta: dict, output: Path) -> None:
    configs = {
        "B.4": ("L_TOTAL_E", 2000, "Líneas totales", "#006157"),
        "B.5": ("P_H_TELFIJA_E", 1971, "Líneas por cada 100 hogares", "#335a5c"),
        "B.11": ("A_TOTAL_E", 2000, "Accesos totales", "#006157"),
        "B.12": ("P_BAF_E", 2000, "Accesos por cada 100 hogares", "#006157"),
        "B.19": ("A_TOTAL_E", 1998, "Accesos totales", "#006157"),
        "B.20": ("P_H_TVRES_E", 1998, "Accesos por cada 100 hogares", "#86adae"),
    }
    column, start, legend, color = configs[figure_id]
    fig, ax = _base(figure_id, meta["year"], start)
    x = np.arange(len(data))
    y = data[column].to_numpy(float)

    if figure_id in {"B.5", "B.20"}:
        # En 2024 estas dos figuras son barras verticales rectangulares con chip numérico.
        bars = ax.bar(x, y, width=0.70, color=color, edgecolor="none", zorder=2)
        for bar, value in zip(bars, y, strict=True):
            ax.annotate(
                f"{value:,.0f}",
                (bar.get_x() + bar.get_width() / 2, value),
                xytext=(0, 6), textcoords="offset points", ha="center", va="bottom",
                fontsize=7.1, color="#3c3c3b",
                bbox=dict(boxstyle="round,pad=0.30,rounding_size=0.8", facecolor="white", edgecolor=color, linewidth=0.8),
                zorder=4,
            )
        ax.grid(axis="y", color="#d1d1d1", linewidth=1.0, zorder=0)
        ax.set_axisbelow(True)
        ax.set_ylim(0, max(y) * (1.35 if figure_id == "B.20" else 1.15))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    else:
        # B.4, B.11, B.12 y B.19 conservan la serie de línea + área del 2024.
        ax.plot(x, y, color=color, linewidth=1.5, marker="o", markersize=4.0,
                markerfacecolor=color, markeredgecolor="none", zorder=4, label=legend)
        ax.fill_between(x, 0, y, color=color, alpha=0.16, zorder=1)
        ax.grid(axis="y", color="#d1d1d1", linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
        if figure_id == "B.12":
            # El referente coloca chip blanco delineado en cada observación.
            for xpos, value in zip(x, y, strict=True):
                ax.annotate(
                    f"{value:,.0f}", (xpos, value), xytext=(0, 7), textcoords="offset points",
                    ha="center", va="bottom", fontsize=6.6, color="#3c3c3b",
                    bbox=dict(boxstyle="round,pad=0.30,rounding_size=0.8", facecolor="white", edgecolor=color, linewidth=0.8),
                    zorder=5,
                )
        else:
            # Los extremos se muestran como números simples, sin chip.
            for xpos, value, ha in ((x[0], y[0], "left"), (x[-1], y[-1], "right")):
                ax.annotate(f"{value:,.0f}", (xpos, value), xytext=(0, 9), textcoords="offset points",
                            ha=ha, va="bottom", fontsize=7.5, fontweight="bold", color="#3c3c3b")
        ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.21), frameon=False, fontsize=9, labelcolor="#3c3c3b")

    step = 1 if len(data) <= 30 else 2
    ax.set_xticks(x[::step], data["ANIO"].astype(str).iloc[::step], rotation=90, fontsize=7.5)
    ax.tick_params(axis="y", labelsize=8)
    note = ""
    if figure_id == "B.12":
        note = "Indicador expresado por cada 100 hogares."
    _footer(fig, f"CRT con datos proporcionados por los operadores de telecomunicaciones a diciembre de {meta['year']}.", note)
    output.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def _geo_shapes(path: Path, values: dict[str, float], breaks: list[float]):
    payload = json.loads(path.read_text(encoding="utf-8"))
    lookup = {_normalize_name(name): (name, value) for name, value in values.items()}
    shapes, colors, found = [], [], set()
    for feature in payload.get("features", []):
        key = _normalize_name(feature.get("properties", {}).get("name", ""))
        aliases = {"coahuila": "coahuila de zaragoza", "michoacan": "michoacan de ocampo", "veracruz": "veracruz de ignacio de la llave", "mexico": "mexico"}
        key = aliases.get(key, key)
        if key not in lookup:
            continue
        name, value = lookup[key]
        found.add(name)
        index = max(0, min(4, int(np.searchsorted(breaks[1:-1], value, side="right"))))
        geometry = feature.get("geometry", {})
        polygons = [geometry.get("coordinates", [])] if geometry.get("type") == "Polygon" else geometry.get("coordinates", [])
        for polygon in polygons:
            if polygon:
                shapes.append(patches.Polygon(np.asarray(polygon[0], dtype=float), closed=True))
                colors.append(MAP_COLORS[index])
    if len(found) != 32:
        missing = sorted(set(values) - found)
        raise ValueError(f"No se empataron las 32 entidades con el mapa: {missing}")
    return shapes, colors


def _plot_map(figure_id: str, data: pd.DataFrame, meta: dict, geojson: Path, output: Path) -> None:
    configs = {
        "B.6": ([0, 29, 43, 56, 69, math.inf], ["Menos de 29", "29 a 42", "43 a 55", "56 a 68", "Más de 68"], "Líneas residenciales por cada 100 hogares"),
        "B.7": ([0, 39, 61, 98, 115, math.inf], ["Menos de 39", "39 a 60", "61 a 97", "98 a 114", "Más de 114"], "Líneas no residenciales por cada 100 unidades económicas"),
        "B.13": ([0, 36, 48, 60, 71, math.inf], ["Menos de 36", "36 a 47", "48 a 59", "60 a 70", "Más de 70"], "Accesos residenciales por cada 100 hogares"),
        "B.14": ([0, 28, 44, 60, 76, math.inf], ["Menos de 28", "28 a 43", "44 a 59", "60 a 75", "Más de 75"], "Accesos no residenciales por cada 100 unidades económicas"),
    }
    breaks, labels, legend_title = configs[figure_id]
    fig, ax = _base(figure_id, meta["year"])
    # El mapa crece para ocupar el espacio de las ilustraciones editoriales
    # excluidas; la leyenda y el indicador nacional permanecen dentro del área.
    ax.set_position([0.175, 0.165, 0.65, 0.67])
    values = dict(zip(data["ENTIDAD"], data["valor"]))
    shape_list, colors = _geo_shapes(geojson, values, breaks)
    ax.add_collection(PatchCollection(shape_list, facecolor=colors, edgecolor="white", linewidth=0.65))
    ax.set_xlim(-119.5, -85)
    ax.set_ylim(14, 33.5)
    ax.set_aspect(1 / np.cos(np.deg2rad(23.5)))
    ax.axis("off")
    handles = [patches.Patch(facecolor=color, edgecolor="none", label=label) for color, label in zip(MAP_COLORS, labels)]
    legend = fig.legend(handles=handles, title=legend_title + ":", loc="lower left", bbox_to_anchor=(0.06, 0.19),
                        frameon=False, fontsize=9.5, title_fontsize=9.5, labelcolor=TEXT)
    legend._legend_box.align = "left"
    legend.get_title().set_fontweight("bold")
    legend.get_title().set_color(TEXT)
    bx, by, bw, bh = 0.755, 0.555, 0.19, 0.22
    fig.add_artist(patches.FancyBboxPatch((bx, by), bw, bh, transform=fig.transFigure,
                   boxstyle="round,pad=0.015,rounding_size=0.02", facecolor=CREAM, edgecolor="#E4E4E8"))
    fig.text(bx + bw / 2, by + bh * 0.73, legend_title + ":", ha="center", va="center", fontsize=9.5, color=TEXT, wrap=True)
    fig.text(bx + bw / 2, by + bh * 0.28, f"{meta['value']:.0f}", ha="center", va="center", fontsize=42, fontweight="bold", color=TEXT)
    if not math.isnan(meta.get("growth", math.nan)):
        fig.text(0.46, 0.185, f"Tasa de crecimiento\nanual de {meta['growth']:.1f}%", ha="center", va="center",
                 fontsize=9.5, fontweight="bold", color="white",
                 bbox=dict(boxstyle="round,pad=0.8", facecolor=TEXT, edgecolor="none"))
    source = f"CRT con datos de los operadores de telecomunicaciones a diciembre de {meta['year']}."
    if figure_id == "B.13":
        source = f"CRT con datos de los operadores a diciembre de {meta['year']} y ENDUTIH 2025 del INEGI."
    elif figure_id == "B.14":
        source = f"CRT con datos de los operadores a diciembre de {meta['year']} y DENUE del INEGI a noviembre de 2023."
    _footer(fig, source)
    output.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def _plot_share(figure_id: str, data: pd.DataFrame, meta: dict, output: Path) -> None:
    fig, ax = _base(figure_id, meta["year"], 2013)
    categories = [column for column in data.columns if column != "ANIO"]
    x = np.arange(len(data))
    bottom = np.zeros(len(data))
    for index, category in enumerate(categories):
        values = data[category].to_numpy(float)
        bars = ax.bar(x, values, bottom=bottom, width=0.58, color=STACK_COLORS[index % len(STACK_COLORS)], label=category)
        for bar, value, base in zip(bars, values, bottom):
            if value >= 2.0:
                ax.text(bar.get_x() + bar.get_width() / 2, base + value / 2, f"{value:.1f}%", ha="center", va="center",
                        fontsize=6.3, fontweight="bold", color="white" if index not in (1, 3) else TEXT)
        bottom += values
    ax.set_ylim(0, 100)
    ax.set_yticks([])
    ax.set_xticks(x, data["ANIO"].astype(str), fontsize=8, fontweight="bold")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.20), ncol=min(8, len(categories)), frameon=False, fontsize=7.5, labelcolor=TEXT)
    note = "Participación de mercado calculada con respecto al número de líneas del servicio."
    if figure_id == "B.17":
        note = "Participación de mercado calculada con respecto al número de accesos del servicio fijo de Internet."
    _footer(fig, f"CRT con datos proporcionados por los operadores de telecomunicaciones a diciembre de {meta['year']}.", note)
    output.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def _plot_ihh(figure_id: str, data: pd.DataFrame, meta: dict, output: Path) -> None:
    column = next(column for column in data.columns if column not in {"ANIO", "MES"})
    fig, ax = _base(figure_id, meta["year"], 2013)
    ordered = data.sort_values("ANIO", ascending=False)
    bars = ax.barh(np.arange(len(ordered)), ordered[column], color=TEAL if figure_id == "B.10" else CORAL, height=0.58)
    ax.set_yticks(np.arange(len(ordered)), ordered["ANIO"].astype(str), fontsize=8, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_xlim(0, ordered[column].max() * 1.13)
    for bar, value in zip(bars, ordered[column]):
        ax.text(value + ordered[column].max() * 0.012, bar.get_y() + bar.get_height() / 2, f"{value:,.0f}", va="center", fontsize=8, color=TEXT)
    _footer(fig, f"CRT con datos proporcionados por los operadores de telecomunicaciones a diciembre de {meta['year']}.",
            "Herfindahl-Hirschman (IHH) estimado con respecto al número de líneas o accesos del servicio.")
    output.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def _plot_speed(data: pd.DataFrame, meta: dict, output: Path) -> None:
    figure_id = "B.15"
    fig, ax = _base(figure_id, meta["year"], 2013)
    categories = [column for column in data.columns if column != "ANIO"]
    colors = [LIGHT, TEXT, "#64649A", CORAL, SALMON]
    x = np.arange(len(data))
    bottom = np.zeros(len(data))
    for index, category in enumerate(categories):
        values = data[category].to_numpy(float)
        bars = ax.bar(x, values, bottom=bottom, width=0.58, color=colors[index], label=category)
        for bar, value, base in zip(bars, values, bottom):
            if value >= 3:
                ax.text(bar.get_x() + bar.get_width() / 2, base + value / 2, f"{value:.0f}%", ha="center", va="center", fontsize=6.4,
                        fontweight="bold", color="white" if index in (1, 2, 4) else TEXT)
        bottom += values
    ax.set_ylim(0, 100)
    ax.set_yticks([])
    ax.set_xticks(x, data["ANIO"].astype(str), fontsize=8, fontweight="bold")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.21), ncol=5, frameon=False, fontsize=7.2, labelcolor=TEXT)
    fig.text(0.75, 0.80, f"Total nacional {meta['year']}\n{meta['value']:,.0f}", ha="center", fontsize=16, fontweight="bold", color=TEXT)
    _footer(fig, f"CRT con datos proporcionados por los operadores de telecomunicaciones a diciembre de {meta['year']}.")
    output.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def _plot_technology(data: pd.DataFrame, meta: dict, output: Path) -> None:
    fig = plt.figure(figsize=(18, 10), facecolor="white")
    bg = fig.add_axes([0, 0, 1, 1], zorder=0)
    bg.axis("off")
    colors = [TEXT, TEAL, LIGHT, SALMON, CORAL]
    bg.add_patch(patches.FancyBboxPatch((0.028, 0.943), 0.007, 0.018,
                 boxstyle="round,pad=0,rounding_size=0.002", facecolor=SALMON, edgecolor="none"))
    bg.text(0.045, 0.952, "Figura B.16.", fontsize=13, fontweight="bold", color=TEXT, va="center")
    bg.text(0.124, 0.952, TITLES["B.16"], fontsize=13, color=TEXT, va="center")

    def draw_panel(offset: float, prefix: str, title: str, total: float, growth: float) -> None:
        bg.add_patch(patches.FancyBboxPatch((0.03 + offset, 0.11), 0.44, 0.75,
                     boxstyle="round,pad=0.018", facecolor="white", edgecolor="#D1D1DF", linewidth=1.3))
        bg.add_patch(patches.FancyBboxPatch((0.17 + offset, 0.83), 0.16, 0.055,
                     boxstyle="round,pad=0.012", facecolor="white", edgecolor="#EEEEEE"))
        bg.text(0.25 + offset, 0.857, title, ha="center", va="center", fontsize=15, fontweight="bold", color=TEXT)
        bg.text(0.36 + offset, 0.70, f"Accesos {'residenciales' if prefix == 'residencial' else 'no residenciales'}\na nivel nacional:",
                ha="center", va="center", fontsize=8, color=TEXT)
        bg.text(0.36 + offset, 0.635, f"{total:,.0f}", ha="center", va="center", fontsize=18, fontweight="bold", color=TEXT)
        if not math.isnan(growth):
            bg.text(0.12 + offset, 0.145, f"Tasa de crecimiento\nanual de {growth:.1f}%", ha="center", va="center",
                    fontsize=9, color=TEXT, bbox=dict(boxstyle="round,pad=0.6", facecolor="white", edgecolor="#EEEEEE"))

        pie = fig.add_axes([0.035 + offset, 0.24, 0.25, 0.48], zorder=3)
        values = data[f"{prefix}_pct"].to_numpy(float)
        wedges, _ = pie.pie(values, colors=colors, startangle=90, counterclock=False,
                            wedgeprops={"linewidth": 1.2, "edgecolor": "white"})
        pie.set_aspect("equal")
        for wedge, value in zip(wedges, values):
            if value < 0.5:
                continue
            angle = np.deg2rad((wedge.theta1 + wedge.theta2) / 2)
            x, y = 1.12 * np.cos(angle), 1.12 * np.sin(angle)
            pie.annotate(f"{value:.1f}%", xy=(0.92 * np.cos(angle), 0.92 * np.sin(angle)), xytext=(x, y),
                         ha="left" if x > 0 else "right", va="center", fontsize=9, fontweight="bold", color=TEXT,
                         arrowprops=dict(arrowstyle="-", color="#A0A0B0", lw=0.8),
                         bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#D1D1DF"))

        bar = fig.add_axes([0.31 + offset, 0.22, 0.13, 0.29], zorder=3)
        growths = data[f"{prefix}_crecimiento"].replace([np.inf, -np.inf], np.nan)
        mask = growths.notna() & growths.abs().gt(0.05)
        values_growth = growths.loc[mask].to_numpy(float)
        names = data.loc[mask, "tecnologia"].tolist()
        xpos = np.arange(len(values_growth))
        bar.bar(xpos, values_growth, color=[TEAL if value >= 0 else LIGHT for value in values_growth], width=0.48)
        bar.axhline(0, color="#A0A0B0", linewidth=0.8)
        bar.set_xticks(xpos, [name.replace(" ", "\n") for name in names], fontsize=6.3, color=TEXT)
        bar.set_yticks([])
        for spine in bar.spines.values():
            spine.set_visible(False)
        for xvalue, value in zip(xpos, values_growth):
            bar.text(xvalue, value, f"{value:.1f}%", ha="center", va="bottom" if value >= 0 else "top", fontsize=7, fontweight="bold", color=TEXT)
        bg.text(0.375 + offset, 0.49, f"Tasa de crecimiento anual,\ndic {meta['year'] - 1} - dic {meta['year']}", ha="center", fontsize=8, color=TEXT)

    draw_panel(0.00, "residencial", "Residencial", meta["res_total"], meta["res_growth"])
    draw_panel(0.49, "no_residencial", "No Residencial", meta["nores_total"], meta["nores_growth"])
    fig.legend([patches.Patch(facecolor=color) for color in colors], data["tecnologia"].tolist(),
               loc="lower center", bbox_to_anchor=(0.5, 0.075), ncol=5, frameon=False, fontsize=8, labelcolor=TEXT)
    _footer(fig, f"CRT con datos proporcionados por los operadores de telecomunicaciones a diciembre de {meta['year']}.",
            "Los porcentajes pueden no sumar 100% debido al redondeo.")
    output.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def plot(figure_id: str, data: pd.DataFrame, meta: dict, output: Path, project_root: Path, geojson: Path | None = None) -> None:
    _configure_fonts(project_root)
    if figure_id in {"B.4", "B.5", "B.8", "B.11", "B.12", "B.19", "B.20"}:
        _plot_series(figure_id, data, meta, output)
    elif figure_id in {"B.6", "B.7", "B.13", "B.14"}:
        if geojson is None:
            raise ValueError(f"{figure_id} requiere el mapa de México")
        _plot_map(figure_id, data, meta, geojson, output)
    elif figure_id in {"B.9", "B.17"}:
        _plot_share(figure_id, data, meta, output)
    elif figure_id in {"B.10", "B.18"}:
        _plot_ihh(figure_id, data, meta, output)
    elif figure_id == "B.15":
        _plot_speed(data, meta, output)
    elif figure_id == "B.16":
        _plot_technology(data, meta, output)


def generate_figure(context, figure_id: str):
    """Ejecuta adquisición, cálculo, reporte, texto y PNG para una figura."""
    print(f"  {figure_id} | Reutilización o descarga del ZIP global BIT/CRT")
    bit_path = context.acquire_source(BIT_SOURCE_ID)
    endutih_path = None
    denue_path = None
    geojson_path = None
    if figure_id == "B.13":
        print(f"  {figure_id} | Reutilización o descarga de ENDUTIH 2025")
        endutih_path = context.acquire_source(ENDUTIH_SOURCE_ID)
    if figure_id == "B.14":
        print(f"  {figure_id} | Reutilización del desglose estatal DENUE")
        denue_path = context.acquire_source(DENUE_SOURCE_ID)
    if figure_id in {"B.6", "B.7", "B.13", "B.14"}:
        print(f"  {figure_id} | Reutilización de la geometría estatal")
        geojson_path = context.acquire_source(MAP_SOURCE_ID)

    print(f"  {figure_id} | Lectura selectiva, cálculo y validación")
    data, meta = calculate(figure_id, bit_path, endutih_path, denue_path)
    period = f"{meta['year']}-{meta['month']:02d}"
    context.record_source_period(BIT_SOURCE_ID, period, "ULTIMO_DISPONIBLE")
    if figure_id == "B.13":
        context.record_source_period(ENDUTIH_SOURCE_ID, "2025", "AL_DIA")
    if figure_id == "B.14":
        context.record_source_period(DENUE_SOURCE_ID, "2023-11", "ULTIMO_LOCAL_DISPONIBLE")
    if geojson_path is not None:
        context.record_source_period(MAP_SOURCE_ID, "sin versión declarada", "REFERENCIA_VISUAL")
    context.write_data_used(data)

    if figure_id in {"B.6", "B.7", "B.13", "B.14"}:
        for row in data.itertuples(index=False):
            inputs = {"entidad": row.ENTIDAD, "periodo_bit": period}
            if hasattr(row, "A_RESIDENCIAL_E"):
                inputs.update({"numerador": row.A_RESIDENCIAL_E, "denominador": row.FAC_HOG})
            elif hasattr(row, "A_NO_RESIDENCIAL_E"):
                inputs.update({"numerador": row.A_NO_RESIDENCIAL_E, "denominador": row.UNIDADES})
            context.record_calculation(f"valor_{int(row.K_ENTIDAD):02d}", "indicador estatal conforme a la fuente y denominador declarados", inputs, round(float(row.valor), 4), "por cada 100", 0)
    context.record_calculation(
        "valor_ultimo_periodo", "selección del último diciembre disponible y aplicación de la fórmula de la figura",
        {"periodo": period, "filas": len(data)}, round(float(meta["value"]), 4), "valor de la figura", 2,
    )

    summary = f"En {meta['year']}, el valor más reciente del indicador fue {meta['value']:,.1f}."
    if "leader" in meta:
        summary = f"En {meta['year']}, {meta['leader']} registró la mayor participación, con {meta['value']:.1f}%."
    text_path = context.render_text("b_4_b_20.md.j2", {"figure_id": figure_id, "title": TITLES[figure_id], "summary": summary})
    print(f"  {figure_id} | Generación de gráfica PNG")
    plot(figure_id, data, meta, context.expected_figure_path, context.project_root, geojson_path)
    return {
        "figure_path": str(context.expected_figure_path), "text_path": str(text_path),
        "source_latest_period": period, "rows_used": len(data), "latest_value": round(float(meta["value"]), 4),
    }

FIGURE_ID = "B.20"


def generate(context):
    """Ejecuta el flujo completo; la caché evita descargas repetidas."""
    return generate_figure(context, FIGURE_ID)


def main() -> int:
    import sys

    project_root = Path(__file__).resolve().parents[2]
    src = project_root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from anuario2026.pipeline import run_pipeline

    run_pipeline(project_root, only=FIGURE_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())