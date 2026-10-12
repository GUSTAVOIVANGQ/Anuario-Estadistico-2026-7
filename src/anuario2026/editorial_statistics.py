"""Puntos clave económicos calculados con cortes y unidades explícitos."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


def annual_income(frame: pd.DataFrame, year: int) -> dict:
    rows = frame.loc[frame["anio"].isin([year - 1, year])].copy()
    if rows.duplicated(["anio", "trimestre"]).any():
        raise ValueError("Los ingresos contienen trimestres duplicados")
    amounts = {}
    for observed in (year - 1, year):
        selected = rows.loc[rows["anio"] == observed]
        if set(selected["trimestre"]) != {1, 2, 3, 4}:
            raise ValueError(f"Faltan trimestres de ingresos para {observed}")
        values = pd.to_numeric(selected["ingresos_miles_millones_pesos"], errors="raise")
        if values.isna().any() or (values < 0).any():
            raise ValueError("Ingresos incompletos o negativos")
        amounts[observed] = float(values.sum())
    if amounts[year - 1] <= 0:
        raise ValueError("La base anual de ingresos debe ser positiva")
    return {"year": year, "value_mmdp": amounts[year], "previous_mmdp": amounts[year - 1],
            "annual_growth_pct": (amounts[year] / amounts[year - 1] - 1) * 100,
            "method": "Suma de los cuatro trimestres; variación respecto al año anterior."}


def quarterly_gdp(frame: pd.DataFrame, year: int) -> dict:
    amounts = {}
    for observed in (year - 1, year):
        selected = frame.loc[(frame["anio"] == observed) & (frame["trimestre"] == 4)]
        if len(selected) != 1:
            raise ValueError(f"Se requiere un único PIB TyR para {observed}-T4")
        value = float(selected.iloc[0]["tyr_miles_millones_pesos"])
        if not pd.notna(value) or value <= 0:
            raise ValueError("El PIB TyR debe ser positivo y estar disponible")
        amounts[observed] = value
    return {"year": year, "quarter": 4, "value_mmdp": amounts[year],
            "previous_mmdp": amounts[year - 1],
            "annual_growth_pct": (amounts[year] / amounts[year - 1] - 1) * 100,
            "method": "TyR = ramas 515 + 517; T4 contra T4 anterior, precios de 2018."}


def calculate_highlights(root: Path, revision: dict, run_dir: Path | None = None) -> dict:
    results = {}
    settings = revision.get("economic_highlights", {})
    for key, calculator, figure in (
        ("income", annual_income, "a_6"), ("gdp", quarterly_gdp, "a_1"),
    ):
        if key not in settings:
            continue
        spec = settings[key]
        year = int(spec["year"])
        path = root / spec["data_file"]
        # Usa los datos de la corrida cuando cubren el periodo solicitado.
        # Un corte incompleto no sustituye la serie completa verificada.
        if run_dir:
            candidate = run_dir / "datos_usados" / f"{figure}_datos_usados.csv"
            if candidate.is_file():
                frame = pd.read_csv(candidate)
                try:
                    calculator(frame, year)
                except (ValueError, KeyError):
                    pass
                else:
                    path = candidate
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if path == root / spec["data_file"] and digest != spec["data_sha256"]:
            raise ValueError(f"Cambió la fuente editorial verificada: {path}")
        result = calculator(pd.read_csv(path), year)
        result.update({"data_file": str(path), "data_sha256": digest,
                       "source_url": spec["source_url"], "original_source_sha256": spec["original_source_sha256"]})
        if key == "income":
            text = (f"En {year}, los ingresos de las empresas del sector de telecomunicaciones "
                    f"ascendieron a **{result['value_mmdp']:.0f} mil millones de pesos**, "
                    f"lo que representó un crecimiento anual de **{result['annual_growth_pct']:.1f}%**."
                    f"\n\nFuente: BIT, datos de los operadores de telecomunicaciones, {year}.")
        else:
            text = (f"Al cuarto trimestre de {year}, el PIB de los sectores de telecomunicaciones "
                    f"y radiodifusión (TyR) se ubicó en **{result['value_mmdp']:.0f} mil millones de pesos**, "
                    f"con un crecimiento anual de **{result['annual_growth_pct']:.1f}%**."
                    "\n\nFuente: INEGI, SCNM. Precios de 2018.")
        result["text"] = text
        results[key] = result
    return results
