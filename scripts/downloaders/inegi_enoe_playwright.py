"""Adquisición reproducible de microdatos ENOE para la figura A.2.

Las direcciones directas oficiales son la vía principal. La navegación con
Playwright, adaptada del código proporcionado por el responsable, sólo se usa
como respaldo si INEGI cambia el comportamiento del enlace directo.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


LANDING_PAGE = "https://www.inegi.org.mx/programas/enoe/15ymas/#microdatos"
DOWNLOAD_BASE = "https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/microdatos"


@dataclass(frozen=True)
class QuarterSpec:
    year: int
    quarter: int
    filename: str

    @property
    def period(self) -> str:
        return f"{self.year}-T{self.quarter}"

    @property
    def source_id(self) -> str:
        return f"inegi_enoe_{self.year}_q{self.quarter}"

    @property
    def url(self) -> str:
        return f"{DOWNLOAD_BASE}/{self.filename}"


@dataclass(frozen=True)
class DownloadResult:
    spec: QuarterSpec
    path: Path
    cache_status: str
    acquired_at: str
    source_last_modified: str = ""
    content_type: str = "application/x-zip-compressed"


def _filename(year: int, quarter: int) -> str:
    if year <= 2019:
        return f"{year}trim{quarter}_csv.zip"
    if year == 2020 and quarter == 1:
        return "2020trim1_csv.zip"
    if year <= 2022:
        return f"enoe_n_{year}_trim{quarter}_csv.zip"
    return f"enoe_{year}_trim{quarter}_csv.zip"


def required_quarters() -> tuple[QuarterSpec, ...]:
    periods: list[tuple[int, int]] = []
    periods.extend((year, quarter) for year in range(2013, 2020) for quarter in (2, 4))
    periods.extend(((2020, 1), (2020, 4)))
    periods.extend((year, quarter) for year in range(2021, 2026) for quarter in (2, 4))
    periods.append((2026, 2))
    return tuple(
        QuarterSpec(year, quarter, _filename(year, quarter))
        for year, quarter in periods
    )


def verify_enoe_zip(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"ZIP ENOE ausente o vacío: {path}")
    try:
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                raise RuntimeError(f"ZIP ENOE dañado en {bad}: {path}")
            names = [name.upper() for name in archive.namelist()]
            if not any("SDEM" in name and name.endswith(".CSV") for name in names):
                raise RuntimeError(f"El ZIP no contiene SDEM: {path}")
            if not any("COE1" in name and name.endswith(".CSV") for name in names):
                raise RuntimeError(f"El ZIP no contiene COE1: {path}")
    except zipfile.BadZipFile as exc:
        raise RuntimeError(f"ZIP ENOE inválido: {path}") from exc


def _download_direct(spec: QuarterSpec, partial: Path) -> tuple[str, str]:
    request = urllib.request.Request(
        spec.url,
        headers={"User-Agent": "AnuarioEstadistico2026/0.3"},
    )
    print(f"    Descarga oficial: {spec.url}")
    with urllib.request.urlopen(request, timeout=180) as response, partial.open("wb") as stream:
        total = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        last_step = -1
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            stream.write(chunk)
            downloaded += len(chunk)
            step = int(downloaded * 20 / total) if total else -1
            if total and step != last_step:
                print(f"    Progreso: {int(downloaded * 100 / total):3d}%")
                last_step = step
            elif not total:
                print(f"    Progreso: {downloaded:,} bytes", end="\r", file=sys.stdout)
        return (
            response.headers.get("Last-Modified", ""),
            response.headers.get("Content-Type", "application/x-zip-compressed"),
        )


def _download_with_playwright(spec: QuarterSpec, partial: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "La descarga directa falló y Playwright no está instalado. "
            "Ejecuta .\\preparar_entorno.ps1 -ConPlaywright."
        ) from exc

    roman = {1: "I", 2: "II", 3: "III", 4: "IV"}[spec.quarter]
    headless = os.environ.get("ANUARIO_PLAYWRIGHT_HEADLESS", "1") != "0"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page(accept_downloads=True)
        page.goto(LANDING_PAGE, wait_until="domcontentloaded", timeout=180_000)
        row = page.get_by_role(
            "row",
            name=re.compile(rf"\b{roman}\s+Trimestre\b.*\b{spec.year}\b", re.IGNORECASE),
        ).first
        link = row.get_by_role("link", name=re.compile(r"descargar.*csv", re.IGNORECASE)).first
        with page.expect_download(timeout=180_000) as download_info:
            link.click()
        download_info.value.save_as(partial)
        browser.close()


def download(destination: Path, project_root: Path | None = None) -> list[DownloadResult]:
    """Obtiene sólo los ZIP faltantes y devuelve evidencia de cada periodo."""
    destination.mkdir(parents=True, exist_ok=True)
    legacy_dir = project_root.parent / "datos" / "A.2" if project_root else None
    force = os.environ.get("ANUARIO_FORCE_DOWNLOAD", "").strip().lower() in {
        "1",
        "true",
        "si",
        "sí",
    }
    offline = os.environ.get("ANUARIO_OFFLINE", "").strip().lower() in {
        "1",
        "true",
        "si",
        "sí",
    }
    specs = required_quarters()
    results: list[DownloadResult] = []

    for index, spec in enumerate(specs, start=1):
        target = destination / spec.filename
        print(f"  A.2 | Archivo {index:02d}/{len(specs)}: {spec.period}")
        if target.is_file() and not force:
            verify_enoe_zip(target)
            print(f"    Reutilizado: {target.name}")
            results.append(
                DownloadResult(
                    spec,
                    target,
                    "REUTILIZADO",
                    datetime.fromtimestamp(target.stat().st_mtime, tz=timezone.utc).isoformat(
                        timespec="seconds"
                    ),
                )
            )
            continue

        legacy = legacy_dir / spec.filename if legacy_dir else None
        if legacy and legacy.is_file() and not force:
            verify_enoe_zip(legacy)
            partial = target.with_suffix(target.suffix + ".part")
            print(f"    Copia local verificada: {legacy.name}")
            shutil.copy2(legacy, partial)
            verify_enoe_zip(partial)
            partial.replace(target)
            results.append(
                DownloadResult(
                    spec,
                    target,
                    "IMPORTADO_DESDE_COPIA_LOCAL",
                    datetime.fromtimestamp(legacy.stat().st_mtime, tz=timezone.utc).isoformat(
                        timespec="seconds"
                    ),
                )
            )
            continue

        if offline:
            raise RuntimeError(f"Falta {spec.filename} y ANUARIO_OFFLINE está activo")

        partial = target.with_suffix(target.suffix + ".part")
        partial.unlink(missing_ok=True)
        last_modified = ""
        content_type = "application/x-zip-compressed"
        try:
            last_modified, content_type = _download_direct(spec, partial)
        except Exception as direct_error:
            print(f"    Enlace directo no disponible; respaldo Playwright: {direct_error}")
            partial.unlink(missing_ok=True)
            _download_with_playwright(spec, partial)
        verify_enoe_zip(partial)
        partial.replace(target)
        results.append(
            DownloadResult(
                spec,
                target,
                "DESCARGADO_Y_VERIFICADO",
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                last_modified,
                content_type,
            )
        )

    return results
