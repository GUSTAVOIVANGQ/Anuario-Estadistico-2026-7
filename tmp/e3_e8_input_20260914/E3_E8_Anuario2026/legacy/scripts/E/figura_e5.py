# -*- coding: utf-8 -*-
"""Figura E.5 — Percepción de beneficios de Internet fijo y/o Telefonía fija.

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
    weighted_mean,
    validate,
)

SIZES = ["Micro", "Pequeña", "Mediana"]
BENEFITS = [
    ("Más gente conoce la empresa", ["mas", "gente", "conoce", "empresa"]),
    ("Están más cerca de sus clientes/consumidores", ["cerca", "consumidores"]),
    ("Hay más ventas/clientes", ["mas", "ventas", "clientes"]),
    (
        "Disminución de los costos al poder encontrar más y mejores proveedores",
        ["costos", "proveedores"],
    ),
    ("Desarrollar nuevos productos o servicios", ["desarroll", "nuevos", "productos", "servicios"]),
    (
        "La entrega de productos o servicios es más rápida o menos costosa",
        ["entrega", "productos", "servicios", "rapida"],
    ),
    ("Los empleados hacen más en el mismo tiempo", ["empleados", "mismo", "tiempo"]),
]
EXPECTED_2023 = {
    "Micro": {
        "internet": [7.6, 7.4, 7.4, 6.7, 6.5, 6.4, 6.0],
        "telefonia": [6.4, 6.8, 6.4, 6.1, 5.8, 6.0, 5.4],
    },
    "Pequeña": {
        "internet": [8.1, 7.9, 7.8, 7.1, 6.9, 7.0, 6.8],
        "telefonia": [7.3, 7.4, 7.1, 6.8, 6.5, 6.6, 6.1],
    },
    "Mediana": {
        "internet": [8.3, 8.1, 8.0, 7.4, 7.4, 7.6, 7.3],
        "telefonia": [7.2, 7.5, 7.1, 6.7, 6.5, 6.8, 6.4],
    },
}


def benefit_col(df, tokens, service):
    required = list(tokens)
    if service == "internet":
        required += ["internet"]
        return find_column(
            df,
            required=required,
            prefer=["escala", "0", "10"],
            reject=["telefon"],
        )
    return find_column(
        df,
        required=required,
        any_groups=[["telefonia", "linea telefonica", "telefon"]],
        prefer=["fija", "escala"],
    )


def calc(df):
    w = factor_col(df)
    sc = size_col(df)
    out = {}
    cols = {}

    for label, tokens in BENEFITS:
        cols[(label, "internet")] = benefit_col(df, tokens, "internet")
        cols[(label, "telefonia")] = benefit_col(df, tokens, "telefonia")

    for size in SIZES:
        real = resolve_size_value(df, size)
        sub = df[df[sc] == real]
        out[size] = {"internet": [], "telefonia": []}
        for label, _ in BENEFITS:
            out[size]["internet"].append(weighted_mean(sub, cols[(label, "internet")], w))
            out[size]["telefonia"].append(weighted_mean(sub, cols[(label, "telefonia")], w))

    return out, cols


def main():
    d23, _ = calc(load_year(2023))
    validate("E.5 / 2023", d23, EXPECTED_2023, tolerance=0.16)

    # La figura actualizada utilizaba únicamente los resultados 2024.
    d24, _ = calc(load_year(2024))

    rows = []
    for size in SIZES:
        for i, (benefit, _) in enumerate(BENEFITS):
            rows.extend(
                [
                    {
                        "Año": 2024,
                        "Tamaño": size,
                        "Beneficio": benefit,
                        "Servicio": "Internet fijo",
                        "Promedio": d24[size]["internet"][i],
                    },
                    {
                        "Año": 2024,
                        "Tamaño": size,
                        "Beneficio": benefit,
                        "Servicio": "Telefonía fija",
                        "Promedio": d24[size]["telefonia"][i],
                    },
                ]
            )

    result = pd.DataFrame(rows)
    print("\nDATOS USADOS PARA LA FIGURA E.5")
    print(result.to_string(index=False, formatters={"Promedio": "{:.1f}".format}))


if __name__ == "__main__":
    main()
