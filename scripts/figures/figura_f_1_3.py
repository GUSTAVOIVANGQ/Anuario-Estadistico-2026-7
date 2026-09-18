"""Figura F.1.3: habilidades en la computadora, por sexo."""

from __future__ import annotations

import math
import sys
import textwrap
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as font_manager
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd


FIGURE_ID = "F.1.3"
CURRENT_SOURCE_ID = "inegi_endutih_2024_reference"
PERIOD_CURRENT = "2024"
LATEST_SOURCE_ID = "inegi_endutih_2025"
PERIOD_LATEST = "2025"
TABLE_TOKEN = "usuarios_anual"
REPORT_TITLE = "Habilidades en la computadora"
SUMMARY_TITLE = "Usuarios de computadora"
UNIVERSE = "P6_1"
HIGHLIGHT = ("Descargar contenidos de Internet", "P6_8_2")
METRICS = [
    ("Enviar y recibir correo electrónico", "P6_8_1", 84, 85),
    ("Crear archivos de texto", "P6_8_4", 85, 85),
    ("Copiar archivos entre directorios", "P6_8_3", 79, 80),
    ("Crear presentaciones", "P6_8_6", 75, 74),
    ("Crear hojas de cálculo", "P6_8_5", 67, 68),
    ("Instalar dispositivos periféricos", "P6_8_7", 55, 65),
    ("Crear o usar bases de datos", "P6_8_8", 48, 50),
    ("Programar en lenguaje especializado", "P6_8_9", 15, 19),
]
REFERENCE_SUMMARY = {"mujeres": 22_584_696, "hombres": 21_932_479, "mujeres_pct": 36, "hombres_pct": 39}
REFERENCE_HIGHLIGHT = (87, 88)
STRICT_SUMMARY = True
REFERENCE_TOLERANCE_PP = 0
REFERENCE_STATUS = "REPRODUCIDA_EXACTAMENTE"
GRID_ROW_COUNTS = (4, 4)
PANEL_COLOR = "pink"
NOTE = "Todos los usuarios se refieren a personas de 6 años o más. ENDUTIH 2024 es el último corte con todas las habilidades comparables."

REFERENCE_SOURCE_ID = "inegi_endutih_2023_reference"
PERIOD_REFERENCE = "2023"
LANDING_PAGE = f"https://www.inegi.org.mx/programas/endutih/{PERIOD_CURRENT}/"

TEXT = "#3c3c3b"
WOMEN = "#b35aba"
MEN = "#006157"
ACCENT = "#4a7d75"
PANEL_PINK = "#F8E6E1"
PANEL_BLUE = "#E8F2F1"
BACKGROUND = "#F8F8FA"
WHITE = "#FFFFFF"


def _configure_fonts(project_root: Path) -> None:
    font_dir = project_root / "assets" / "fonts" / "Noto_Sans"
    for name in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf"):
        path = font_dir / name
        if path.is_file():
            font_manager.fontManager.addfont(path)
    available = {item.name for item in font_manager.fontManager.ttflist}
    plt.rcParams.update(
        {
            "font.family": "Noto Sans" if "Noto Sans" in available else "DejaVu Sans",
            "axes.unicode_minus": False,
        }
    )


def _formula_columns(formula: str | tuple[str, ...]) -> set[str]:
    return {formula} if isinstance(formula, str) else set(formula)


def _required_columns() -> set[str]:
    columns = {"SEXO", "EDAD", "FAC_PER"}
    columns |= _formula_columns(UNIVERSE)
    columns |= _formula_columns(HIGHLIGHT[1])
    for _, formula, _, _ in METRICS:
        columns |= _formula_columns(formula)
    return columns


def _pick_member(archive: zipfile.ZipFile, token: str) -> str:
    marker = f"_{token.lower()}_"
    matches = [
        name
        for name in archive.namelist()
        if name.lower().endswith(".csv")
        and "conjunto_de_datos/" in name.lower().replace("\\", "/")
        and marker in Path(name).name.lower()
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Se esperaba un CSV {token} y se encontraron {len(matches)} en {archive.filename}: {matches}"
        )
    return matches[0]


def _member_columns(path: Path, token: str) -> tuple[set[str], str]:
    if not zipfile.is_zipfile(path):
        raise ValueError(f"El insumo ENDUTIH no es un ZIP válido: {path}")
    with zipfile.ZipFile(path) as archive:
        member = _pick_member(archive, token)
        with archive.open(member) as stream:
            header = pd.read_csv(stream, encoding="latin1", nrows=0)
    return {str(column).strip().upper() for column in header.columns}, member


def load_endutih(path: Path, token: str) -> tuple[pd.DataFrame, str]:
    available, member = _member_columns(path, token)
    required = _required_columns()
    missing = sorted(required - available)
    if missing:
        raise ValueError(f"Faltan variables ENDUTIH en {member}: {missing}")
    with zipfile.ZipFile(path) as archive, archive.open(member) as stream:
        frame = pd.read_csv(
            stream,
            encoding="latin1",
            usecols=lambda column: str(column).strip().upper() in required,
            low_memory=False,
        )
    frame.columns = [str(column).strip().upper() for column in frame.columns]
    print(f"  {FIGURE_ID} | {path.name}: {len(frame):,} registros; tabla {member}")
    return frame, member


def _num(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def _condition(frame: pd.DataFrame, formula: str | tuple[str, ...]) -> pd.Series:
    if isinstance(formula, str):
        return _num(frame, formula).eq(1)
    return pd.concat([_num(frame, column).eq(1) for column in formula], axis=1).any(axis=1)


def _formula_text(formula: str | tuple[str, ...]) -> str:
    if isinstance(formula, str):
        return f"{formula}=1"
    return "(" + " OR ".join(f"{column}=1" for column in formula) + ")"


def _round_half_up(value: float) -> int:
    return int(math.floor(float(value) + 0.5))


def calculate(frame: pd.DataFrame, period: str) -> pd.DataFrame:
    weight = _num(frame, "FAC_PER").fillna(0.0)
    age = _num(frame, "EDAD").ge(6)
    sex_values = _num(frame, "SEXO")
    universe_condition = _condition(frame, UNIVERSE)
    rows: list[dict[str, object]] = []

    for sex_value, sex_label in ((2, "Mujeres"), (1, "Hombres")):
        sex = sex_values.eq(sex_value)
        population = age & sex
        universe = population & universe_condition
        population_weight = float(weight.loc[population].sum())
        universe_weight = float(weight.loc[universe].sum())
        if population_weight <= 0 or universe_weight <= 0:
            raise ValueError(f"Universo ponderado no positivo para {sex_label}")

        rows.append(
            {
                "periodo": period,
                "tipo": "resumen",
                "indicador": SUMMARY_TITLE,
                "variable": _formula_text(UNIVERSE),
                "sexo": sex_label,
                "personas": round(universe_weight),
                "universo": round(population_weight),
                "porcentaje": universe_weight / population_weight * 100,
                "porcentaje_mostrado": _round_half_up(universe_weight / population_weight * 100),
            }
        )

        for kind, title, formula in [
            ("destacado", HIGHLIGHT[0], HIGHLIGHT[1]),
            *[("indicador", title, formula) for title, formula, _, _ in METRICS],
        ]:
            numerator = float(weight.loc[universe & _condition(frame, formula)].sum())
            percentage = numerator / universe_weight * 100
            rows.append(
                {
                    "periodo": period,
                    "tipo": kind,
                    "indicador": title,
                    "variable": _formula_text(formula),
                    "sexo": sex_label,
                    "personas": round(numerator),
                    "universo": round(universe_weight),
                    "porcentaje": percentage,
                    "porcentaje_mostrado": _round_half_up(percentage),
                }
            )

    return pd.DataFrame(rows)


def validate_reference(reference: pd.DataFrame) -> dict[str, object]:
    data = calculate(reference, PERIOD_REFERENCE)
    differences: list[dict[str, object]] = []

    summary = data.loc[data["tipo"].eq("resumen")].set_index("sexo")
    for sex, expected_count, expected_share in (
        ("Mujeres", REFERENCE_SUMMARY["mujeres"], REFERENCE_SUMMARY["mujeres_pct"]),
        ("Hombres", REFERENCE_SUMMARY["hombres"], REFERENCE_SUMMARY["hombres_pct"]),
    ):
        observed_count = int(summary.loc[sex, "personas"])
        observed_share = int(summary.loc[sex, "porcentaje_mostrado"])
        differences.append(
            {
                "indicador": SUMMARY_TITLE,
                "sexo": sex,
                "publicado": f"{expected_count:,}; {expected_share}%",
                "recalculado": f"{observed_count:,}; {observed_share}%",
                "diferencia_pp": abs(observed_share - expected_share),
            }
        )
        if STRICT_SUMMARY and (observed_count != expected_count or observed_share != expected_share):
            raise RuntimeError(
                f"{FIGURE_ID} no reprodujo el resumen 2023 para {sex}: "
                f"{observed_count:,}/{observed_share}% frente a {expected_count:,}/{expected_share}%"
            )

    expected_metrics = {title: (women, men) for title, _, women, men in METRICS}
    expected_metrics[HIGHLIGHT[0]] = REFERENCE_HIGHLIGHT
    detail = data.loc[data["tipo"].isin(["destacado", "indicador"])].set_index(["indicador", "sexo"])
    maximum = 0
    for title, (women, men) in expected_metrics.items():
        for sex, expected in (("Mujeres", women), ("Hombres", men)):
            observed = int(detail.loc[(title, sex), "porcentaje_mostrado"])
            difference = abs(observed - expected)
            maximum = max(maximum, difference)
            differences.append(
                {
                    "indicador": title,
                    "sexo": sex,
                    "publicado": f"{expected}%",
                    "recalculado": f"{observed}%",
                    "diferencia_pp": difference,
                }
            )
    if maximum > REFERENCE_TOLERANCE_PP:
        raise RuntimeError(
            f"{FIGURE_ID} excedió la tolerancia de validación 2023: "
            f"{maximum} pp > {REFERENCE_TOLERANCE_PP} pp"
        )
    return {
        "estado": REFERENCE_STATUS,
        "comparaciones": len(differences),
        "diferencia_maxima_pp": maximum,
        "detalle": differences,
    }


def _card(ax: plt.Axes, x: float, y: float, width: float, height: float, color: str) -> None:
    ax.add_patch(
        patches.FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.006,rounding_size=0.018",
            transform=ax.transAxes,
            facecolor=color,
            edgecolor="none",
        )
    )


def _pair(ax: plt.Axes, x: float, y: float, width: float, women: int, men: int, size: float) -> None:
    ax.text(x + width * 0.27, y, "Mujeres", ha="center", va="bottom", color=TEXT, fontsize=size * 0.42, fontweight="bold", transform=ax.transAxes)
    ax.text(x + width * 0.27, y - 0.006, f"{women}%", ha="center", va="top", color=WOMEN, fontsize=size, fontweight="bold", transform=ax.transAxes)
    ax.text(x + width * 0.73, y, "Hombres", ha="center", va="bottom", color=TEXT, fontsize=size * 0.42, fontweight="bold", transform=ax.transAxes)
    ax.text(x + width * 0.73, y - 0.006, f"{men}%", ha="center", va="top", color=MEN, fontsize=size, fontweight="bold", transform=ax.transAxes)


def _plot(data: pd.DataFrame, output: Path, project_root: Path, period: str) -> None:
    _configure_fonts(project_root)
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    _card(ax, 0.025, 0.065, 0.95, 0.86, BACKGROUND)
    ax.add_patch(patches.FancyBboxPatch((0.038, 0.872), 0.008, 0.018, boxstyle="round,pad=0,rounding_size=.003", transform=ax.transAxes, facecolor=ACCENT, edgecolor="none"))
    ax.text(0.052, 0.881, f"Figura {FIGURE_ID}.", color=TEXT, fontsize=14, fontweight="bold", ha="left", va="center", transform=ax.transAxes)
    ax.text(0.155, 0.881, "Actividades en Smartphone, Internet, computadora y uso de redes sociales", color=TEXT, fontsize=14, ha="left", va="center", transform=ax.transAxes)

    _card(ax, 0.045, 0.675, 0.205, 0.15, WHITE)
    ax.text(0.1475, 0.75, textwrap.fill(REPORT_TITLE, 27), color=TEXT, fontsize=16, fontweight="bold", ha="center", va="center", transform=ax.transAxes)

    summary = data.loc[data["tipo"].eq("resumen")].set_index("sexo")
    _card(ax, 0.262, 0.675, 0.39, 0.15, PANEL_PINK if PANEL_COLOR == "pink" else PANEL_BLUE)
    ax.text(0.457, 0.794, SUMMARY_TITLE, color=TEXT, fontsize=12, fontweight="bold", ha="center", va="center", transform=ax.transAxes)
    for x, sex in ((0.36, "Mujeres"), (0.555, "Hombres")):
        row = summary.loc[sex]
        ax.text(x, 0.762, sex, color=TEXT, fontsize=9.5, fontweight="bold", ha="center", transform=ax.transAxes)
        ax.text(x, 0.724, f"{int(row['personas']):,}", color=TEXT, fontsize=18, fontweight="bold", ha="center", transform=ax.transAxes)
        ax.text(x, 0.693, f"({int(row['porcentaje_mostrado'])}% de la población de 6 años o más)", color=TEXT, fontsize=7.7, ha="center", transform=ax.transAxes)

    highlight = data.loc[data["tipo"].eq("destacado")].set_index("sexo")
    _card(ax, 0.664, 0.675, 0.291, 0.15, PANEL_PINK if PANEL_COLOR == "pink" else PANEL_BLUE)
    ax.text(0.8095, 0.788, textwrap.fill(HIGHLIGHT[0], 42), color=TEXT, fontsize=10.5, fontweight="bold", ha="center", va="center", transform=ax.transAxes)
    _pair(ax, 0.68, 0.735, 0.26, int(highlight.loc["Mujeres", "porcentaje_mostrado"]), int(highlight.loc["Hombres", "porcentaje_mostrado"]), 22)

    metrics = data.loc[data["tipo"].eq("indicador")]
    values = {
        (str(row.indicador), str(row.sexo)): int(row.porcentaje_mostrado)
        for row in metrics.itertuples(index=False)
    }
    if sum(GRID_ROW_COUNTS) != len(METRICS):
        raise ValueError("GRID_ROW_COUNTS no coincide con el número de indicadores")
    x0, x1, bottom, top, gap = 0.045, 0.955, 0.155, 0.645, 0.012
    nrows = len(GRID_ROW_COUNTS)
    height = (top - bottom - gap * (nrows - 1)) / nrows
    metric_index = 0
    for row, ncols in enumerate(GRID_ROW_COUNTS):
        width = (x1 - x0 - gap * (ncols - 1)) / ncols
        label_width = 25 if ncols <= 4 else 21
        label_size = 8.2 if ncols <= 4 else 7.2
        pair_size = 19 if ncols <= 4 else 17
        y = top - (row + 1) * height - row * gap
        for col in range(ncols):
            title, _, _, _ = METRICS[metric_index]
            metric_index += 1
            x = x0 + col * (width + gap)
            _card(ax, x, y, width, height, PANEL_PINK if PANEL_COLOR == "pink" else PANEL_BLUE)
            ax.text(x + width / 2, y + height * 0.78, textwrap.fill(title, label_width), color=TEXT, fontsize=label_size, fontweight="bold", ha="center", va="center", linespacing=1.08, transform=ax.transAxes)
            _pair(ax, x, y + height * 0.42, width, values[(title, "Mujeres")], values[(title, "Hombres")], pair_size)
            ax.add_patch(patches.Rectangle((x + width * 0.14, y + height * 0.12), width * 0.27, height * 0.025, transform=ax.transAxes, facecolor=WOMEN, edgecolor="none"))
            ax.add_patch(patches.Rectangle((x + width * 0.59, y + height * 0.12), width * 0.27, height * 0.025, transform=ax.transAxes, facecolor=MEN, edgecolor="none"))

    ax.text(0.04, 0.112, "Fuente:", color=TEXT, fontsize=8.5, fontweight="bold", ha="left", va="top", transform=ax.transAxes)
    source = f"IFT con datos de la ENDUTIH {period}, del INEGI. Datos disponibles en {LANDING_PAGE}"
    ax.text(0.085, 0.112, source, color=TEXT, fontsize=8.5, ha="left", va="top", transform=ax.transAxes)
    ax.text(0.04, 0.086, "Nota:", color=TEXT, fontsize=8.5, fontweight="bold", ha="left", va="top", transform=ax.transAxes)
    ax.text(0.075, 0.086, NOTE, color=TEXT, fontsize=8.5, ha="left", va="top", transform=ax.transAxes)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200, facecolor="white")
    plt.close(fig)


def generate(context):
    print(f"  {FIGURE_ID} | 1/5 Reutilización o descarga de ENDUTIH")
    reference_path = context.acquire_source(REFERENCE_SOURCE_ID)
    selected_source_id = CURRENT_SOURCE_ID
    selected_path = context.acquire_source(CURRENT_SOURCE_ID)
    selected_period = PERIOD_CURRENT
    compatibility: dict[str, object] = {"seleccionado": selected_period}

    if LATEST_SOURCE_ID:
        latest_path = context.acquire_source(LATEST_SOURCE_ID)
        latest_columns, latest_member = _member_columns(latest_path, TABLE_TOKEN)
        missing_latest = sorted(_required_columns() - latest_columns)
        compatibility = {
            "último_publicado": PERIOD_LATEST,
            "tabla": latest_member,
            "variables_faltantes": missing_latest,
            "seleccionado": selected_period if missing_latest else PERIOD_LATEST,
        }
        if not missing_latest:
            selected_source_id = LATEST_SOURCE_ID
            selected_path = latest_path
            selected_period = PERIOD_LATEST

    print(f"  {FIGURE_ID} | 2/5 Validación del modelo con ENDUTIH 2023")
    reference, reference_member = load_endutih(reference_path, TABLE_TOKEN)
    validation = validate_reference(reference)
    del reference
    print(
        f"  {FIGURE_ID} | Validación 2023: {validation['estado']}; "
        f"{validation['comparaciones']} contrastes; diferencia máxima "
        f"{validation['diferencia_maxima_pp']} pp"
    )

    print(f"  {FIGURE_ID} | 3/5 Cálculo con ENDUTIH {selected_period}")
    current, current_member = load_endutih(selected_path, TABLE_TOKEN)
    data = calculate(current, selected_period)
    del current

    context.record_source_period(REFERENCE_SOURCE_ID, PERIOD_REFERENCE, "REFERENCIA_REPRODUCIDA")
    context.record_source_period(selected_source_id, selected_period, "AL_DIA" if selected_period == PERIOD_LATEST else "ULTIMO_COMPATIBLE")
    if LATEST_SOURCE_ID:
        context.record_source_period(LATEST_SOURCE_ID, PERIOD_LATEST, "NO_COMPARABLE" if compatibility["variables_faltantes"] else "AL_DIA")

    context.write_data_used(data)
    context.record_calculation(
        "validacion_endutih_2023",
        "Suma FAC_PER por sexo; porcentajes ponderados dentro del universo declarado",
        {"tabla": reference_member, "universo": _formula_text(UNIVERSE)},
        validation,
        "personas y porcentaje",
        2,
    )
    context.record_calculation(
        f"resultados_endutih_{selected_period}",
        "Numerador=sum(FAC_PER donde indicador=1); denominador=sum(FAC_PER del universo, por sexo)",
        {
            "tabla": current_member,
            "universo": _formula_text(UNIVERSE),
            "compatibilidad": compatibility,
            "variables": [row[1] for row in METRICS],
        },
        {
            "periodo": selected_period,
            "filas_publicadas": len(data),
            "porcentaje_mayor": round(float(data.loc[data["tipo"].ne("resumen"), "porcentaje"].max()), 2),
        },
        "personas y porcentaje",
        2,
    )

    detail = data.loc[data["tipo"].isin(["destacado", "indicador"])]
    highest = detail.loc[detail["porcentaje"].idxmax()]
    summary_text = (
        f"Con ENDUTIH {selected_period}, {highest['indicador']} registró el mayor "
        f"porcentaje de la figura: {highest['porcentaje']:.1f}% en {highest['sexo'].lower()}."
    )
    text_path = context.render_text(
        "f_endutih.md.j2",
        {"resumen": summary_text, "periodo": selected_period, "figura": FIGURE_ID},
    )

    print(f"\nResultados usados por {FIGURE_ID} (ENDUTIH {selected_period}):")
    print(
        data[["tipo", "indicador", "sexo", "personas", "universo", "porcentaje"]]
        .to_string(
            index=False,
            formatters={
                "personas": lambda value: f"{value:,.0f}",
                "universo": lambda value: f"{value:,.0f}",
                "porcentaje": lambda value: f"{value:.2f}%",
            },
        )
    )
    print(f"  {FIGURE_ID} | 4/5 Texto automático generado: {text_path}")
    print(f"  {FIGURE_ID} | 5/5 Generación de gráfica PNG")
    _plot(data, context.expected_figure_path, context.project_root, selected_period)

    return {
        "figure_path": str(context.expected_figure_path),
        "text_path": str(text_path),
        "detected_period": selected_period,
        "rows_used": len(data),
        "reference_validation": validation["estado"],
        "source_table": current_member,
        "compatibility": compatibility,
    }


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root / "src"))
    from anuario2026.pipeline import run_pipeline

    run_pipeline(project_root, only=FIGURE_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
