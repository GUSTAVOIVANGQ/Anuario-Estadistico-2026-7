"""Figura A.3: descarga INEGI, cálculo de INPC/IPCOM y gráfica PNG."""

from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui

import csv
import json
import os
import queue
import re
import shutil
import sys
import textwrap
import threading
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, NamedTuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


FIGURE_ID = "A.3"
DYNAMIC_SOURCE_ID = "inegi_inpc_dynamic"
CURRENT_SOURCE_ID = "inegi_inpc_current_2026_07_reference"
DYNAMIC_URL = (
    "https://www.inegi.org.mx/app/indicesdeprecios/Estructura.aspx?"
    "idEstructura=112001300090&T=%C3%8Dndices+de+Precios+al+Consumidor&ST=Clasi"
)
SOURCE_LANDING_PAGE = "https://www.inegi.org.mx/programas/inpc/2018a/"
CSV_CONTROL_NAME = (
    "Consulta las series seleccionadas en formato separado por comas (CSV)"
)

COLOR_TEXT = "#3c3c3b"
COLOR_INPC = "#006157"
COLOR_IPCOM = "#b35aba"
COLOR_BACKGROUND = "#F8F8FA"

MONTH_NUMBER = {
    "Ene": 1,
    "Feb": 2,
    "Mar": 3,
    "Abr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Ago": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dic": 12,
}
MONTH_NAME = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}


class DynamicDownload(NamedTuple):
    path: Path
    cache_status: str
    acquired_at: str
    source_last_modified: str = ""
    content_type: str = "text/csv"


def _truthy_environment(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "si", "sí"}


def _configure_fonts(project_root: Path) -> str:
    font_dir = project_root / "assets" / "fonts" / "Noto_Sans"
    for name in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf"):
        path = font_dir / name
        if path.is_file():
            font_manager.fontManager.addfont(path)
    available = {item.name for item in font_manager.fontManager.ttflist}
    family = "Noto Sans" if "Noto Sans" in available else "DejaVu Sans"
    plt.rcParams.update({"font.family": family, "axes.unicode_minus": False})
    return family


def _run_isolated(function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Ejecuta Playwright síncrono fuera de un posible bucle asíncrono del host."""
    result_queue: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=1)

    def target() -> None:
        try:
            result_queue.put((True, function(*args, **kwargs)))
        except BaseException as exc:  # noqa: BLE001 - se propaga al hilo principal
            result_queue.put((False, exc))

    worker = threading.Thread(target=target, name="a3-playwright", daemon=True)
    worker.start()
    worker.join()
    ok, result = result_queue.get()
    if not ok:
        raise result
    return result


def _download_dynamic_with_playwright(destination: Path) -> dict[str, str]:
    """Descarga el CSV histórico desde el control dinámico de INEGI."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "A.3 necesita Playwright cuando el CSV no existe. Ejecuta "
            ".\\preparar_entorno.ps1 -ConPlaywright."
        ) from exc

    destination.parent.mkdir(parents=True, exist_ok=True)
    headed = _truthy_environment("ANUARIO_PLAYWRIGHT_HEADED")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed)
        try:
            page = browser.new_page(accept_downloads=True)
            page.goto(DYNAMIC_URL, wait_until="networkidle", timeout=120_000)
            page.get_by_role("img", name=CSV_CONTROL_NAME).click(timeout=60_000)

            start = page.locator("#MainContent_wuc_BarraHerramientas1_ddlAnioI")
            end = page.locator("#MainContent_wuc_BarraHerramientas1_ddlAnioF")
            start.wait_for(state="visible", timeout=60_000)
            end.wait_for(state="visible", timeout=60_000)

            available_start = [
                int(value)
                for value in start.locator("option").evaluate_all(
                    "nodes => nodes.map(node => node.value).filter(Boolean)"
                )
            ]
            available_end = [
                int(value)
                for value in end.locator("option").evaluate_all(
                    "nodes => nodes.map(node => node.value).filter(Boolean)"
                )
            ]
            if not available_start or not available_end:
                raise RuntimeError("INEGI no publicó las opciones de años para el CSV de A.3.")
            selected_start = min(2010, max(available_start))
            if selected_start not in available_start:
                selected_start = min(available_start)
            selected_end = max(available_end)
            start.select_option(str(selected_start))
            end.select_option(str(selected_end))
            page.wait_for_load_state("networkidle", timeout=120_000)

            with page.expect_download(timeout=120_000) as download_info:
                page.get_by_role("button", name="Exportar").click(timeout=120_000)
            download = download_info.value
            download.save_as(destination)
            return {
                "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "selected_start": str(selected_start),
                "selected_end": str(selected_end),
                "response_url": page.url,
                "suggested_filename": download.suggested_filename,
            }
        finally:
            browser.close()


def load_dynamic_series(path: Path) -> pd.DataFrame:
    """Lee las columnas total INPC y 08 Comunicaciones del CSV dinámico."""
    with path.open("r", encoding="latin1", newline="") as stream:
        rows = list(csv.reader(stream))
    header_index = next(
        (index for index, row in enumerate(rows) if row and row[0].strip() == "Título"),
        None,
    )
    if header_index is None:
        raise ValueError(f"No se encontró el encabezado Título en {path.name}")
    headers = rows[header_index]
    inpc_columns = [
        index
        for index, value in enumerate(headers)
        if index > 0 and "Nacional, total" in value
    ]
    ipcom_columns = [
        index
        for index, value in enumerate(headers)
        if index > 0 and "08 Comunicaciones" in value
    ]
    if len(inpc_columns) != 1 or len(ipcom_columns) != 1:
        raise ValueError(
            f"Se esperaban una columna INPC total y una IPCOM; se encontraron "
            f"{len(inpc_columns)} y {len(ipcom_columns)} en {path.name}"
        )
    inpc_column, ipcom_column = inpc_columns[0], ipcom_columns[0]
    records: list[dict[str, int | float | str]] = []
    for row in rows[header_index + 1 :]:
        if not row:
            continue
        match = re.fullmatch(r"([A-ZÁÉÍÓÚA-Za-záéíóú]{3})\s+(\d{4})", row[0].strip())
        if not match or match.group(1) not in MONTH_NUMBER:
            continue
        if len(row) <= max(inpc_column, ipcom_column):
            continue
        records.append(
            {
                "fecha": row[0].strip(),
                "anio": int(match.group(2)),
                "mes": MONTH_NUMBER[match.group(1)],
                "inpc_historico": float(row[inpc_column]),
                "ipcom": float(row[ipcom_column]),
            }
        )
    frame = pd.DataFrame.from_records(records)
    if frame.empty:
        raise ValueError(f"No se encontraron observaciones mensuales en {path.name}")
    frame = frame.sort_values(["anio", "mes"]).reset_index(drop=True)
    latest = frame.iloc[-1]
    if (int(latest["anio"]), int(latest["mes"])) < (2024, 7):
        raise ValueError(f"La serie IPCOM de {path.name} termina antes de julio de 2024")
    return frame


def _existing_dynamic(project_root: Path) -> Path | None:
    source_root = project_root / "data" / "raw" / DYNAMIC_SOURCE_ID / "objects"
    if not source_root.is_dir():
        return None
    candidates = [
        path
        for path in source_root.glob("*/*.csv")
        if path.is_file() and path.name != "metadata.json"
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None


def acquire_dynamic_source(project_root: Path) -> DynamicDownload:
    """Usa primero el CSV verificado y descarga con Playwright sólo si hace falta."""
    from anuario2026.sources import sha256_path, verify_raw_file

    existing = _existing_dynamic(project_root)
    if existing and not _truthy_environment("ANUARIO_FORCE_DOWNLOAD"):
        verify_raw_file(existing)
        load_dynamic_series(existing)
        metadata_path = existing.parent / "metadata.json"
        metadata = (
            json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata_path.is_file()
            else {}
        )
        return DynamicDownload(
            path=existing,
            cache_status="REUTILIZADO",
            acquired_at=str(metadata.get("downloaded_at", "")),
            source_last_modified=str(metadata.get("source_last_modified", "")),
            content_type=str(metadata.get("content_type", "text/csv")),
        )

    if _truthy_environment("ANUARIO_OFFLINE"):
        raise RuntimeError(
            "El CSV dinámico de A.3 no está en caché y ANUARIO_OFFLINE está activo."
        )

    staging_dir = project_root / "data" / "raw" / DYNAMIC_SOURCE_ID / "staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    partial = staging_dir / "inpc_ipcom_hasta_2024.csv.part"
    print("  A.3 | Descarga Playwright del CSV histórico INPC/IPCOM")
    metadata = _run_isolated(_download_dynamic_with_playwright, partial)
    verify_raw_file(partial)
    load_dynamic_series(partial)
    digest = sha256_path(partial)
    final_dir = project_root / "data" / "raw" / DYNAMIC_SOURCE_ID / "objects" / digest
    final_dir.mkdir(parents=True, exist_ok=True)
    final = final_dir / "inpc_ipcom_hasta_2024.csv"
    if final.exists():
        partial.unlink(missing_ok=True)
    else:
        shutil.move(str(partial), str(final))
    saved = {
        **metadata,
        "source_id": DYNAMIC_SOURCE_ID,
        "sha256": digest,
        "bytes": final.stat().st_size,
        "content_type": "text/csv",
        "cache_status": "DESCARGADO_Y_VERIFICADO",
    }
    (final_dir / "metadata.json").write_text(
        json.dumps(saved, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return DynamicDownload(
        path=final,
        cache_status="DESCARGADO_Y_VERIFICADO",
        acquired_at=str(metadata["downloaded_at"]),
    )


def load_current_inpc(path: Path) -> pd.DataFrame:
    """Lee la serie nacional INPC del conjunto mensual vigente de INEGI."""
    with zipfile.ZipFile(path) as archive:
        members = [
            name
            for name in archive.namelist()
            if name.lower().endswith("conjunto_de_datos_inpc_mensual.csv")
        ]
        if len(members) != 1:
            raise ValueError(
                f"Se esperaba un conjunto mensual INPC y se encontraron {len(members)}"
            )
        with archive.open(members[0]) as stream:
            data = pd.read_csv(stream, encoding="latin1")
    required = {"FECHA", "CONCEPTO", "VALOR"}
    if not required.issubset(data.columns):
        raise ValueError(f"Faltan columnas {sorted(required - set(data.columns))} en {path.name}")
    normalized = data["CONCEPTO"].astype(str).str.replace("\x8d", "", regex=False)
    mask = normalized.str.contains("Precios al Consumidor", case=False, regex=False) & normalized.str.contains(
        "INPC", case=False, regex=False
    )
    current = data.loc[mask, ["FECHA", "VALOR"]].copy()
    current["fecha_dt"] = pd.to_datetime(
        current["FECHA"], format="%Y-%m-%d", errors="coerce"
    )
    missing_dates = current["fecha_dt"].isna()
    current.loc[missing_dates, "fecha_dt"] = pd.to_datetime(
        current.loc[missing_dates, "FECHA"], errors="coerce", dayfirst=True
    )
    current["inpc"] = pd.to_numeric(current["VALOR"], errors="coerce")
    current = current.dropna(subset=["fecha_dt", "inpc"])
    current["anio"] = current["fecha_dt"].dt.year.astype(int)
    current["mes"] = current["fecha_dt"].dt.month.astype(int)
    current = current.sort_values(["anio", "mes"]).drop_duplicates(["anio", "mes"], keep="last")
    if current.empty:
        raise ValueError(f"No se localizó la serie total INPC en {path.name}")
    return current[["anio", "mes", "inpc"]].reset_index(drop=True)


def build_annual_series(dynamic: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    """Construye el corte del diseño: diciembre, salvo julio 2024 y último 2026."""
    latest = current.iloc[-1]
    latest_year, latest_month = int(latest["anio"]), int(latest["mes"])
    records: list[dict[str, int | float | str]] = []
    for year in range(2010, latest_year + 1):
        if year <= 2023:
            month = 12
        elif year == 2024:
            month = 7
        elif year < latest_year:
            month = 12
        else:
            month = latest_month
        inpc_row = current.loc[current["anio"].eq(year) & current["mes"].eq(month)]
        if inpc_row.empty:
            historical = dynamic.loc[
                dynamic["anio"].eq(year) & dynamic["mes"].eq(month), "inpc_historico"
            ]
            if historical.empty:
                continue
            inpc_value = float(historical.iloc[-1])
        else:
            inpc_value = float(inpc_row.iloc[-1]["inpc"])
        ipcom_row = dynamic.loc[
            dynamic["anio"].eq(year) & dynamic["mes"].eq(month), "ipcom"
        ]
        ipcom_value = float(ipcom_row.iloc[-1]) if not ipcom_row.empty else np.nan
        records.append(
            {
                "etiqueta": f"{year}*" if year == 2024 else str(year),
                "anio": year,
                "mes_inpc": month,
                "periodo_inpc": f"{year}-{month:02d}",
                "inpc": inpc_value,
                "periodo_ipcom": f"{year}-{month:02d}" if not np.isnan(ipcom_value) else "",
                "ipcom": ipcom_value,
            }
        )
    result = pd.DataFrame.from_records(records)
    if result.empty or result["anio"].max() < 2026:
        raise ValueError("El conjunto vigente del INPC no contiene observaciones de 2026")
    return result


def _plot(data: pd.DataFrame, output_path: Path, project_root: Path) -> None:
    _configure_fonts(project_root)
    fig, ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(COLOR_BACKGROUND)
    x = np.arange(len(data), dtype=float)

    ax.plot(
        x,
        data["inpc"],
        color=COLOR_INPC,
        linewidth=2.2,
        marker="o",
        markersize=5.5,
        markeredgewidth=0,
        label="Índice Nacional de Precios al Consumidor (INPC)",
        zorder=4,
    )
    ax.plot(
        x,
        data["ipcom"],
        color=COLOR_IPCOM,
        linewidth=2.2,
        marker="o",
        markersize=5.5,
        markeredgewidth=0,
        label="Índice de Precios de Comunicaciones (IPCOM)",
        zorder=4,
    )

    for position, row in zip(x, data.itertuples(index=False), strict=True):
        inpc_offset = 12 if pd.isna(row.ipcom) or row.inpc >= row.ipcom else -16
        inpc_va = "bottom" if inpc_offset > 0 else "top"
        ax.annotate(
            f"{row.inpc:.0f}",
            xy=(position, row.inpc),
            xytext=(0, inpc_offset),
            textcoords="offset points",
            ha="center",
            va=inpc_va,
            fontsize=8,
            fontweight="bold",
            color=COLOR_TEXT,
            bbox={
                "boxstyle": "round,pad=0.3,rounding_size=0.8",
                "facecolor": "white",
                "edgecolor": COLOR_INPC,
                "linewidth": 0.8,
            },
            zorder=5,
        )
        if pd.notna(row.ipcom):
            ipcom_offset = -16 if row.inpc >= row.ipcom else 12
            ipcom_va = "top" if ipcom_offset < 0 else "bottom"
            ax.annotate(
                f"{row.ipcom:.0f}",
                xy=(position, row.ipcom),
                xytext=(0, ipcom_offset),
                textcoords="offset points",
                ha="center",
                va=ipcom_va,
                fontsize=8,
                fontweight="bold",
                color=COLOR_TEXT,
                bbox={
                    "boxstyle": "round,pad=0.3,rounding_size=0.8",
                    "facecolor": "white",
                    "edgecolor": COLOR_IPCOM,
                    "linewidth": 0.8,
                },
                zorder=5,
            )

    ax.set_ylim(60, 170)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
    ax.tick_params(axis="y", labelsize=9, colors=COLOR_TEXT, length=0)
    ax.set_xticks(x, data["etiqueta"], fontsize=9, color=COLOR_TEXT, fontweight="bold")
    ax.tick_params(axis="x", length=0, pad=8)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.add_artist(
        mpatches.FancyBboxPatch(
            (0.057, 0.918),
            0.007,
            0.018,
            transform=fig.transFigure,
            boxstyle="round,pad=0,rounding_size=0.002",
            facecolor=COLOR_IPCOM,
            edgecolor="none",
        )
    )
    fig.text(
        0.071,
        0.927,
        "Figura A.3.",
        fontsize=14,
        fontweight="bold",
        color=COLOR_TEXT,
        va="center",
    )
    fig.text(
        0.151,
        0.927,
        "Índices de precios (INPC e IPCOM)",
        fontsize=14,
        color=COLOR_TEXT,
        va="center",
    )
    fig.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 0.125),
        ncol=2,
        fontsize=9,
        frameon=False,
        labelcolor=COLOR_TEXT,
        handlelength=2.5,
        columnspacing=2.2,
    )

    latest = data.iloc[-1]
    latest_month = MONTH_NAME[int(latest["mes_inpc"])]
    source_body = (
        f"IFT con datos del INEGI a {latest_month} de {int(latest['anio'])}. "
        f"Datos disponibles en: {SOURCE_LANDING_PAGE}"
    )
    notes_body = (
        "Base segunda quincena de julio 2018 = 100. Los índices de 2010 a 2023 "
        "corresponden a diciembre y en 2024 a julio. Para 2025 se usa diciembre "
        f"y para 2026, {latest_month}. La serie IPCOM está disponible hasta julio de 2024."
    )
    fig.text(0.055, 0.079, "Fuente:", fontsize=8.1, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(
        0.094,
        0.079,
        textwrap.fill(source_body, width=205),
        fontsize=8.1,
        color=COLOR_TEXT,
        va="top",
    )
    fig.text(0.055, 0.047, "Notas:", fontsize=8.1, fontweight="bold", color=COLOR_TEXT, va="top")
    fig.text(
        0.091,
        0.047,
        textwrap.fill(notes_body, width=215),
        fontsize=8.1,
        color=COLOR_TEXT,
        va="top",
    )

    fig.subplots_adjust(left=0.074, right=0.96, top=0.83, bottom=0.25)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    apply_reference_ui(fig, FIGURE_ID); fig.savefig(output_path, dpi=200, facecolor="white", edgecolor="none")
    plt.close(fig)


def generate(context):
    print("  A.3 | Adquisición y verificación del CSV histórico INPC/IPCOM")
    dynamic_download = acquire_dynamic_source(context.project_root)
    dynamic = load_dynamic_series(dynamic_download.path)
    dynamic_latest = dynamic.iloc[-1]
    dynamic_period = f"{int(dynamic_latest['anio'])}-{int(dynamic_latest['mes']):02d}"
    context.register_raw_source(
        DYNAMIC_SOURCE_ID,
        dynamic_download.path,
        owner="INEGI",
        title="INPC e índice de la división Comunicaciones, serie previa a 2024",
        expected_period="2024-07",
        detected_period=dynamic_period,
        landing_page=SOURCE_LANDING_PAGE,
        exact_url=DYNAMIC_URL,
        cache_status=dynamic_download.cache_status,
        downloaded_at=dynamic_download.acquired_at,
        source_last_modified=dynamic_download.source_last_modified,
        content_type=dynamic_download.content_type,
    )

    print("  A.3 | Adquisición y verificación del conjunto mensual vigente del INPC")
    current_path = context.acquire_source(CURRENT_SOURCE_ID)
    current = load_current_inpc(current_path)
    current_latest = current.iloc[-1]
    current_period = f"{int(current_latest['anio'])}-{int(current_latest['mes']):02d}"
    context.record_source_period(CURRENT_SOURCE_ID, current_period, "AL_DIA")

    data = build_annual_series(dynamic, current)
    context.write_data_used(data)
    latest = data.iloc[-1]
    prior_year_same_month = current.loc[
        current["anio"].eq(int(latest["anio"]) - 1)
        & current["mes"].eq(int(latest["mes_inpc"]))
    ]
    if prior_year_same_month.empty:
        raise ValueError("No existe el mes comparable del año anterior para el INPC")
    prior_value = float(prior_year_same_month.iloc[-1]["inpc"])
    annual_variation = (float(latest["inpc"]) / prior_value - 1) * 100
    context.record_calculation(
        "variacion_anual_inpc",
        "(INPC último mes / INPC mismo mes año anterior - 1) * 100",
        {
            "periodo_ultimo": str(latest["periodo_inpc"]),
            "inpc_ultimo": round(float(latest["inpc"]), 6),
            "periodo_previo": f"{int(latest['anio']) - 1}-{int(latest['mes_inpc']):02d}",
            "inpc_previo": round(prior_value, 6),
        },
        round(annual_variation, 2),
        "porcentaje",
        2,
    )
    latest_ipcom = data.dropna(subset=["ipcom"]).iloc[-1]
    prior_ipcom = dynamic.loc[
        dynamic["anio"].eq(2023) & dynamic["mes"].eq(12), "ipcom"
    ].iloc[-1]
    ipcom_change = (float(latest_ipcom["ipcom"]) / float(prior_ipcom) - 1) * 100
    context.record_calculation(
        "variacion_ipcom_ultimo_corte",
        "(IPCOM julio 2024 / IPCOM diciembre 2023 - 1) * 100",
        {
            "ipcom_2024_07": round(float(latest_ipcom["ipcom"]), 6),
            "ipcom_2023_12": round(float(prior_ipcom), 6),
        },
        round(ipcom_change, 2),
        "porcentaje",
        2,
    )
    context.record_calculation(
        "ultimo_nivel_inpc",
        "última observación publicada del INPC",
        {"periodo": str(latest["periodo_inpc"])},
        round(float(latest["inpc"]), 3),
        "índice",
        3,
    )

    latest_month_name = MONTH_NAME[int(latest["mes_inpc"])]
    text_path = context.render_text(
        "a_3.md.j2",
        {
            "mes": latest_month_name,
            "anio": int(latest["anio"]),
            "inpc": float(latest["inpc"]),
            "variacion_anual": annual_variation,
            "ipcom": float(latest_ipcom["ipcom"]),
            "variacion_ipcom": ipcom_change,
        },
    )

    output_path = context.expected_figure_path
    print("  A.3 | Generación de gráfica PNG")
    _plot(data, output_path, context.project_root)
    print(f"  A.3 | Gráfica: {output_path}")
    return {
        "figure_path": str(output_path),
        "text_path": str(text_path),
        "detected_period": current_period,
        "rows_used": len(data),
        "dynamic_cache_status": dynamic_download.cache_status,
        "ipcom_last_period": str(latest_ipcom["periodo_ipcom"]),
        "latest_inpc": round(float(latest["inpc"]), 3),
        "annual_variation_inpc": round(annual_variation, 2),
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
