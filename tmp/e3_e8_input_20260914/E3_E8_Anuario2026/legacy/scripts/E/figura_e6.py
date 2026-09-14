# -*- coding: utf-8 -*-
"""Figura E.6 — Beneficios de vender a través de Internet fijo.

Versión sin gráfica: calcula, valida e imprime en consola los datos que
originalmente se utilizaban para generar la figura.
"""
from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _mipymes_common import (
    load_year,
    factor_col,
    size_col,
    resolve_size_value,
    find_column,
    yes_mask,
    validate,
    _norm,
)

CATS = [
    "Incremento de ventas",
    "Ampliar canales de venta",
    "Inclusión de marketing digital",
    "La rapidez en la que se realizan las ventas o compras",
    "Otro",
]
SIZES = ["General", "Micro", "Pequeña", "Mediana"]
EXPECTED_2024 = {
    "General": [65.7, 17.2, 6.7, 8.1, 1.2],
    "Micro": [66.2, 16.9, 6.4, 8.0, 1.2],
    "Pequeña": [57.2, 20.8, 11.4, 9.5, 0.6],
    "Mediana": [60.2, 20.1, 8.0, 9.2, 1.4],
}


def calc(df):
    w = factor_col(df)
    sc = size_col(df)
    sell = find_column(
        df,
        required=["vender"],
        any_groups=[["producto", "servicio"]],
        prefer=["internet"],
        reject=["beneficio"],
    )
    benefit = find_column(
        df,
        required=["principal", "beneficio"],
        any_groups=[["venda", "venta", "vender"]],
        prefer=["internet"],
    )
    sellers = df[yes_mask(df[sell])].copy()
    out = {}

    for size in SIZES:
        sub = sellers if size == "General" else sellers[sellers[sc] == resolve_size_value(df, size)]
        den = pd.to_numeric(sub[w], errors="coerce").fillna(0).sum()
        vals = []
        cm = sub[benefit].astype(str).map(_norm)

        for cat in CATS:
            if cat == "Otro":
                mask = cm.str.startswith("otro")
            elif cat.startswith("La rapidez"):
                mask = cm.str.contains("rapidez") | (cm.str.contains("rapida") & cm.str.contains("venta"))
            elif cat.startswith("Inclusión"):
                mask = cm.str.contains("marketing")
            elif cat.startswith("Ampliar"):
                mask = cm.str.contains("ampli") & cm.str.contains("canal")
            else:
                mask = cm.str.contains("increment") & cm.str.contains("venta")

            num = pd.to_numeric(sub.loc[mask, w], errors="coerce").fillna(0).sum()
            vals.append(float(num / den * 100) if den else 0.0)

        out[size] = vals

    return out


def main():
    d24 = calc(load_year(2024))
    validate("E.6 / 2024 contra reporte oficial", d24, EXPECTED_2024, 0.16)

    rows = [
        {"Tamaño": size, "Beneficio": cat, "Porcentaje": value}
        for size in SIZES
        for cat, value in zip(CATS, d24[size])
    ]
    result = pd.DataFrame(rows)

    print("\nDATOS USADOS PARA LA FIGURA E.6")
    print(result.to_string(index=False, formatters={"Porcentaje": "{:.1f}%".format}))


if __name__ == "__main__":
    main()
