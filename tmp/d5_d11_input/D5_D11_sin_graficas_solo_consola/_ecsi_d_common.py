from __future__ import annotations

import math
import re
import shutil
import urllib.request
from collections import OrderedDict
from pathlib import Path

import pandas as pd

# Rutas base
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "datos_ecsi"

# Fuente oficial
ECSI_PAGE_URL = "https://www.ift.org.mx/node/27269"
ECSI_CSV_URLS = [
    "https://www.ift.org.mx/sites/default/files/contenidogeneral/publicaciones/baseconfianzadigital.csv",
]


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _download(url: str, destination: Path, timeout: int = 90) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp, destination.open("wb") as f:
        shutil.copyfileobj(resp, f)


def _discover_csv_url_from_page() -> str | None:
    req = urllib.request.Request(ECSI_PAGE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    m = re.search(r'https?://[^"\']*baseconfianzadigital\.csv', html, flags=re.I)
    if m:
        return m.group(0)

    m = re.search(r'href=["\']([^"\']*baseconfianzadigital\.csv)["\']', html, flags=re.I)
    if m:
        href = m.group(1)
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            return "https://www.ift.org.mx" + href
    return None


def ensure_ecsi_csv(force_download: bool = False) -> Path:
    ensure_dirs()
    target = DATA_DIR / "baseconfianzadigital_ecsi_2024.csv"
    if target.exists() and not force_download:
        return target

    errors: list[str] = []
    candidate_urls = list(ECSI_CSV_URLS)

    try:
        discovered = _discover_csv_url_from_page()
        if discovered and discovered not in candidate_urls:
            candidate_urls.append(discovered)
    except Exception as exc:
        errors.append(f"No se pudo descubrir la URL desde la página ECSI: {exc}")

    for url in candidate_urls:
        try:
            _download(url, target)
            return target
        except Exception as exc:
            errors.append(f"{url} -> {exc}")

    raise RuntimeError(
        "No fue posible descargar la base oficial de la ECSI 2024. "
        "Intentos realizados:\n- " + "\n- ".join(errors)
    )


def load_ecsi(force_download: bool = False) -> pd.DataFrame:
    csv_path = ensure_ecsi_csv(force_download=force_download)
    return pd.read_csv(csv_path, low_memory=False)


def internet_users(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["rescate_internet"] == 1].copy()


def weighted_pct_binary(df: pd.DataFrame, var: str, weight_col: str = "fac_per") -> float:
    denom = float(df[weight_col].sum())
    if denom == 0:
        return float("nan")
    numer = float(df.loc[df[var] == 1, weight_col].sum())
    return round(numer / denom * 100, 1)


def weighted_distribution(
    df: pd.DataFrame,
    var: str,
    code_to_label: OrderedDict[int, str],
    *,
    weight_col: str = "fac_per",
    fill_missing_with: int | None = None,
    recode: dict[int, int] | None = None,
) -> OrderedDict[str, float]:
    data = df.copy()
    series = data[var].copy()

    if recode:
        series = series.replace(recode)
    if fill_missing_with is not None:
        series = series.fillna(fill_missing_with)

    data["__tmp__"] = series
    denom = float(data[weight_col].sum())

    out: OrderedDict[str, float] = OrderedDict()
    for code, label in code_to_label.items():
        if denom == 0:
            out[label] = float("nan")
        else:
            numer = float(data.loc[data["__tmp__"] == code, weight_col].sum())
            out[label] = round(numer / denom * 100, 1)
    return out


def max_abs_diff(actual: dict, expected: dict) -> float:
    diffs = []
    for key, expected_value in expected.items():
        if isinstance(expected_value, dict):
            diffs.append(max_abs_diff(actual.get(key, {}), expected_value))
        else:
            actual_value = actual.get(key)
            if actual_value is None or (
                isinstance(actual_value, float) and math.isnan(actual_value)
            ):
                diffs.append(float("inf"))
            else:
                diffs.append(abs(float(actual_value) - float(expected_value)))
    return max(diffs) if diffs else 0.0


def infer_grouped_security_model(
    df: pd.DataFrame,
    *,
    group_var: str,
    groups: OrderedDict[int, str],
    value_var: str,
    relevant_var: str | None,
    expected_2024: OrderedDict[str, OrderedDict[str, float]],
) -> dict:
    """Infiere el modelo de cálculo que mejor replica los valores de 2024."""
    candidate_models = [
        {
            "name": "usuarios_internet__1a4y9__fill_na_a_9",
            "universe": "internet_users",
            "code_map": OrderedDict([
                (1, "Muy seguro"),
                (2, "Seguro"),
                (3, "Ni seguro / Ni inseguro"),
                (4, "Inseguro"),
                (9, "NS/NR"),
            ]),
            "recode": None,
            "fill_missing_with": 9,
        },
        {
            "name": "usuarios_internet__1a4_y_5_a_9__fill_na_a_9",
            "universe": "internet_users",
            "code_map": OrderedDict([
                (1, "Muy seguro"),
                (2, "Seguro"),
                (3, "Ni seguro / Ni inseguro"),
                (4, "Inseguro"),
                (9, "NS/NR"),
            ]),
            "recode": {5: 9},
            "fill_missing_with": 9,
        },
        {
            "name": "solo_quienes_realizan_la_actividad__1a4y9__drop_na",
            "universe": "activity_users",
            "code_map": OrderedDict([
                (1, "Muy seguro"),
                (2, "Seguro"),
                (3, "Ni seguro / Ni inseguro"),
                (4, "Inseguro"),
                (9, "NS/NR"),
            ]),
            "recode": None,
            "fill_missing_with": None,
        },
        {
            "name": "solo_quienes_realizan_la_actividad__1a5__drop_na",
            "universe": "activity_users",
            "code_map": OrderedDict([
                (1, "Muy seguro"),
                (2, "Seguro"),
                (3, "Ni seguro / Ni inseguro"),
                (4, "Inseguro"),
                (5, "Muy inseguro"),
            ]),
            "recode": None,
            "fill_missing_with": None,
        },
    ]

    best: dict | None = None

    for model in candidate_models:
        if model["universe"] == "activity_users" and not relevant_var:
            continue

        base = internet_users(df)
        if model["universe"] == "activity_users":
            base = base[base[relevant_var] == 1].copy()  # type: ignore[index]

        table: OrderedDict[str, OrderedDict[str, float]] = OrderedDict()
        for group_code, group_label in groups.items():
            sub = base[base[group_var] == group_code].copy()
            table[group_label] = weighted_distribution(
                sub,
                value_var,
                model["code_map"],
                fill_missing_with=model["fill_missing_with"],
                recode=model["recode"],
            )

        trial = {
            "model": model,
            "table": table,
            "score_max_abs_diff": max_abs_diff(table, expected_2024),
        }
        if best is None or trial["score_max_abs_diff"] < best["score_max_abs_diff"]:
            best = trial

    if best is None:
        raise RuntimeError("No se pudo inferir un modelo válido.")
    return best


def infer_security_model_by_sex_with_total(
    df: pd.DataFrame,
    *,
    value_var: str,
    relevant_var: str | None,
    expected_2024: OrderedDict[str, OrderedDict[str, float]],
) -> dict:
    """Infiere el modelo de cálculo y devuelve Total, Mujeres y Hombres."""
    candidate_models = [
        {
            "name": "usuarios_internet__1a4y9__fill_na_a_9",
            "universe": "internet_users",
            "code_map": OrderedDict([
                (1, "Muy seguro"),
                (2, "Seguro"),
                (3, "Ni seguro / Ni inseguro"),
                (4, "Inseguro"),
                (9, "NS/NR"),
            ]),
            "recode": None,
            "fill_missing_with": 9,
        },
        {
            "name": "usuarios_internet__1a4_y_5_a_9__fill_na_a_9",
            "universe": "internet_users",
            "code_map": OrderedDict([
                (1, "Muy seguro"),
                (2, "Seguro"),
                (3, "Ni seguro / Ni inseguro"),
                (4, "Inseguro"),
                (9, "NS/NR"),
            ]),
            "recode": {5: 9},
            "fill_missing_with": 9,
        },
        {
            "name": "solo_quienes_realizan_la_actividad__1a4y9__drop_na",
            "universe": "activity_users",
            "code_map": OrderedDict([
                (1, "Muy seguro"),
                (2, "Seguro"),
                (3, "Ni seguro / Ni inseguro"),
                (4, "Inseguro"),
                (9, "NS/NR"),
            ]),
            "recode": None,
            "fill_missing_with": None,
        },
    ]

    best: dict | None = None
    sex_groups = OrderedDict([(2, "Hombres"), (1, "Mujeres")])

    for model in candidate_models:
        if model["universe"] == "activity_users" and not relevant_var:
            continue

        base = internet_users(df)
        if model["universe"] == "activity_users":
            base = base[base[relevant_var] == 1].copy()  # type: ignore[index]

        base = base[base["sexo"].isin([1, 2])].copy()

        table: OrderedDict[str, OrderedDict[str, float]] = OrderedDict()
        table["Total"] = weighted_distribution(
            base,
            value_var,
            model["code_map"],
            fill_missing_with=model["fill_missing_with"],
            recode=model["recode"],
        )

        for sex_code, sex_label in sex_groups.items():
            sub = base[base["sexo"] == sex_code].copy()
            table[sex_label] = weighted_distribution(
                sub,
                value_var,
                model["code_map"],
                fill_missing_with=model["fill_missing_with"],
                recode=model["recode"],
            )

        trial = {
            "model": model,
            "table": table,
            "score_max_abs_diff": max_abs_diff(table, expected_2024),
        }
        if best is None or trial["score_max_abs_diff"] < best["score_max_abs_diff"]:
            best = trial

    if best is None:
        raise RuntimeError("No se pudo inferir un modelo válido para la figura D.11.")
    return best
