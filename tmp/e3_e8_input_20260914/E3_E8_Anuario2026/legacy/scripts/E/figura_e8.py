# -*- coding: utf-8 -*-
"""Figura E.8 — Beneficios de contar con una aplicación móvil.

Versión sin gráfica: calcula, valida e imprime en consola los datos 2024 que
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
    weighted_yes_pct,
    validate,
)

SIZES = ["General", "Micro", "Pequeña", "Mediana"]
BENEFITS = [
    ("El contacto con los clientes es más rápido", ["contacto", "clientes"]),
    ("La solicitud de pedidos es más ágil", ["solicitud", "pedidos"]),
    ("Mayor competitividad en el mercado", ["competitividad"]),
    ("Facilita el control de ventas", ["control", "ventas"]),
]
EXPECTED_2023 = {
    "El contacto con los clientes es más rápido": [62.7, 62.1, 69.6, 71.4],
    "La solicitud de pedidos es más ágil": [44.4, 43.4, 57.8, 43.9],
    "Mayor competitividad en el mercado": [41.0, 41.0, 41.8, 41.8],
    "Facilita el control de ventas": [33.5, 33.4, 35.2, 32.7],
}
EXPECTED_2024 = {
    "El contacto con los clientes es más rápido": [60.1, 59.9, 62.5, 60.8],
    "La solicitud de pedidos es más ágil": [39.7, 39.3, 44.8, 40.1],
    "Mayor competitividad en el mercado": [37.8, 38.2, 33.7, 25.9],
    "Facilita el control de ventas": [23.7, 24.5, 14.5, 23.1],
}


def benefit_col(df, tokens):
    return find_column(
        df,
        required=tokens,
        prefer=["beneficios", "aplicacion"],
        reject=["pagina", "correo", "banca", "nube"],
    )


def calc(df):
    w = factor_col(df)
    sc = size_col(df)
    out = {}
    for title, tokens in BENEFITS:
        col = benefit_col(df, tokens)
        vals = [weighted_yes_pct(df, col, w)]
        for size in SIZES[1:]:
            vals.append(
                weighted_yes_pct(
                    df[df[sc] == resolve_size_value(df, size)],
                    col,
                    w,
                )
            )
        out[title] = vals
    return out


def main():
    # 2023 se conserva como control de validación histórica.
    d23 = calc(load_year(2023))
    validate("E.8 / 2023", d23, EXPECTED_2023, 0.16)

    # La figura actualizada utilizaba únicamente los resultados 2024.
    d24 = calc(load_year(2024))
    validate("E.8 / 2024 contra reporte oficial", d24, EXPECTED_2024, 0.16)

    rows = []
    for benefit, vals in d24.items():
        for size, value in zip(SIZES, vals):
            rows.append(
                {
                    "Año": 2024,
                    "Beneficio": benefit,
                    "Tamaño": size,
                    "Porcentaje": value,
                }
            )

    result = pd.DataFrame(rows)
    print("\nDATOS USADOS PARA LA FIGURA E.8")
    print(result.to_string(index=False, formatters={"Porcentaje": "{:.1f}%".format}))


if __name__ == "__main__":
    main()
