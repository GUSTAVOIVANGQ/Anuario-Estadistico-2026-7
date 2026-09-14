"""Figura B.22: accesos no residenciales de TV restringida por cada 100 unidades.

Flujo completo y autónomo: reutiliza o descarga BIT, consulta el catálogo oficial
de descarga masiva del DENUE, conserva los ZIP crudos, cuenta los establecimientos,
calcula los indicadores, registra la auditoría y genera el mapa PNG.
"""

from __future__ import annotations

import base64
import json
import math
import re
import sys
import unicodedata
import urllib.request
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path, PurePosixPath

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PatchCollection


FIGURE_ID = "B.22"
BIT_SOURCE_ID = "crt_bit_todo_2025_q2"
DENUE_SOURCE_ID = "inegi_denue_2026_05"
MAP_SOURCE_ID = "mexico_geojson_legacy"
BIT_TABLE = "TD_ACC_TVRES_ITE_VA.csv"
BIT_VALUE_COLUMNS = ("A_NO_RESIDENCIAL_E", "A_COMERCIAL_E", "A_NO_RESIDENCIAL")

DENUE_PORTAL = "https://www.inegi.org.mx/app/descarga/?ti=6"
DENUE_API = (
    "https://www.inegi.org.mx/app/api/descarga/descarga/descargamasiva/"
    "lista/obtenerarchivos"
)
DENUE_CONTENT_ROOT = "https://www.inegi.org.mx/contenidos"
DENUE_FOLDER = "Otros|DENUE|Actividad económica|"

ENTITIES = {
    1: "Aguascalientes", 2: "Baja California", 3: "Baja California Sur",
    4: "Campeche", 5: "Coahuila de Zaragoza", 6: "Colima", 7: "Chiapas",
    8: "Chihuahua", 9: "Ciudad de México", 10: "Durango", 11: "Guanajuato",
    12: "Guerrero", 13: "Hidalgo", 14: "Jalisco", 15: "México",
    16: "Michoacán de Ocampo", 17: "Morelos", 18: "Nayarit",
    19: "Nuevo León", 20: "Oaxaca", 21: "Puebla", 22: "Querétaro",
    23: "Quintana Roo", 24: "San Luis Potosí", 25: "Sinaloa", 26: "Sonora",
    27: "Tabasco", 28: "Tamaulipas", 29: "Tlaxcala",
    30: "Veracruz de Ignacio de la Llave", 31: "Yucatán", 32: "Zacatecas",
}

COLORS = ["#ADDCDF", "#317DA3", "#4B4B83", "#F58F82", "#F2535A"]
LABELS = ["Menos de 4", "4 a 6", "7 a 9", "10 a 12", "Más de 13"]
BREAKS = [0, 4, 7, 10, 13, math.inf]
TEXT = "#4B4B83"
CREAM = "#FBFBF7"

MONTHS = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo",
    6: "junio", 7: "julio", 8: "agosto", 9: "septiembre",
    10: "octubre", 11: "noviembre", 12: "diciembre",
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


def _round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype("string").str.strip().str.replace(",", "", regex=False),
        errors="coerce",
    )


def _zip_member(archive: zipfile.ZipFile, filename: str) -> str:
    for name in archive.namelist():
        if PurePosixPath(name.replace("\\", "/")).name.casefold() == filename.casefold():
            return name
    raise ValueError(f"El ZIP BIT no contiene la tabla requerida: {filename}")


def load_bit_table(raw_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(raw_path) as archive:
        member = _zip_member(archive, BIT_TABLE)
        with archive.open(member) as stream:
            header = pd.read_csv(stream, nrows=0, encoding="latin-1")
        value_column = next(
            (column for column in BIT_VALUE_COLUMNS if column in header.columns), None
        )
        if value_column is None:
            raise ValueError(
                f"{BIT_TABLE} no contiene ninguna columna de accesos no residenciales: "
                f"{', '.join(BIT_VALUE_COLUMNS)}"
            )
        with archive.open(member) as stream:
            frame = pd.read_csv(
                stream,
                usecols=["K_ENTIDAD", "ANIO", "MES", value_column],
                encoding="latin-1",
                low_memory=False,
            )
    return frame.rename(columns={value_column: "accesos_no_residenciales"})


def _period_key(value: str) -> tuple[int, int] | None:
    match = re.search(r"(\d{1,2})/(\d{4})", value or "")
    return (int(match.group(2)), int(match.group(1))) if match else None


def discover_latest_denue_files() -> tuple[str, list[dict[str, str]]]:
    """Consulta el catálogo oficial y devuelve los ZIP CSV del último DENUE."""
    payload = {
        "tinfo": "6", "ag": "0", "prog": "0", "cc": "0", "subtema": "0",
        "anio": "0", "formato": "0", "datosAbiertos": "3",
        "titulo": base64.b64encode(DENUE_FOLDER.encode("utf-8")).decode("ascii"),
        "textoBuscar": "", "ingles": "0", "tipoInfo": "OTROS",
    }
    request = urllib.request.Request(
        DENUE_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "AnuarioEstadistico2026/0.14",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        rows = json.loads(response.read().decode("utf-8-sig"))
    available = [(_period_key(str(row.get("anioInfo", ""))), row) for row in rows]
    available = [(period, row) for period, row in available if period is not None]
    if not available:
        raise RuntimeError("El catálogo INEGI no devolvió ediciones DENUE con periodo válido")
    latest = max(period for period, _ in available)
    records: list[dict[str, str]] = []
    for period, row in available:
        if period != latest:
            continue
        formats = [item for item in str(row.get("formatos", "")).split("|") if item]
        extensions = [item for item in str(row.get("extensiones", "")).split("|") if item]
        if "csv" not in formats:
            continue
        index = formats.index("csv")
        if index >= len(extensions):
            continue
        suffix = extensions[index].split("&", 1)[0]
        relative = str(row["pathLogico"]) + suffix
        url = DENUE_CONTENT_ROOT + relative
        records.append({
            "title": str(row["titulo"]).rsplit("|", 1)[-1],
            "url": url,
            "filename": PurePosixPath(relative).name,
        })
    if len(records) < 20:
        raise RuntimeError(
            f"La edición DENUE más reciente sólo devolvió {len(records)} ZIP CSV; "
            "se esperaba el conjunto nacional por actividad"
        )
    period_text = f"{latest[1]:02d}/{latest[0]}"
    return period_text, sorted(records, key=lambda item: item["filename"])


def _valid_zip(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 100:
        return False
    try:
        with zipfile.ZipFile(path) as archive:
            return bool(archive.namelist())
    except zipfile.BadZipFile:
        return False


def _download(url: str, destination: Path, position: int, total_files: int) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if _valid_zip(destination):
        print(f"  DENUE {position:02d}/{total_files:02d} | reutiliza {destination.name}")
        return "REUTILIZADO"
    partial = destination.with_suffix(destination.suffix + ".part")
    partial.unlink(missing_ok=True)
    request = urllib.request.Request(
        url, headers={"User-Agent": "AnuarioEstadistico2026/0.14"}
    )
    print(f"  DENUE {position:02d}/{total_files:02d} | descarga {destination.name}")
    with urllib.request.urlopen(request, timeout=180) as response, partial.open("wb") as stream:
        expected = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        last_step = -1
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            stream.write(block)
            downloaded += len(block)
            step = int(downloaded * 10 / expected) if expected else 0
            if expected and step != last_step:
                print(f"      {min(step * 10, 100):3d}% ({downloaded:,}/{expected:,} bytes)")
                last_step = step
    if not _valid_zip(partial):
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"INEGI devolvió un ZIP inválido o vacío: {url}")
    partial.replace(destination)
    return "DESCARGADO_Y_VERIFICADO"


def acquire_denue_collection(
    project_root: Path,
    manual_files: tuple[Path, ...] = (),
) -> tuple[str, list[Path], list[dict[str, str]]]:
    """Usa manuales si existen; de lo contrario descarga la colección oficial."""
    usable_manual = [
        path for path in manual_files if path.suffix.casefold() in {".csv", ".zip"}
    ]
    if usable_manual:
        return "05/2026", usable_manual, [
            {"title": path.name, "url": DENUE_PORTAL, "filename": path.name,
             "cache_status": "INSUMO_MANUAL_VERIFICADO"}
            for path in usable_manual
        ]

    period, records = discover_latest_denue_files()
    cache = project_root / "data" / "raw" / DENUE_SOURCE_ID / period.replace("/", "_")
    paths: list[Path] = []
    for position, record in enumerate(records, 1):
        path = cache / record["filename"]
        record["cache_status"] = _download(record["url"], path, position, len(records))
        paths.append(path)
    return period, paths, records


def _dataset_csv_members(archive: zipfile.ZipFile) -> list[str]:
    csvs = [
        name for name in archive.namelist()
        if not name.endswith("/") and name.casefold().endswith(".csv")
    ]
    datasets = [name for name in csvs if "conjunto_de_datos" in name.casefold()]
    if datasets:
        return datasets
    return [
        name for name in csvs
        if "diccionario" not in name.casefold() and "metadato" not in name.casefold()
    ]


def _state_column(columns: list[str]) -> str:
    normalized = {str(column).strip().casefold(): str(column) for column in columns}
    for candidate in ("cve_ent", "cveent", "entidad", "nom_ent"):
        if candidate in normalized:
            return normalized[candidate]
    raise ValueError(f"El archivo DENUE no contiene columna de entidad: {columns}")


def _count_csv_stream(stream) -> dict[int, int]:
    header = pd.read_csv(stream, nrows=0, encoding="latin-1")
    state_column = _state_column(list(header.columns))
    stream.seek(0)
    counts: dict[int, int] = {}
    for chunk in pd.read_csv(
        stream,
        usecols=[state_column],
        dtype={state_column: "string"},
        encoding="latin-1",
        chunksize=250_000,
        low_memory=False,
    ):
        values = chunk[state_column].astype("string").str.extract(r"(\d{1,2})", expand=False)
        codes = pd.to_numeric(values, errors="coerce")
        frequencies = codes.loc[codes.between(1, 32)].astype(int).value_counts()
        for code, frequency in frequencies.items():
            counts[int(code)] = counts.get(int(code), 0) + int(frequency)
    return counts


def count_denue_units(paths: list[Path]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for position, path in enumerate(paths, 1):
        print(f"  DENUE {position:02d}/{len(paths):02d} | cuenta establecimientos en {path.name}")
        if path.suffix.casefold() == ".csv":
            with path.open("rb") as stream:
                partial = _count_csv_stream(stream)
        elif path.suffix.casefold() == ".zip":
            partial: dict[int, int] = {}
            with zipfile.ZipFile(path) as archive:
                members = _dataset_csv_members(archive)
                if not members:
                    raise ValueError(f"El ZIP DENUE no contiene CSV de datos: {path}")
                for member in members:
                    with archive.open(member) as stream:
                        member_counts = _count_csv_stream(stream)
                    for code, frequency in member_counts.items():
                        partial[code] = partial.get(code, 0) + frequency
        else:
            raise ValueError(f"Formato DENUE no admitido: {path}")
        for code, frequency in partial.items():
            counts[code] = counts.get(code, 0) + frequency
    missing = sorted(set(ENTITIES) - set(counts))
    if missing:
        raise ValueError(f"DENUE no produjo las 32 entidades; faltan {missing}")
    return counts


def build_metrics(
    bit: pd.DataFrame,
    units_by_entity: dict[int, int],
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    accesses = bit.copy()
    for column in ("K_ENTIDAD", "ANIO", "MES", "accesos_no_residenciales"):
        accesses[column] = _numeric(accesses[column])
    accesses = accesses.loc[
        accesses["K_ENTIDAD"].between(1, 32)
        & accesses["ANIO"].notna()
        & accesses["MES"].between(1, 12)
        & accesses["accesos_no_residenciales"].notna()
    ].copy()
    periods = accesses[["ANIO", "MES"]].drop_duplicates().sort_values(["ANIO", "MES"])
    if periods.empty:
        raise ValueError("BIT no contiene un periodo válido de accesos no residenciales")
    year = int(periods.iloc[-1]["ANIO"])
    month = int(periods.iloc[-1]["MES"])
    latest = accesses.loc[accesses["ANIO"].eq(year) & accesses["MES"].eq(month)]
    grouped = (
        latest.groupby("K_ENTIDAD", as_index=False)["accesos_no_residenciales"]
        .sum(min_count=1)
    )
    grouped["K_ENTIDAD"] = grouped["K_ENTIDAD"].astype(int)
    units = pd.DataFrame({
        "K_ENTIDAD": list(units_by_entity),
        "unidades_economicas": list(units_by_entity.values()),
    })
    data = grouped.merge(units, on="K_ENTIDAD", how="outer", validate="one_to_one")
    if len(data) != 32 or data[["accesos_no_residenciales", "unidades_economicas"]].isna().any().any():
        missing = sorted(set(ENTITIES) - set(data.dropna()["K_ENTIDAD"].astype(int)))
        raise ValueError(f"No fue posible calcular las 32 entidades; faltan {missing}")
    data["entidad"] = data["K_ENTIDAD"].map(ENTITIES)
    data["penetracion"] = (
        data["accesos_no_residenciales"] / data["unidades_economicas"] * 100
    )
    data["penetracion_grafica"] = data["penetracion"].map(_round_half_up)
    data.insert(0, "anio_bit", year)
    data.insert(1, "mes_bit", month)
    data = data.sort_values("K_ENTIDAD").reset_index(drop=True)

    current_total = float(data["accesos_no_residenciales"].sum())
    unit_total = int(data["unidades_economicas"].sum())
    previous_total = float(
        accesses.loc[
            accesses["ANIO"].eq(year - 1) & accesses["MES"].eq(month),
            "accesos_no_residenciales",
        ].sum()
    )
    growth = (current_total / previous_total - 1) * 100 if previous_total > 0 else math.nan
    national = current_total / unit_total * 100
    metadata: dict[str, float | int] = {
        "anio_bit": year,
        "mes_bit": month,
        "accesos_nacionales": round(current_total),
        "unidades_nacionales": unit_total,
        "penetracion_nacional": national,
        "penetracion_nacional_grafica": _round_half_up(national),
        "accesos_previos": round(previous_total),
        "crecimiento_anual": growth,
    }
    return data, metadata


def _class_color(value: int) -> str:
    for lower, upper, color in zip(BREAKS[:-1], BREAKS[1:], COLORS):
        if lower <= value < upper:
            return color
    return COLORS[-1]


def _entity_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    plain = "".join(c for c in decomposed if not unicodedata.combining(c))
    return plain.casefold()


def _geo_patches(geojson_path: Path, values: dict[str, int]):
    payload = json.loads(geojson_path.read_text(encoding="utf-8"))
    canonical = {_entity_key(name): name for name in values}
    canonical.update({
        "coahuila": "Coahuila de Zaragoza",
        "michoacan": "Michoacán de Ocampo",
        "veracruz": "Veracruz de Ignacio de la Llave",
    })
    shapes: list[patches.Polygon] = []
    facecolors: list[str] = []
    found: set[str] = set()
    for feature in payload.get("features", []):
        raw_name = str(feature.get("properties", {}).get("name", "")).strip()
        name = canonical.get(_entity_key(raw_name), raw_name)
        if name not in values:
            continue
        found.add(name)
        geometry = feature.get("geometry", {})
        coordinates = geometry.get("coordinates", [])
        polygons = [coordinates] if geometry.get("type") == "Polygon" else coordinates
        for polygon in polygons:
            if polygon:
                shapes.append(patches.Polygon(np.asarray(polygon[0], dtype=float), closed=True))
                facecolors.append(_class_color(values[name]))
    missing = sorted(set(values) - found)
    if missing:
        raise ValueError(f"El mapa no contiene las entidades {missing}")
    return shapes, facecolors


def _plot(
    data: pd.DataFrame,
    metadata: dict[str, float | int],
    denue_period: str,
    geojson_path: Path,
    output_path: Path,
    project_root: Path,
) -> None:
    _configure_fonts(project_root)
    fig = plt.figure(figsize=(16, 8.5), facecolor="white")
    fig.add_artist(patches.FancyBboxPatch(
        (0.035, 0.055), 0.93, 0.86,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=0, facecolor=CREAM, transform=fig.transFigure, zorder=0,
    ))
    fig.text(0.055, 0.875, " ", fontsize=2, va="center",
             bbox=dict(boxstyle="round,pad=1.5,rounding_size=0.2",
                       facecolor="#F58F82", edgecolor="none"))
    fig.text(0.071, 0.875, "Figura B.22.", fontsize=14, fontweight="bold",
             color=TEXT, va="center")
    fig.text(
        0.161, 0.875,
        "Accesos del Servicio de Televisión Restringida No Residencial por cada "
        "100 unidades económicas por entidad federativa",
        fontsize=13.3, fontweight="medium", color=TEXT, va="center",
    )

    map_ax = fig.add_axes([0.20, 0.15, 0.60, 0.68])
    map_ax.axis("off")
    values = data.set_index("entidad")["penetracion_grafica"].astype(int).to_dict()
    state_patches, facecolors = _geo_patches(geojson_path, values)
    map_ax.add_collection(PatchCollection(
        state_patches, facecolor=facecolors, edgecolor=TEXT, linewidth=0.65
    ))
    map_ax.set_xlim(-119.5, -85.0)
    map_ax.set_ylim(14.0, 33.3)
    map_ax.set_aspect(1 / np.cos(np.deg2rad(23.5)))

    legend_handles = [
        patches.FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.2",
                               facecolor=color, edgecolor="none", label=label)
        for color, label in zip(COLORS, LABELS)
    ]
    legend = map_ax.legend(
        handles=legend_handles, loc="lower left", bbox_to_anchor=(0.075, 0.17),
        bbox_transform=fig.transFigure, frameon=False, fontsize=11,
        labelcolor=TEXT, handlelength=2.8, handleheight=1.4, labelspacing=0.8,
    )
    for item in legend.get_texts():
        item.set_fontweight("bold")

    bx, by, bw, bh = 0.70, 0.59, 0.22, 0.20
    fig.add_artist(patches.FancyBboxPatch(
        (bx, by), bw, bh, boxstyle="round,pad=0.015,rounding_size=0.03",
        linewidth=0, facecolor="white", transform=fig.transFigure, zorder=6,
    ))
    fig.add_artist(patches.Polygon(
        [[bx + 0.07, by + 0.005], [bx + 0.11, by + 0.005], [bx + 0.11, by - 0.035]],
        closed=True, facecolor="white", edgecolor="none",
        transform=fig.transFigure, zorder=5,
    ))
    fig.text(
        bx + bw / 2, by + bh * 0.69,
        "Accesos del servicio de televisión\nrestringida No Residencial por cada\n"
        "100 unidades económicas:",
        fontsize=10.5, color=TEXT, ha="center", va="center", zorder=7,
    )
    fig.text(
        bx + bw / 2, by + bh * 0.22,
        str(int(metadata["penetracion_nacional_grafica"])),
        fontsize=34, fontweight="bold", color=TEXT, ha="center", va="center", zorder=7,
    )

    growth = float(metadata["crecimiento_anual"])
    gx, gy, gw, gh = 0.43, 0.10, 0.22, 0.105
    fig.add_artist(patches.FancyBboxPatch(
        (gx, gy), gw, gh, boxstyle="round,pad=0.012,rounding_size=0.02",
        linewidth=0, facecolor="white", transform=fig.transFigure, zorder=6,
    ))
    icon = patches.FancyBboxPatch(
        (gx + 0.008, gy + 0.008), 0.06, gh - 0.016,
        boxstyle="round,pad=0.005,rounding_size=0.015",
        linewidth=0, facecolor=TEXT, transform=fig.transFigure, zorder=7,
    )
    fig.add_artist(icon)
    line_x = [gx + 0.018, gx + 0.018, gx + 0.031, gx + 0.041, gx + 0.055]
    line_y = [gy + 0.032, gy + 0.070, gy + 0.046, gy + 0.067, gy + 0.052]
    fig.add_artist(plt.Line2D(line_x, line_y, color="white", linewidth=1.7,
                             transform=fig.transFigure, zorder=8))
    fig.add_artist(patches.FancyArrowPatch(
        (gx + 0.055, gy + 0.052), (gx + 0.063, gy + 0.075),
        arrowstyle="-|>", mutation_scale=8, color="white", linewidth=1.4,
        transform=fig.transFigure, zorder=8,
    ))
    growth_text = "N/D" if math.isnan(growth) else f"{growth:.1f}%"
    fig.text(gx + 0.145, gy + gh * 0.65, "Tasa de crecimiento",
             fontsize=10.5, color=TEXT, ha="center", va="center", zorder=8)
    fig.text(gx + 0.145, gy + gh * 0.37, f"anual de {growth_text}",
             fontsize=11, fontweight="bold", color=TEXT,
             ha="center", va="center", zorder=8)

    month = MONTHS[int(metadata["mes_bit"])]
    denue_month, denue_year = denue_period.split("/")
    fig.text(0.055, 0.072, "Fuente:", fontsize=8, fontweight="bold", color=TEXT)
    fig.text(
        0.096, 0.072,
        f"CRT con datos de los operadores de telecomunicaciones a {month} de "
        f"{int(metadata['anio_bit'])} y del DENUE del INEGI, a "
        f"{MONTHS[int(denue_month)]} de {denue_year}.",
        fontsize=8, fontweight="normal", color=TEXT,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  B.22 | Adquisición o reutilización de TODO.zip de BIT/CRT")
    bit_path = context.acquire_source(BIT_SOURCE_ID)
    print("  B.22 | Consulta del catálogo y adquisición de DENUE")
    denue_period, denue_paths, denue_records = acquire_denue_collection(
        context.project_root, context.manual_files
    )
    manual_set = {path.resolve() for path in context.manual_files}
    if not manual_set:
        for path, record in zip(denue_paths, denue_records):
            context.register_raw_source(
                f"{DENUE_SOURCE_ID}:{path.stem}", path,
                owner="INEGI", title=f"DENUE {denue_period}: {record['title']}",
                expected_period=denue_period, detected_period=denue_period,
                landing_page=DENUE_PORTAL, exact_url=record["url"],
                cache_status=record["cache_status"],
                downloaded_at=datetime.fromtimestamp(
                    path.stat().st_mtime, tz=timezone.utc
                ).isoformat(timespec="seconds"),
                content_type="application/zip",
            )
    print("  B.22 | Reutilización de la geometría estatal de México")
    geojson_path = context.acquire_source(MAP_SOURCE_ID)

    print("  B.22 | Lectura de accesos BIT y conteo de establecimientos DENUE")
    units = count_denue_units(denue_paths)
    data, metadata = build_metrics(load_bit_table(bit_path), units)
    bit_period = f"{int(metadata['anio_bit'])}-{int(metadata['mes_bit']):02d}"
    context.record_source_period(BIT_SOURCE_ID, bit_period, "ULTIMO_DISPONIBLE")
    context.record_source_period(MAP_SOURCE_ID, "sin versión declarada", "REFERENCIA_VISUAL")
    context.write_data_used(data)

    for row in data.itertuples(index=False):
        context.record_calculation(
            f"penetracion_{row.K_ENTIDAD:02d}",
            "accesos no residenciales BIT / establecimientos crudos DENUE * 100",
            {
                "entidad": row.entidad, "periodo_bit": bit_period,
                "periodo_denue": denue_period,
                "accesos": row.accesos_no_residenciales,
                "unidades_economicas": row.unidades_economicas,
            },
            row.penetracion, "accesos por cada 100 unidades económicas", 0,
        )
    context.record_calculation(
        "penetracion_nacional",
        "suma(accesos no residenciales BIT) / suma(establecimientos DENUE) * 100",
        {
            "periodo_bit": bit_period, "periodo_denue": denue_period,
            "accesos": metadata["accesos_nacionales"],
            "unidades_economicas": metadata["unidades_nacionales"],
        },
        metadata["penetracion_nacional"],
        "accesos por cada 100 unidades económicas", 0,
    )
    context.record_calculation(
        "crecimiento_anual_accesos",
        "(accesos del último corte / accesos del mismo mes del año previo - 1) * 100",
        {
            "periodo_actual": bit_period,
            "accesos_actuales": metadata["accesos_nacionales"],
            "accesos_previos": metadata["accesos_previos"],
        },
        metadata["crecimiento_anual"], "%", 1,
    )

    ranked = data.sort_values("penetracion", ascending=False)
    highest = ranked.head(3).to_dict("records")
    lowest = ranked.tail(2).sort_values("penetracion").to_dict("records")
    text_path = context.render_text("b_22.md.j2", {
        "anio_bit": int(metadata["anio_bit"]),
        "mes_bit": int(metadata["mes_bit"]),
        "periodo_denue": denue_period,
        "penetracion_nacional": float(metadata["penetracion_nacional"]),
        "crecimiento_anual": float(metadata["crecimiento_anual"]),
        "mayor_1": highest[0], "mayor_2": highest[1], "mayor_3": highest[2],
        "menor_1": lowest[0], "menor_2": lowest[1],
    })
    print("  B.22 | Generación del mapa PNG")
    _plot(
        data, metadata, denue_period, geojson_path,
        context.expected_figure_path, context.project_root,
    )
    return {
        "figure_path": str(context.expected_figure_path),
        "text_path": str(text_path),
        "source_latest_period": f"BIT {bit_period}; DENUE {denue_period}",
        "rows_used": len(data),
        "denue_establishments": int(metadata["unidades_nacionales"]),
        "denue_files": len(denue_paths),
    }


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
