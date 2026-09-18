"""Figura B.21: accesos residenciales de TV restringida por cada 100 hogares.

El script contiene el flujo completo: reutiliza o descarga los ZIP oficiales,
lee las tablas crudas, detecta el último corte BIT, calcula los indicadores,
registra la auditoría y genera la gráfica PNG.
"""

from __future__ import annotations

import json
import sys
import unicodedata
import zipfile
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


FIGURE_ID = "B.21"
BIT_SOURCE_ID = "crt_bit_todo_2025_q2"
ENDUTIH_SOURCE_ID = "inegi_endutih_2025"
MAP_SOURCE_ID = "mexico_geojson_legacy"
ENDUTIH_YEAR = 2025
BIT_TABLE = "TD_ACC_TVRES_ITE_VA.csv"
HOUSEHOLDS_TABLE = f"tr_endutih_hogares_anual_{ENDUTIH_YEAR}.csv"

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

COLORS = ["#afafaf", "#737f7c", "#63918b", "#2d4f4b", "#012f2a"]
LABELS = ["Menos de 55", "56-65", "66-75", "76-85", "Más de 85"]
COLOR_TEXT = "#3c3c3b"

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


def _zip_member(archive: zipfile.ZipFile, filename: str) -> str:
    for name in archive.namelist():
        candidate = PurePosixPath(name.replace("\\", "/")).name
        if candidate.casefold() == filename.casefold():
            return name
    raise ValueError(f"El ZIP no contiene la tabla requerida: {filename}")


def load_bit_table(raw_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(raw_path) as archive:
        with archive.open(_zip_member(archive, BIT_TABLE)) as stream:
            frame = pd.read_csv(
                stream,
                usecols=["K_ENTIDAD", "ANIO", "MES", "A_RESIDENCIAL_E"],
                encoding="latin-1",
                low_memory=False,
            )
    return frame


def load_households(raw_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(raw_path) as archive:
        with archive.open(_zip_member(archive, HOUSEHOLDS_TABLE)) as stream:
            header = pd.read_csv(stream, nrows=0)
        entity_column = "CVE_ENT" if "CVE_ENT" in header.columns else "ENT"
        with archive.open(_zip_member(archive, HOUSEHOLDS_TABLE)) as stream:
            frame = pd.read_csv(
                stream,
                usecols=[entity_column, "FAC_HOG"],
                dtype=str,
                low_memory=False,
            )
    return frame.rename(columns={entity_column: "K_ENTIDAD"})


def _round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def build_metrics(
    bit: pd.DataFrame,
    households: pd.DataFrame,
    *,
    maximum_bit_year: int = ENDUTIH_YEAR,
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    """Selecciona el último corte BIT y calcula accesos por cada 100 hogares."""
    accesses = bit.copy()
    for column in ("K_ENTIDAD", "ANIO", "MES", "A_RESIDENCIAL_E"):
        accesses[column] = pd.to_numeric(accesses[column], errors="coerce")
    accesses = accesses.loc[
        accesses["K_ENTIDAD"].between(1, 32)
        & accesses["ANIO"].le(maximum_bit_year)
        & accesses["A_RESIDENCIAL_E"].notna()
    ].copy()
    periods = accesses[["ANIO", "MES"]].dropna().drop_duplicates()
    if periods.empty:
        raise ValueError("BIT no contiene un periodo válido de accesos residenciales")
    periods = periods.sort_values(["ANIO", "MES"])
    bit_year = int(periods.iloc[-1]["ANIO"])
    bit_month = int(periods.iloc[-1]["MES"])
    latest = accesses.loc[
        accesses["ANIO"].eq(bit_year) & accesses["MES"].eq(bit_month)
    ]
    by_entity = (
        latest.groupby("K_ENTIDAD", as_index=False)["A_RESIDENCIAL_E"]
        .sum(min_count=1)
        .rename(columns={"A_RESIDENCIAL_E": "accesos_residenciales"})
    )

    homes = households.copy()
    homes["K_ENTIDAD"] = pd.to_numeric(homes["K_ENTIDAD"], errors="coerce")
    homes["FAC_HOG"] = pd.to_numeric(homes["FAC_HOG"], errors="coerce")
    homes = homes.loc[homes["K_ENTIDAD"].between(1, 32) & homes["FAC_HOG"].gt(0)]
    homes = (
        homes.groupby("K_ENTIDAD", as_index=False)["FAC_HOG"]
        .sum(min_count=1)
        .rename(columns={"FAC_HOG": "hogares_expandidos"})
    )

    data = by_entity.merge(homes, on="K_ENTIDAD", how="outer", validate="one_to_one")
    if len(data) != 32 or data[["accesos_residenciales", "hogares_expandidos"]].isna().any().any():
        missing = sorted(set(ENTITIES) - set(data.dropna()["K_ENTIDAD"].astype(int)))
        raise ValueError(f"No fue posible calcular las 32 entidades; faltan {missing}")
    data["K_ENTIDAD"] = data["K_ENTIDAD"].astype(int)
    data["entidad"] = data["K_ENTIDAD"].map(ENTITIES)
    data["penetracion"] = data["accesos_residenciales"] / data["hogares_expandidos"] * 100
    data["penetracion_grafica"] = data["penetracion"].map(_round_half_up)
    data.insert(0, "anio_bit", bit_year)
    data.insert(1, "mes_bit", bit_month)
    data.insert(2, "anio_endutih", ENDUTIH_YEAR)
    data = data.sort_values("K_ENTIDAD").reset_index(drop=True)

    total_accesses = float(data["accesos_residenciales"].sum())
    total_homes = float(data["hogares_expandidos"].sum())
    national = total_accesses / total_homes * 100
    metadata: dict[str, float | int] = {
        "anio_bit": bit_year,
        "mes_bit": bit_month,
        "anio_endutih": ENDUTIH_YEAR,
        "accesos_nacionales": round(total_accesses),
        "hogares_nacionales": round(total_homes),
        "penetracion_nacional": national,
        "penetracion_nacional_grafica": _round_half_up(national),
    }
    return data, metadata


def _class_color(value: int) -> str:
    if value < 55:
        return COLORS[0]
    if value <= 65:
        return COLORS[1]
    if value <= 75:
        return COLORS[2]
    if value <= 85:
        return COLORS[3]
    return COLORS[4]


def _entity_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    plain = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
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
            if not polygon:
                continue
            outer_ring = np.asarray(polygon[0], dtype=float)
            shapes.append(patches.Polygon(outer_ring, closed=True))
            facecolors.append(_class_color(values[name]))
    missing = sorted(set(values) - found)
    if missing:
        raise ValueError(f"El mapa no contiene las entidades {missing}")
    return shapes, facecolors


def _draw_home_tv(fig: plt.Figure) -> None:
    """Recrea con formas simples la ilustración de vivienda del referente."""
    icon = fig.add_axes([0.73, 0.19, 0.23, 0.27], zorder=5)
    icon.set_xlim(0, 10)
    icon.set_ylim(0, 7)
    icon.axis("off")
    icon.add_patch(patches.Rectangle((0.5, 0.5), 7.9, 5.2, facecolor="#86adae",
                                     edgecolor=COLOR_TEXT, linewidth=3))
    icon.add_patch(patches.Rectangle((1.0, 0.65), 6.9, 0.18, facecolor=COLOR_TEXT,
                                     edgecolor="none"))
    icon.add_patch(patches.Rectangle((2.6, 0.8), 3.8, 3.8, facecolor="#4a7d75",
                                     edgecolor="none"))
    icon.add_patch(patches.Polygon([[2.15, 4.55], [4.5, 6.7], [6.85, 4.55]],
                                   facecolor="#4a7d75", edgecolor=COLOR_TEXT, linewidth=3))
    icon.add_patch(patches.Rectangle((3.7, 0.8), 1.6, 2.25, facecolor="#335a5c",
                                     edgecolor=COLOR_TEXT, linewidth=2))
    for x in (2.9, 5.35):
        icon.add_patch(patches.Rectangle((x, 3.1), 0.85, 0.85, facecolor="white",
                                         edgecolor="#86adae", linewidth=2))
    icon.add_patch(patches.Rectangle((8.9, 0.3), 0.85, 3.7, facecolor=COLOR_TEXT,
                                     edgecolor="none"))
    for y, color in ((3.6, "#3b6667"), (3.15, "#335a5c"), (2.7, "#335a5c")):
        icon.add_patch(patches.Circle((9.32, y), 0.12, facecolor=color, edgecolor="none"))
    icon.plot([0.9, 0.9], [0.15, 0.5], color=COLOR_TEXT, linewidth=3)
    icon.plot([8.0, 8.0], [0.15, 0.5], color=COLOR_TEXT, linewidth=3)


def _plot(
    data: pd.DataFrame,
    metadata: dict[str, float | int],
    geojson_path: Path,
    output_path: Path,
    project_root: Path,
) -> None:
    _configure_fonts(project_root)
    fig, map_ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    map_ax.set_facecolor("white")
    map_ax.axis("off")

    values = data.set_index("entidad")["penetracion_grafica"].astype(int).to_dict()
    state_patches, facecolors = _geo_patches(geojson_path, values)
    map_ax.add_collection(PatchCollection(
        state_patches, facecolor=facecolors, edgecolor="white", linewidth=0.5
    ))
    map_ax.set_xlim(-120.5, -79.0)
    map_ax.set_ylim(13.5, 34.0)
    map_ax.set_aspect(1 / np.cos(np.deg2rad(23.5)))

    bx, by, bw, bh = 0.735, 0.56, 0.215, 0.275
    bubble_face, bubble_edge = "#f7f7f7", "#c0c0c0"
    fig.add_artist(patches.FancyBboxPatch(
        (bx, by), bw, bh, boxstyle="round,pad=0.015,rounding_size=0.015",
        linewidth=1.0, edgecolor=bubble_edge, facecolor=bubble_face,
        transform=fig.transFigure, zorder=6, clip_on=False,
    ))
    fig.text(
        bx + bw / 2, by + bh * 0.80,
        "Accesos del servicio de televisión\nrestringida residencial por cada\n100 hogares:",
        transform=fig.transFigure, fontsize=9.5, color=COLOR_TEXT,
        ha="center", va="center", zorder=7, multialignment="center", clip_on=False,
    )
    fig.text(
        bx + bw / 2, by + bh * 0.37, str(int(metadata["penetracion_nacional_grafica"])),
        transform=fig.transFigure, fontsize=60, fontweight="bold", color=COLOR_TEXT,
        ha="center", va="center", zorder=7, clip_on=False,
    )
    line_y = by + bh * 0.60
    fig.add_artist(plt.Line2D(
        [bx + 0.02, bx + bw - 0.02], [line_y, line_y], transform=fig.transFigure,
        color="#d0d0d0", linewidth=0.8, zorder=7, clip_on=False,
    ))

    # El ejemplo incluye la tarjeta de crecimiento. B.21 no calcula esa tasa;
    # se conserva el componente visual sin inventar un dato, marcándolo como N/D.
    tx, ty, tw, th = 0.28, 0.155, 0.225, 0.095
    fig.add_artist(patches.FancyBboxPatch(
        (tx, ty), tw, th, boxstyle="round,pad=0.012,rounding_size=0.012",
        linewidth=0, edgecolor="none", facecolor="#2d4f4b",
        transform=fig.transFigure, zorder=6, clip_on=False,
    ))
    fig.add_artist(patches.FancyBboxPatch(
        (tx + 0.008, ty + 0.012), 0.038, th - 0.024,
        boxstyle="round,pad=0.005,rounding_size=0.008", linewidth=0,
        facecolor="#012f2a", transform=fig.transFigure, zorder=7, clip_on=False,
    ))
    icon_cx, icon_cy = tx + 0.027, ty + th / 2
    icon_hw, icon_hh = 0.010, 0.020
    xs = [icon_cx - icon_hw, icon_cx - icon_hw * 0.3, icon_cx + icon_hw * 0.3, icon_cx + icon_hw]
    ys = [icon_cy - icon_hh * 0.4, icon_cy + icon_hh * 0.1, icon_cy - icon_hh * 0.15, icon_cy + icon_hh * 0.55]
    fig.add_artist(plt.Line2D(xs, ys, transform=fig.transFigure, color="white", linewidth=2.0,
                             solid_capstyle="round", solid_joinstyle="round", zorder=8, clip_on=False))
    fig.add_artist(plt.Line2D([icon_cx + icon_hw * 0.65, icon_cx + icon_hw],
                             [icon_cy + icon_hh * 0.20, icon_cy + icon_hh * 0.55],
                             transform=fig.transFigure, color="white", linewidth=2.0,
                             solid_capstyle="round", zorder=8, clip_on=False))
    text_cx = tx + 0.008 + 0.038 + (tw - 0.008 - 0.038) / 2 + 0.008
    fig.text(text_cx, ty + th * 0.65, "Tasa de crecimiento", transform=fig.transFigure,
             fontsize=9.5, fontweight="bold", color="white", ha="center", va="center", zorder=7)
    fig.text(text_cx, ty + th * 0.28, "anual N/D", transform=fig.transFigure,
             fontsize=9.5, fontweight="bold", color="white", ha="center", va="center", zorder=7)

    fig.text(0.08, 0.94, " ", bbox=dict(boxstyle="round,pad=1.6,rounding_size=0.2",
             facecolor="#4a7d75", edgecolor="none"), va="center", fontsize=2)
    fig.text(0.093, 0.94, "Figura B.21.", fontsize=14, fontweight="bold", color=COLOR_TEXT, va="center")
    fig.text(
        0.180, 0.94,
        "Accesos del Servicio de Televisión Restringida Residencial por cada 100 hogares por entidad federativa",
        fontsize=14, fontweight="medium", color=COLOR_TEXT, va="center",
    )

    legend_handles = [patches.Patch(facecolor=color, edgecolor="none", label=label)
                      for color, label in zip(COLORS, LABELS)]
    legend = map_ax.legend(
        handles=legend_handles,
        title="Accesos del servicio de televisión\nrestringida residencial\npor cada 100 hogares:",
        loc="lower left", bbox_to_anchor=(0.08, 0.12), bbox_transform=fig.transFigure,
        prop={"weight": "normal", "size": 10},
        title_fontproperties={"weight": "bold", "size": 10},
        facecolor="white", labelcolor=COLOR_TEXT, edgecolor="none", framealpha=0.0,
        handletextpad=0.5, labelspacing=0.3, handlelength=1.2,
        borderpad=0.0, borderaxespad=0.0,
    )
    legend._legend_box.align = "left"
    legend.get_title().set_multialignment("left")
    legend.get_title().set_color(COLOR_TEXT)

    months = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
        7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
    }
    month = months[int(metadata["mes_bit"])]
    fig.text(0.08, 0.07, "Fuente:", fontsize=8, fontweight="bold", color=COLOR_TEXT, ha="left", va="center")
    fig.text(
        0.11, 0.07,
        f"IFT con datos de los operadores de telecomunicaciones a {month} de "
        f"{int(metadata['anio_bit'])} y de la ENDUTIH {ENDUTIH_YEAR} del INEGI.",
        fontsize=8, fontweight="normal", color=COLOR_TEXT, ha="left", va="center",
    )

    plt.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.15)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  B.21 | Adquisición o reutilización de TODO.zip de BIT/CRT")
    bit_path = context.acquire_source(BIT_SOURCE_ID)
    print("  B.21 | Adquisición o reutilización del ZIP ENDUTIH 2025")
    endutih_path = context.acquire_source(ENDUTIH_SOURCE_ID)
    print("  B.21 | Reutilización de la geometría estatal de México")
    geojson_path = context.acquire_source(MAP_SOURCE_ID)

    print("  B.21 | Lectura de accesos, hogares y cálculo por entidad")
    data, metadata = build_metrics(load_bit_table(bit_path), load_households(endutih_path))
    bit_period = f"{int(metadata['anio_bit'])}-{int(metadata['mes_bit']):02d}"
    context.record_source_period(BIT_SOURCE_ID, bit_period, "ULTIMO_DISPONIBLE")
    context.record_source_period(ENDUTIH_SOURCE_ID, str(ENDUTIH_YEAR), "AL_DIA")
    context.record_source_period(MAP_SOURCE_ID, "sin versión declarada", "REFERENCIA_VISUAL")
    context.write_data_used(data)

    for row in data.itertuples(index=False):
        context.record_calculation(
            f"penetracion_{row.K_ENTIDAD:02d}",
            "accesos residenciales BIT / suma(FAC_HOG ENDUTIH) * 100",
            {
                "entidad": row.entidad,
                "periodo_bit": bit_period,
                "anio_endutih": ENDUTIH_YEAR,
                "accesos": row.accesos_residenciales,
                "hogares": row.hogares_expandidos,
            },
            row.penetracion,
            "accesos por cada 100 hogares",
            0,
        )
    context.record_calculation(
        "penetracion_nacional",
        "suma(accesos residenciales BIT) / suma(FAC_HOG ENDUTIH) * 100",
        {
            "periodo_bit": bit_period,
            "anio_endutih": ENDUTIH_YEAR,
            "accesos": metadata["accesos_nacionales"],
            "hogares": metadata["hogares_nacionales"],
        },
        metadata["penetracion_nacional"],
        "accesos por cada 100 hogares",
        0,
    )

    ranked = data.sort_values("penetracion", ascending=False)
    highest = ranked.head(3).to_dict("records")
    lowest = ranked.tail(3).sort_values("penetracion", ascending=False).to_dict("records")
    text_path = context.render_text("b_21.md.j2", {
        "anio_bit": int(metadata["anio_bit"]),
        "mes_bit": int(metadata["mes_bit"]),
        "anio_endutih": ENDUTIH_YEAR,
        "penetracion_nacional": float(metadata["penetracion_nacional"]),
        "mayor_1": highest[0], "mayor_2": highest[1], "mayor_3": highest[2],
        "menor_1": lowest[0], "menor_2": lowest[1], "menor_3": lowest[2],
    })
    print("  B.21 | Generación del mapa PNG")
    _plot(data, metadata, geojson_path, context.expected_figure_path, context.project_root)
    return {
        "figure_path": str(context.expected_figure_path),
        "text_path": str(text_path),
        "source_latest_period": f"BIT {bit_period}; ENDUTIH {ENDUTIH_YEAR}",
        "rows_used": len(data),
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
