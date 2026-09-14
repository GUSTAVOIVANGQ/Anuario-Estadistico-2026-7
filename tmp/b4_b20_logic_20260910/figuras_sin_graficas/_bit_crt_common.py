# -*- coding: utf-8 -*-
"""Utilidades de descarga y trazabilidad para las figuras B.4-B.20.

No requiere argumentos. Los scripts buscan primero archivos ya descargados y,
si faltan, intentan obtener la tabla individual o TODO.zip del BIT/CRT.
"""
from __future__ import annotations

import hashlib
import io
import os
import re
import shutil
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd

CRT_PORTAL = "https://bit.crt.gob.mx/BitWebApp/descargaDatos.xhtml"
CRT_TODO_URL = "https://bit.crt.gob.mx/descargas/datos/tabs/TODO.zip"
CRT_METADATA_URL = "https://bit.crt.gob.mx/descargas/datos/tabs/METADATOS.zip"
GEOJSON_URL = "https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json"


def repo_root(start: Path | None = None) -> Path:
    p = (start or Path(__file__)).resolve()
    for parent in [p.parent, *p.parents]:
        if (parent / "scripts").is_dir() and ((parent / "config").is_dir() or (parent / "datos").exists()):
            return parent
    return p.parent


ROOT = repo_root()
BIT_RAW_DIR = ROOT / "datos" / "BIT" / "origen"
BIT_TABLE_DIR = ROOT / "datos" / "BIT" / "tablas"
OUTPUT_DIR = ROOT / "output"
BIT_RAW_DIR.mkdir(parents=True, exist_ok=True)
BIT_TABLE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TODO_PATH = BIT_RAW_DIR / "CRT_BIT_TODO.zip"
METADATA_PATH = BIT_RAW_DIR / "CRT_BIT_METADATOS.zip"


def read_csv_flexible(path_or_buffer, **kwargs) -> pd.DataFrame:
    last = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            if hasattr(path_or_buffer, "seek"):
                path_or_buffer.seek(0)
            return pd.read_csv(path_or_buffer, encoding=enc, low_memory=False, **kwargs)
        except Exception as exc:
            last = exc
    raise RuntimeError(f"No fue posible leer CSV: {last}")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().upper() for c in out.columns]
    return out


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )


def sha256_file(path: Path, chunk=1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _zip_has(path: Path, filename: str) -> bool:
    if not path.exists() or not zipfile.is_zipfile(path):
        return False
    target = Path(filename).name.lower()
    try:
        with zipfile.ZipFile(path) as zf:
            return any(Path(n).name.lower() == target for n in zf.namelist())
    except Exception:
        return False


def _extract_from_zip(zip_path: Path, filename: str, dest: Path) -> Path | None:
    if not _zip_has(zip_path, filename):
        return None
    target = Path(filename).name.lower()
    with zipfile.ZipFile(zip_path) as zf:
        member = next(n for n in zf.namelist() if Path(n).name.lower() == target)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(member) as src, dest.open("wb") as dst:
            shutil.copyfileobj(src, dst)
    return dest


def _find_existing_file(filename: str) -> Path | None:
    candidates = [BIT_TABLE_DIR / filename]
    for p in candidates:
        if p.exists() and p.stat().st_size > 100:
            return p
    for base in (ROOT / "datos", ROOT / "data" / "raw"):
        if not base.exists():
            continue
        try:
            for p in base.rglob(filename):
                if p.is_file() and p.stat().st_size > 100:
                    return p
        except OSError:
            pass
    return None


def _find_existing_todo(required: str | None = None) -> Path | None:
    candidates = [
        TODO_PATH,
        ROOT / "datos" / "A.4" / "CRT_BIT_TODO.zip",
        ROOT / "datos" / "BIT" / "CRT_BIT_TODO.zip",
    ]
    for p in candidates:
        if p.exists() and zipfile.is_zipfile(p) and (required is None or _zip_has(p, required)):
            return p
    for base in (ROOT / "datos", ROOT / "data" / "raw"):
        if not base.exists():
            continue
        for pat in ("*TODO*.zip", "*todo*.zip"):
            try:
                for p in base.rglob(pat):
                    if zipfile.is_zipfile(p) and (required is None or _zip_has(p, required)):
                        return p
            except OSError:
                pass
    return None


def _write_links(figure_id: str, filenames: list[str]) -> None:
    d = ROOT / "datos" / figure_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "ENLACES_DESCARGA.txt").write_text(
        f"Figura {figure_id}\n\nPortal BIT/CRT:\n{CRT_PORTAL}\n\n"
        f"Descarga global TODO.zip:\n{CRT_TODO_URL}\n\n"
        f"Metadatos:\n{CRT_METADATA_URL}\n\n"
        "Tablas requeridas:\n" + "\n".join(filenames) + "\n",
        encoding="utf-8",
    )


def _try_direct_with_urllib(filename: str, dest: Path) -> bool:
    urls = [
        f"https://bit.crt.gob.mx/descargas/datos/tabs/{filename}",
        f"https://bit.crt.gob.mx/descargas/datos/tabs/{Path(filename).stem}.zip",
    ]
    headers = {"User-Agent": "Mozilla/5.0", "Referer": CRT_PORTAL}
    for url in urls:
        tmp = dest.with_suffix(dest.suffix + ".part")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=90) as resp, tmp.open("wb") as f:
                shutil.copyfileobj(resp, f)
            if url.lower().endswith(".csv"):
                head = tmp.read_bytes()[:1024].lower()
                if tmp.stat().st_size > 100 and not head.lstrip().startswith(b"<html"):
                    tmp.replace(dest)
                    return True
            elif zipfile.is_zipfile(tmp) and _zip_has(tmp, filename):
                _extract_from_zip(tmp, filename, dest)
                tmp.unlink(missing_ok=True)
                return True
        except Exception:
            tmp.unlink(missing_ok=True)
    return False


def _download_todo_playwright(required: str) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "No está Playwright. Instala con: pip install playwright && "
            "python -m playwright install chromium"
        ) from exc

    with sync_playwright() as pw:
        # Intento por APIRequestContext, guardando streaming solo si es razonable.
        request = pw.request.new_context(ignore_https_errors=True, extra_http_headers={"User-Agent": "Mozilla/5.0", "Referer": CRT_PORTAL})
        try:
            for url in (
                f"https://bit.crt.gob.mx/descargas/datos/tabs/{required}",
                f"https://bit.crt.gob.mx/descargas/datos/tabs/{Path(required).stem}.zip",
            ):
                try:
                    resp = request.get(url, timeout=120_000)
                    body = resp.body()
                    if url.endswith(".csv") and len(body) > 100 and not body.lstrip().lower().startswith(b"<html"):
                        dest = BIT_TABLE_DIR / required
                        dest.write_bytes(body)
                        return TODO_PATH
                    if body[:2] == b"PK":
                        ztmp = BIT_RAW_DIR / f"{Path(required).stem}.zip"
                        ztmp.write_bytes(body)
                        if _zip_has(ztmp, required):
                            _extract_from_zip(ztmp, required, BIT_TABLE_DIR / required)
                            return ztmp
                except Exception:
                    pass
        finally:
            request.dispose()

        browser = pw.chromium.launch(headless=True)
        try:
            context = browser.new_context(accept_downloads=True, ignore_https_errors=True)
            page = context.new_page()
            page.goto(CRT_PORTAL, wait_until="domcontentloaded", timeout=120_000)
            page.wait_for_timeout(2500)

            stem = Path(required).stem.lower()
            for sel in (f"a[href*='{required}']", f"a[href*='{stem}']"):
                loc = page.locator(sel)
                if loc.count():
                    href = loc.first.get_attribute("href")
                    if href:
                        try:
                            r = context.request.get(urljoin(page.url, href), timeout=180_000)
                            body = r.body()
                            if len(body) > 100 and not body.lstrip().lower().startswith(b"<html"):
                                dest = BIT_TABLE_DIR / required
                                if body[:2] == b"PK":
                                    ztmp = BIT_RAW_DIR / f"{Path(required).stem}.zip"
                                    ztmp.write_bytes(body)
                                    if _extract_from_zip(ztmp, required, dest):
                                        return ztmp
                                else:
                                    dest.write_bytes(body)
                                    return TODO_PATH
                        except Exception:
                            pass

            todo = page.locator("a[href*='TODO.zip']")
            if todo.count() == 0:
                todo = page.get_by_text(re.compile(r"DESCARGAR\s+TODO", re.I))
            if todo.count() == 0:
                raise RuntimeError("No se encontró el enlace TODO.zip en el portal BIT/CRT")
            print("Descargando TODO.zip del BIT/CRT. Puede superar 1 GB; sólo se hace si no hay copia local.")
            with page.expect_download(timeout=900_000) as info:
                todo.first.click(force=True)
            dl = info.value
            dl.save_as(str(TODO_PATH))
        finally:
            browser.close()

    if not zipfile.is_zipfile(TODO_PATH):
        raise RuntimeError(f"La descarga no es un ZIP válido: {TODO_PATH}")
    return TODO_PATH


def ensure_bit_table(filename: str, figure_id: str = "BIT") -> Path:
    _write_links(figure_id, [filename])
    existing = _find_existing_file(filename)
    if existing:
        return existing

    todo = _find_existing_todo(filename)
    if todo:
        dest = BIT_TABLE_DIR / filename
        if _extract_from_zip(todo, filename, dest):
            return dest

    dest = BIT_TABLE_DIR / filename
    if _try_direct_with_urllib(filename, dest):
        return dest

    _download_todo_playwright(filename)
    if dest.exists() and dest.stat().st_size > 100:
        return dest
    todo = _find_existing_todo(filename)
    if todo and _extract_from_zip(todo, filename, dest):
        return dest
    raise RuntimeError(
        f"No se encontró {filename}. Descarga TODO.zip desde {CRT_PORTAL} y colócalo en {TODO_PATH}."
    )


def ensure_bit_table_any(candidates: list[str], figure_id: str, keywords: tuple[str, ...] = ()) -> Path:
    _write_links(figure_id, candidates)
    for name in candidates:
        p = _find_existing_file(name)
        if p:
            return p
        todo = _find_existing_todo(name)
        if todo:
            dest = BIT_TABLE_DIR / name
            if _extract_from_zip(todo, name, dest):
                return dest
    # Si ya existe TODO.zip, descubrir nombre por palabras clave.
    todo = _find_existing_todo()
    if todo and keywords:
        with zipfile.ZipFile(todo) as zf:
            matches = [n for n in zf.namelist() if n.lower().endswith(".csv") and all(k.lower() in Path(n).name.lower() for k in keywords)]
            if len(matches) == 1:
                name = Path(matches[0]).name
                dest = BIT_TABLE_DIR / name
                _extract_from_zip(todo, name, dest)
                return dest
            if len(matches) > 1:
                # Preferir histórico y telefonía fija.
                matches = sorted(matches, key=lambda n: ("hist" not in n.lower(), len(n)))
                name = Path(matches[0]).name
                dest = BIT_TABLE_DIR / name
                _extract_from_zip(todo, name, dest)
                return dest
    # Forzar descarga global con el primer candidato y volver a descubrir.
    _download_todo_playwright(candidates[0])
    for name in candidates:
        p = _find_existing_file(name)
        if p:
            return p
        if _zip_has(TODO_PATH, name):
            dest = BIT_TABLE_DIR / name
            _extract_from_zip(TODO_PATH, name, dest)
            return dest
    if keywords and zipfile.is_zipfile(TODO_PATH):
        with zipfile.ZipFile(TODO_PATH) as zf:
            matches = [n for n in zf.namelist() if n.lower().endswith(".csv") and all(k.lower() in Path(n).name.lower() for k in keywords)]
            if matches:
                matches = sorted(matches, key=lambda n: ("hist" not in n.lower(), len(n)))
                name = Path(matches[0]).name
                dest = BIT_TABLE_DIR / name
                _extract_from_zip(TODO_PATH, name, dest)
                return dest
    raise RuntimeError("No se encontró una tabla BIT compatible. Candidatos: " + ", ".join(candidates))


def latest_december_year(df: pd.DataFrame, year_col="ANIO", month_col="MES") -> int:
    y = numeric(df[year_col])
    m = numeric(df[month_col])
    years = y[m == 12].dropna().astype(int)
    if years.empty:
        raise ValueError("La tabla no contiene observaciones de diciembre (MES=12).")
    return int(years.max())


def latest_year(df: pd.DataFrame, year_col="ANIO") -> int:
    y = numeric(df[year_col]).dropna().astype(int)
    if y.empty:
        raise ValueError("La tabla no contiene años válidos.")
    return int(y.max())


def ensure_geojson() -> Path:
    candidates = [ROOT / "datos" / "mexico.json", ROOT / "mexico.json"]
    for p in candidates:
        if p.exists() and p.stat().st_size > 1000:
            return p
    dest = ROOT / "datos" / "mexico.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(GEOJSON_URL, dest)
    except Exception as exc:
        raise RuntimeError(
            f"No se pudo descargar el mapa. Descárgalo de {GEOJSON_URL} y guárdalo en {dest}"
        ) from exc
    return dest


def save_audit(figure_id: str, df: pd.DataFrame, suffix="resultados") -> Path:
    d = ROOT / "datos" / figure_id
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{suffix}_{figure_id.lower().replace('.', '')}.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path
