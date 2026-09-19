"""Figura G.1: concesiones de radiodifusión para AM, FM y TDT."""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import patches


FIGURE_ID = "G.1"
SOURCE_RADIO = "crt_bit_srs_estaciones_entidad_actual"
SOURCE_TDT = "crt_bit_str_catalogo_distintivos_actual"
SERVICES = ["TDT", "FM", "AM"]
CATEGORIES = [
    ("COMERCIAL", "Comerciales", "#132b2d"),
    ("PUBLICO", "Públicas", "#335a5c"),
    ("SOCIAL", "Sociales", "#4c7d7e"),
    ("SOCIAL COMUNITARIA", "Sociales Comunitarias", "#64a0a1"),
    ("SOCIAL INDIGENA", "Sociales Indígenas", "#86adae"),
    ("SOCIAL AFROMEXICANA", "Sociales Afromexicanas", "#5c9596"),
]
REFERENCE_2023 = {
    "TDT": [597, 278, 52, 7, 0],
    "FM": [1171, 303, 267, 144, 27],
    "AM": [272, 58, 31, 4, 3],
}
TEXT = "#3c3c3b"
BG = "#F8F8FA"

<<<<<<< HEAD
# Estilo de etiquetas tipo chip, alineado con la Figura C.14.
CHIP_LINE = "#8f9a9d"
CHIP_EDGE = "#cbd4d8"
CHIP_FACE = "white"
CHIP_PAD = 0.30
CHIP_LW = 0.9
CHIP_FONTSIZE = 9.0
TOTAL_FONTSIZE = 9.8

=======
>>>>>>> 93f2bf9f8ee9510be3d7cd1817e28eb1b7e51fc4

def _norm(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"\s+", " ", text.strip().upper())


def _read_csv(path: Path) -> pd.DataFrame:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        for separator in (",", ";", "\t"):
            try:
                data = pd.read_csv(path, encoding=encoding, sep=separator, low_memory=False)
                if data.shape[1] > 1:
                    data.columns = [_norm(column).replace(" ", "_") for column in data.columns]
                    return data
            except Exception as exc:  # pragma: no cover - sólo se conserva el último diagnóstico
                last_error = exc
    raise ValueError(f"No fue posible leer {path.name}: {last_error}")


def _column(data: pd.DataFrame, *aliases: str) -> str:
    available = {_norm(column).replace(" ", "_"): column for column in data.columns}
    for alias in aliases:
        normalized = _norm(alias).replace(" ", "_")
        if normalized in available:
            return available[normalized]
    raise KeyError(f"Falta una columna requerida {aliases}; disponibles: {list(data.columns)}")


def _canonical_use(value: object) -> str:
    text = _norm(value)
    if "AFROMEX" in text:
        return "SOCIAL AFROMEXICANA"
    if "COMUNITAR" in text:
        return "SOCIAL COMUNITARIA"
    if "INDIGEN" in text:
        return "SOCIAL INDIGENA"
    if "COMERCIAL" in text:
        return "COMERCIAL"
    if "PUBLIC" in text:
        return "PUBLICO"
    if "SOCIAL" in text:
        return "SOCIAL"
    return text


def _prepare_radio(data: pd.DataFrame) -> pd.DataFrame:
    year = _column(data, "ANIO", "AÑO", "YEAR")
    band = _column(data, "BANDA", "SERVICIO")
    use = _column(data, "TIPO_USO", "USO", "TIPO_DE_USO", "MODALIDAD")
    count = _column(data, "NO_ESTACIONES", "NUM_ESTACIONES", "NUMERO_ESTACIONES")
    result = pd.DataFrame({
        "anio": pd.to_numeric(data[year], errors="coerce"),
        "servicio": data[band].map(_norm),
        "tipo_uso": data[use].map(_canonical_use),
        "concesiones": pd.to_numeric(data[count], errors="coerce").fillna(0),
    })
    return result.loc[result.anio.between(2000, 2100)].copy()


def _prepare_tdt(data: pd.DataFrame) -> pd.DataFrame:
    year = _column(data, "ANIO", "AÑO", "YEAR")
    use = _column(data, "TIPO_USO", "USO", "TIPO_DE_USO", "MODALIDAD")
    identifier = _column(data, "DISTINTIVO", "DISTINTIVO_LLAMADA", "ID_ESTACION", "ID")
    result = pd.DataFrame({
        "anio": pd.to_numeric(data[year], errors="coerce"),
        "tipo_uso": data[use].map(_canonical_use),
        "distintivo": data[identifier].astype("string").str.strip(),
    })
    valid = result.anio.between(2000, 2100) & result.distintivo.notna() & result.distintivo.ne("")
    return result.loc[valid].copy()


def calculate_data(path_radio: Path, path_tdt: Path) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    radio = _prepare_radio(_read_csv(path_radio))
    tdt = _prepare_tdt(_read_csv(path_tdt))
    common_years = sorted(set(radio.anio.astype(int)) & set(tdt.anio.astype(int)))
    if not common_years:
        raise ValueError("Las tablas de radio y TDT no comparten un año válido")
    year = common_years[-1]

    present_uses = set(radio.loc[radio.anio.eq(year), "tipo_uso"]) | set(
        tdt.loc[tdt.anio.eq(year), "tipo_uso"]
    )
    categories = [item for item in CATEGORIES if item[0] in present_uses]
    rows: list[dict[str, object]] = []
    for service in SERVICES:
        for order, (key, label, color) in enumerate(categories):
            if service == "TDT":
                subset = tdt.loc[tdt.anio.eq(year) & tdt.tipo_uso.eq(key), "distintivo"]
                value = int(subset.nunique())
                formula = "conteo distinto de DISTINTIVO"
            else:
                subset = radio.loc[
                    radio.anio.eq(year) & radio.servicio.eq(service) & radio.tipo_uso.eq(key),
                    "concesiones",
                ]
                value = int(round(float(subset.sum())))
                formula = "suma de NO_ESTACIONES"
            rows.append({
                "anio": year,
                "servicio": service,
                "tipo_uso": key,
                "categoria": label,
                "orden": order,
                "concesiones": value,
                "formula": formula,
                "color": color,
            })
    result = pd.DataFrame(rows)
    totals = result.groupby(["anio", "servicio"], as_index=False).concesiones.sum()
    if set(totals.servicio) != set(SERVICES) or totals.concesiones.le(0).any():
        raise ValueError(f"El cálculo produjo servicios incompletos: {totals.to_dict('records')}")

    comparisons: list[dict[str, object]] = []
    reference_labels = [item[1] for item in CATEGORIES[:5]]
    current = result.set_index(["servicio", "categoria"])["concesiones"]
    for service in SERVICES:
        for label, expected in zip(reference_labels, REFERENCE_2023[service], strict=True):
            calculated = int(current.get((service, label), 0))
            comparisons.append({
                "anio": 2023,
                "servicio": service,
                "categoria": label,
                "anuario_2024": expected,
                "archivo_bit_actual": calculated,
                "diferencia": calculated - expected,
            })
    return result, pd.DataFrame(comparisons), year


def _font(root: Path) -> str:
    for name in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf"):
        path = root / "assets" / "fonts" / "Noto_Sans" / name
        if path.is_file():
            fm.fontManager.addfont(path)
    return "Noto Sans" if any(item.name == "Noto Sans" for item in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data: pd.DataFrame, year: int, output: Path, root: Path) -> None:
    plt.rcParams.update({"font.family": _font(root), "axes.unicode_minus": False})
<<<<<<< HEAD

=======
>>>>>>> 93f2bf9f8ee9510be3d7cd1817e28eb1b7e51fc4
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.add_artist(patches.Rectangle(
        (.055, .878), .009, .014, transform=fig.transFigure,
        facecolor="#4a7d75", edgecolor="none",
    ))
    fig.text(.073, .885, "Figura G.1.", fontsize=14, fontweight="bold", color=TEXT, va="center")
<<<<<<< HEAD
    fig.text(
        .158, .885,
        "Concesiones otorgadas de radiodifusión para AM, FM y TDT, a nivel nacional",
        fontsize=14, fontweight="medium", color=TEXT, va="center",
    )

    ax = fig.add_axes([.11, .22, .78, .56])
    ax.set_facecolor(BG)

    y_positions = {"TDT": 2, "FM": 1, "AM": 0}
    bar_height = .48
    maximum = int(data.groupby("servicio").concesiones.sum().max())

    running = {service: 0 for service in SERVICES}
    callouts = {service: [] for service in SERVICES}

    # Barras apiladas y metadatos para las etiquetas.
    for _, row in data.sort_values(["orden", "servicio"]).iterrows():
        service = str(row.servicio)
        value = int(row.concesiones)
        left = running[service]

        ax.barh(
            y_positions[service], value, left=left, height=bar_height,
            color=row.color, edgecolor="none",
            label=row.categoria if service == "TDT" else None,
            zorder=3,
        )

        if value > 0:
            center = left + value / 2
            callouts[service].append({
                "order": int(row.orden),
                "center": center,
                "value": value,
                "color": str(row.color),
            })

        running[service] += value

    # Chips de valores.
    # Las categorías pares van arriba y las impares abajo. Cada orden usa una
    # altura distinta, de modo que incluso los segmentos muy pequeños no se
    # encimen. Como xy y xytext comparten la misma x, los conectores son
    # SIEMPRE verticales y rectos: no hay diagonales.
    for service in SERVICES:
        y = y_positions[service]

        for item in callouts[service]:
            order = item["order"]
            center = item["center"]
            value = item["value"]
            color = item["color"]

            side = 1 if order % 2 == 0 else -1
            level = order // 2
            label_y = y + side * (.36 + level * .14)
            bar_edge_y = y + side * bar_height / 2

            ax.annotate(
                f"{value:,}",
                xy=(center, bar_edge_y),
                xytext=(center, label_y),
                ha="center", va="center",
                fontsize=CHIP_FONTSIZE,
                color=TEXT,
                fontweight="bold",
                bbox=dict(
                    boxstyle=f"round,pad={CHIP_PAD},rounding_size=.7",
                    facecolor=CHIP_FACE,
                    edgecolor=CHIP_EDGE,
                    linewidth=CHIP_LW,
                ),
                arrowprops=dict(
                    arrowstyle="-",
                    color=color,
                    linewidth=CHIP_LW,
                    shrinkA=0,
                    shrinkB=0,
                    connectionstyle="arc3,rad=0",
                ),
                annotation_clip=False,
                zorder=6,
            )

        # Chip del total con conector horizontal recto.
        total = running[service]
        ax.annotate(
            f"Total: {total:,}",
            xy=(total, y),
            xytext=(total + maximum * .055, y),
            ha="left", va="center",
            fontsize=TOTAL_FONTSIZE,
            color=TEXT,
            fontweight="bold",
            bbox=dict(
                boxstyle=f"round,pad={CHIP_PAD},rounding_size=.7",
                facecolor=CHIP_FACE,
                edgecolor=CHIP_EDGE,
                linewidth=CHIP_LW,
            ),
            arrowprops=dict(
                arrowstyle="-",
                color=CHIP_LINE,
                linewidth=CHIP_LW,
                shrinkA=0,
                shrinkB=0,
                connectionstyle="arc3,rad=0",
            ),
            annotation_clip=False,
            zorder=6,
        )

    ax.set_xlim(0, maximum * 1.32)
    ax.set_ylim(-.88, 2.88)
    ax.set_yticks([2, 1, 0], ["TDT", "FM", "AM"])
    ax.tick_params(axis="y", colors=TEXT, labelsize=10.5, length=0, pad=18)
    ax.tick_params(axis="x", colors=TEXT, labelsize=9.5)
    ax.grid(axis="x", color="#d1d1d1", linewidth=1, zorder=0)

=======
    fig.text(.158, .885, "Concesiones otorgadas de radiodifusión para AM, FM y TDT, a nivel nacional",
             fontsize=14, fontweight="medium", color=TEXT, va="center")

    ax = fig.add_axes([.11, .22, .78, .56])
    ax.set_facecolor(BG)
    y_positions = {"TDT": 2, "FM": 1, "AM": 0}
    maximum = int(data.groupby("servicio").concesiones.sum().max())
    running = {service: 0 for service in SERVICES}
    callouts = {service: [] for service in SERVICES}
    for _, row in data.sort_values(["orden", "servicio"]).iterrows():
        service = str(row.servicio)
        value = int(row.concesiones)
        ax.barh(y_positions[service], value, left=running[service], height=.48,
                color=row.color, edgecolor="none", label=row.categoria if service == "TDT" else None)
        center = running[service] + value / 2
        if value > 0:
            callouts[service].append((int(row.orden), center, value, str(row.color)))
        running[service] += value

    for service in SERVICES:
        y = y_positions[service]
        total = running[service]
        for order, center, value, color in callouts[service]:
            side = 1 if order % 2 == 0 else -1
            level = order // 2
            label_x = center
            if value < maximum * .025:
                label_x += (order - 2.5) * maximum * .012
            label_y = y + side * (.34 + level * .07)
            ax.annotate(
                f"{value:,}", xy=(center, y + side * .24), xytext=(label_x, label_y),
                ha="center", va="center", fontsize=7.5, color=TEXT, fontweight="bold",
                bbox=dict(boxstyle="round,pad=.22", facecolor="white", edgecolor="none"),
                arrowprops=dict(arrowstyle="-", color=color, linewidth=.8,
                                connectionstyle="arc3,rad=0"),
                annotation_clip=False, zorder=5,
            )
        total = running[service]
        ax.annotate(
            f"Total: {total:,}", xy=(total, y), xytext=(total + maximum * .045, y),
            ha="left", va="center", fontsize=9, color=TEXT, fontweight="bold",
            bbox=dict(boxstyle="round,pad=.24", facecolor="white", edgecolor="none"),
            arrowprops=dict(arrowstyle="-", color="#7c7c7c", linewidth=.8,
                            connectionstyle="arc3,rad=0"),
        )
    ax.set_xlim(0, maximum * 1.32)
    ax.set_ylim(-.72, 2.82)
    ax.set_yticks([2, 1, 0], ["TDT", "FM", "AM"])
    ax.tick_params(axis="y", colors=TEXT, labelsize=10, length=0, pad=18)
    ax.tick_params(axis="x", colors=TEXT, labelsize=9)
    ax.grid(axis="x", color="#d1d1d1", linewidth=1, zorder=0)
>>>>>>> 93f2bf9f8ee9510be3d7cd1817e28eb1b7e51fc4
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_visible(True)
        ax.spines[side].set_color("#7c7c7c")
        ax.spines[side].set_linewidth(1)
<<<<<<< HEAD

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles, labels,
        loc="upper center", bbox_to_anchor=(.5, -.11), ncol=5,
        frameon=False, fontsize=9.2, labelcolor=TEXT,
        columnspacing=1.25, handlelength=2.5,
    )

    fig.text(.055, .09, "Fuente:", fontsize=8.5, fontweight="bold", color=TEXT)
    fig.text(
        .099, .09,
        f"CRT con datos del Banco de Información de Telecomunicaciones (BIT), corte {year}.",
        fontsize=8.5, color=TEXT,
    )

=======
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, -.11), ncol=5,
              frameon=False, fontsize=9, labelcolor=TEXT, columnspacing=1.25, handlelength=2.5)

    fig.text(.055, .09, "Fuente:", fontsize=8.5, fontweight="bold", color=TEXT)
    fig.text(.099, .09,
             f"CRT con datos del Banco de Información de Telecomunicaciones (BIT), corte {year}.",
             fontsize=8.5, color=TEXT)
>>>>>>> 93f2bf9f8ee9510be3d7cd1817e28eb1b7e51fc4
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  G.1 | Descarga o reutilización de los CSV individuales de BIT/CRT")
    radio_path = context.acquire_source(SOURCE_RADIO)
    tdt_path = context.acquire_source(SOURCE_TDT)
    print("  G.1 | Cálculo desde datos crudos de AM, FM y TDT")
    data, comparison, year = calculate_data(radio_path, tdt_path)
    context.record_source_period(SOURCE_RADIO, str(year), "ULTIMO_DISPONIBLE")
    context.record_source_period(SOURCE_TDT, str(year), "ULTIMO_DISPONIBLE")
    context.write_data_used(data.drop(columns="color"))
    context.write_data_used(comparison, "control_anuario_2024")

    for row in data.itertuples(index=False):
        context.record_calculation(
            f"concesiones_{row.servicio.lower()}_{row.tipo_uso.lower().replace(' ', '_')}",
            row.formula,
            {"anio": year, "servicio": row.servicio, "tipo_uso": row.tipo_uso},
            row.concesiones,
            "concesiones",
            0,
        )
    totals = data.groupby("servicio", sort=False).concesiones.sum()
    print(f"\nG.1 | Resultados usados, corte {year}")
    print(data[["servicio", "categoria", "concesiones"]].to_string(index=False))
    print("\nG.1 | Totales")
    for service in SERVICES:
        print(f"  {service}: {int(totals[service]):,}")
    print("\nG.1 | Control contra las etiquetas publicadas en el Anuario 2024")
    print(comparison.to_string(index=False))

    largest = totals.idxmax()
    text_path = context.render_text("parrafo_figura.md.j2", {
        "periodo": str(year),
        "descripcion": (
            f"BIT registra {int(totals['AM']):,} concesiones de AM, {int(totals['FM']):,} de FM "
            f"y {int(totals['TDT']):,} distintivos de TDT en el último corte común disponible."
        ),
        "variacion": None,
        "mayor": {"etiqueta": largest, "valor": int(totals[largest])},
        "menor": None,
        "unidad": "concesiones",
        "decimales": 0,
    })
    print("  G.1 | Generación de gráfica PNG")
    _plot(data, year, context.expected_figure_path, context.project_root)
    return {
        "figure_path": str(context.expected_figure_path),
        "text_path": str(text_path),
        "source_latest_period": str(year),
        "rows_used": len(data),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "src"))
    from anuario2026.pipeline import run_pipeline

    run_pipeline(root, only=FIGURE_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
