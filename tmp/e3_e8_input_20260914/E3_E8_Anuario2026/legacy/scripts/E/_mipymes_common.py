# -*- coding: utf-8 -*-
"""Utilidades comunes para Figuras E.3-E.8 (Anuario Estadístico 2026).

Descarga y procesa las bases oficiales de la Cuarta Encuesta a MiPymes del IFT.
La interfaz pública de los scripts se conserva: basta ejecutar cada figura con Python.
"""
from __future__ import annotations

import math
import re
import shutil
import unicodedata
import urllib.request
import zipfile
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

OFFICIAL = {
    2022: {
        "page": "https://www.ift.org.mx/usuarios-y-audiencias/cuarta-encuesta-2022-micro-pequenas-y-medianas-empresas",
        "zip": "https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/bd4taencuesta2022.zip",
    },
    2023: {
        "page": "https://www.ift.org.mx/usuarios-y-audiencias/cuarta-encuesta-2023-micro-pequenas-y-medianas-empresas",
        "zip": "https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/bd4taencuesta2023.zip",
    },
    2024: {
        "page": "https://www.ift.org.mx/node/26777",
        "zip": "https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/basededatoscuartaencuesta2024mipymes.zip",
    },
}


def project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if parent.name.lower() == "legacy":
            return parent.parent
    # legacy/scripts/E/file.py -> project root = parents[3]
    return here.parents[3]


PROJECT_ROOT = project_root()
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "ift_mipymes"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "output"


def _norm(x) -> str:
    s = str(x).replace("\xa0", " ").replace("\n", " ")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _download_requests(url: str, target: Path) -> None:
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("requests no está instalado") from exc
    with requests.get(url, stream=True, timeout=120, headers={"User-Agent": "Mozilla/5.0"}) as r:
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or "").lower()
        if "text/html" in ctype:
            raise RuntimeError(f"La URL devolvió HTML en lugar del ZIP ({ctype})")
        with target.open("wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)


def _download_urllib(url: str, target: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, target.open("wb") as f:
        shutil.copyfileobj(resp, f)


def _download_playwright(year: int, target: Path) -> None:
    """Fallback mediante Playwright, siguiendo la página pública del IFT."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Falló la descarga HTTP y Playwright no está instalado. Instale con: pip install playwright && playwright install chromium"
        ) from exc

    page_url = OFFICIAL[year]["page"]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(accept_downloads=True)
        page.goto(page_url, wait_until="domcontentloaded", timeout=120000)
        links = page.locator("a")
        chosen = None
        for i in range(links.count()):
            a = links.nth(i)
            text = _norm(a.inner_text())
            href = a.get_attribute("href") or ""
            if ("base" in text and "datos" in text) or href.lower().endswith(".zip"):
                chosen = a
                break
        if chosen is None:
            browser.close()
            raise RuntimeError(f"No se encontró el enlace de Base de Datos en {page_url}")
        try:
            with page.expect_download(timeout=120000) as info:
                chosen.click()
            info.value.save_as(str(target))
        finally:
            browser.close()


def ensure_zip(year: int) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    target = RAW_DIR / f"cuarta_encuesta_mipymes_{year}.zip"
    if target.exists() and target.stat().st_size > 1024:
        try:
            with zipfile.ZipFile(target) as zf:
                zf.testzip()
            return target
        except Exception:
            target.unlink(missing_ok=True)

    url = OFFICIAL[year]["zip"]
    errors = []
    for fn in (_download_requests, _download_urllib):
        try:
            fn(url, target)
            with zipfile.ZipFile(target) as zf:
                zf.testzip()
            print(f"Descarga oficial {year}: {url}")
            return target
        except Exception as exc:
            errors.append(f"{fn.__name__}: {exc}")
            target.unlink(missing_ok=True)
    try:
        _download_playwright(year, target)
        with zipfile.ZipFile(target) as zf:
            zf.testzip()
        print(f"Descarga oficial {year} mediante Playwright: {OFFICIAL[year]['page']}")
        return target
    except Exception as exc:
        errors.append(f"Playwright: {exc}")
        target.unlink(missing_ok=True)
        raise RuntimeError(
            f"No fue posible descargar la base oficial MiPymes {year}.\n"
            f"Página: {OFFICIAL[year]['page']}\nZIP: {url}\n" + "\n".join(errors)
        )


def extract_workbook(year: int) -> Path:
    zip_path = ensure_zip(year)
    dest = RAW_DIR / str(year)
    dest.mkdir(parents=True, exist_ok=True)
    existing = list(dest.rglob("*.xlsx")) + list(dest.rglob("*.xls"))
    if existing:
        return _choose_workbook(existing)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)
    candidates = list(dest.rglob("*.xlsx")) + list(dest.rglob("*.xls"))
    if not candidates:
        raise FileNotFoundError(f"El ZIP oficial {year} no contiene una hoja Excel reconocible.")
    return _choose_workbook(candidates)


def _choose_workbook(paths: Sequence[Path]) -> Path:
    def score(p: Path):
        n = _norm(p.name)
        s = 0
        if "base" in n: s += 100
        if "datos" in n: s += 50
        if "encuesta" in n: s += 20
        if "diccionario" in n: s -= 100
        return (s, p.stat().st_size)
    return max(paths, key=score)


def load_year(year: int) -> pd.DataFrame:
    path = extract_workbook(year)
    print(f"Base {year}: {path}")
    return pd.read_excel(path, engine="openpyxl" if path.suffix.lower() == ".xlsx" else None)


def find_column(
    df: pd.DataFrame,
    required: Iterable[str] = (),
    any_groups: Iterable[Iterable[str]] = (),
    prefer: Iterable[str] = (),
    reject: Iterable[str] = (),
) -> str:
    req = [_norm(x) for x in required]
    groups = [[_norm(x) for x in g] for g in any_groups]
    pref = [_norm(x) for x in prefer]
    rej = [_norm(x) for x in reject]
    choices = []
    for col in df.columns:
        n = _norm(col)
        if any(x not in n for x in req):
            continue
        if any(not any(opt in n for opt in grp) for grp in groups):
            continue
        if any(x in n for x in rej):
            continue
        score = sum(5 for x in pref if x in n) - len(n) / 10000
        choices.append((score, str(col)))
    if not choices:
        raise KeyError(
            f"No se encontró columna. required={list(required)}, any_groups={list(any_groups)}, prefer={list(prefer)}"
        )
    choices.sort(reverse=True)
    return choices[0][1]


def size_col(df: pd.DataFrame) -> str:
    try:
        return find_column(df, required=["clasificacion", "empresa"], any_groups=[["tamano", "tamaño"]])
    except Exception:
        return find_column(df, any_groups=[["tamano", "tamaño"]], prefer=["clasificacion", "empresa"])


def factor_col(df: pd.DataFrame) -> str:
    cols = []
    for c in df.columns:
        n = _norm(c)
        if "factor" in n and ("expansion" in n or "ponder" in n):
            score = (10 if "final" in n else 0) + (3 if "normalizado" not in n else 0)
            cols.append((score, str(c)))
    if not cols:
        raise KeyError("No se encontró el factor de expansión/ponderación.")
    return max(cols)[1]


def resolve_size_value(df: pd.DataFrame, label: str) -> object:
    col = size_col(df)
    key = _norm(label)
    for v in df[col].dropna().unique():
        if key[:4] in _norm(v):
            return v
    raise KeyError(f"No se encontró tamaño {label} en {col}")


def yes_mask(series: pd.Series) -> pd.Series:
    nums = pd.to_numeric(series, errors="coerce")
    texts = series.astype(str).map(_norm)
    return nums.eq(1) | texts.isin({"si", "s", "yes"}) | texts.str.startswith("si ")


def weighted_yes_pct(df: pd.DataFrame, col: str, weight: str) -> float:
    tmp = df[[col, weight]].dropna(subset=[col, weight]).copy()
    den = pd.to_numeric(tmp[weight], errors="coerce").fillna(0).sum()
    if den == 0:
        return 0.0
    num = pd.to_numeric(tmp.loc[yes_mask(tmp[col]), weight], errors="coerce").fillna(0).sum()
    return float(num / den * 100)


def weighted_mean(df: pd.DataFrame, value_col: str, weight_col: str) -> float:
    tmp = df[[value_col, weight_col]].copy()
    bad = tmp[value_col].astype(str).map(_norm).isin({"ns nc", "ns nr", "no sabe", "no sabe no contesto", "nan"})
    tmp = tmp[~bad]
    tmp[value_col] = pd.to_numeric(tmp[value_col], errors="coerce")
    tmp[weight_col] = pd.to_numeric(tmp[weight_col], errors="coerce")
    tmp = tmp.dropna()
    if tmp.empty or tmp[weight_col].sum() == 0:
        return float("nan")
    return float((tmp[value_col] * tmp[weight_col]).sum() / tmp[weight_col].sum())


def weighted_igs(df: pd.DataFrame, service: str) -> float:
    """IGS = promedio ponderado 0/25/50/75/100, según metodología IFT 2024."""
    w = factor_col(df)
    svc_tokens = ["internet"] if service == "internet" else ["telefon", "fija"]
    # Primero buscar una columna recodificada.
    try:
        col = find_column(
            df,
            required=["satisfech"],
            any_groups=[[svc_tokens[0]], svc_tokens[1:] or svc_tokens],
            prefer=["recodificada", "recodificado"],
        )
    except Exception:
        col = find_column(df, required=["satisfech"], any_groups=[svc_tokens])

    s = df[col]
    numeric = pd.to_numeric(s, errors="coerce")
    vals = set(numeric.dropna().round(5).unique())
    if vals and max(vals) <= 100 and any(v in vals for v in [0, 25, 50, 75, 100]):
        tmp = df.copy()
        tmp["__igs__"] = numeric
        return weighted_mean(tmp, "__igs__", w)

    mapping = {
        "totalmente insatisfecho": 0,
        "insatisfecho": 25,
        "ni satisfecho ni insatisfecho": 50,
        "satisfecho": 75,
        "totalmente satisfecho": 100,
    }
    tmp = df.copy()
    tmp["__igs__"] = s.astype(str).map(_norm).map(mapping)
    return weighted_mean(tmp, "__igs__", w)


def by_sizes(df: pd.DataFrame, calc, include_general=True):
    sc = size_col(df)
    out = {}
    if include_general:
        out["General"] = calc(df)
    for label in ["Micro", "Pequeña", "Mediana"]:
        actual = resolve_size_value(df, label)
        out[label] = calc(df[df[sc] == actual])
    return out


def validate(name: str, actual, expected, tolerance: float = 0.15) -> None:
    """Valida recursivamente números del Anuario/Reporte oficial."""
    errors = []
    def walk(a, e, path=""):
        if isinstance(e, dict):
            for k, v in e.items():
                if k not in a:
                    errors.append(f"{path}/{k}: faltante")
                else:
                    walk(a[k], v, f"{path}/{k}")
        else:
            try:
                av = float(a); ev = float(e)
                if not math.isfinite(av) or abs(av - ev) > tolerance:
                    errors.append(f"{path}: calculado={av:.3f}, esperado={ev:.3f}")
            except Exception:
                errors.append(f"{path}: valor no numérico {a!r}")
    walk(actual, expected)
    if errors:
        raise AssertionError(f"Validación {name} falló:\n" + "\n".join(errors))
    print(f"VALIDACIÓN OK: {name}")


def save_audit(fig_id: str, data: pd.DataFrame) -> Path:
    out_dir = PROCESSED_DIR / fig_id
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"datos_{fig_id.lower().replace('.', '_')}_actualizados.csv"
    data.to_csv(path, index=False, encoding="utf-8-sig")
    return path
