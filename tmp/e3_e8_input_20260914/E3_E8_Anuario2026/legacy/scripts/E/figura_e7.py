# -*- coding: utf-8 -*-
"""Figura E.7 — Dispositivos que usan las MiPymes para realizar sus actividades.

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
    weighted_yes_pct,
    validate,
)

SIZES = ["General", "Micro", "Pequeña", "Mediana"]
DEVICES = [
    ("Teléfonos móviles inteligentes (Smartphones)", ["smartphone"]),
    ("Computadoras de escritorio", ["escritorio"]),
    ("Terminal punto de venta fija, para celular (clip) o tableta", ["terminal"]),
    ("Laptop", ["laptop"]),
    ("Teléfonos móviles análogos", ["sin acceso"]),
    ("Servidores de almacenamiento de información", ["servidor"]),
]
EXPECTED_2023 = {
    "Teléfonos móviles inteligentes (Smartphones)": [98.5, 98.7, 94.9, 96.1],
    "Computadoras de escritorio": [49.1, 47.4, 74.1, 93.3],
    "Terminal punto de venta fija, para celular (clip) o tableta": [54.5, 54.2, 60.7, 58.2],
    "Laptop": [41.9, 40.5, 62.1, 73.6],
    "Teléfonos móviles análogos": [34.3, 33.8, 44.7, 46.8],
    "Servidores de almacenamiento de información": [14.0, 12.5, 33.6, 56.4],
}
EXPECTED_2024 = {
    "Teléfonos móviles inteligentes (Smartphones)": [95.7, 95.6, 97.2, 93.7],
    "Computadoras de escritorio": [51.3, 49.7, 74.3, 87.5],
    "Terminal punto de venta fija, para celular (clip) o tableta": [47.1, 46.8, 50.1, 61.8],
    "Laptop": [38.2, 36.7, 60.3, 59.1],
    "Teléfonos móviles análogos": [31.2, 30.1, 45.6, 41.4],
    "Servidores de almacenamiento de información": [17.8, 16.5, 36.0, 44.1],
}


def device_col(df, tokens):
    return find_column(
        df,
        required=tokens,
        prefer=["dispositivo", "aparato", "cuenta"],
        reject=["beneficio", "frecuencia", "satisfech"],
    )


def calc(df):
    w = factor_col(df)
    sc = size_col(df)
    out = {}
    for title, tokens in DEVICES:
        col = device_col(df, tokens)
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
    d23 = calc(load_year(2023))
    validate("E.7 / 2023", d23, EXPECTED_2023, 0.16)

    d24 = calc(load_year(2024))
    validate("E.7 / 2024 contra reporte oficial", d24, EXPECTED_2024, 0.16)

    rows = []
    for year, data in [(2023, d23), (2024, d24)]:
        for device, vals in data.items():
            for size, value in zip(SIZES, vals):
                rows.append(
                    {
                        "Año": year,
                        "Dispositivo": device,
                        "Tamaño": size,
                        "Porcentaje": value,
                    }
                )

    result = pd.DataFrame(rows)
    print("\nDATOS USADOS PARA LA FIGURA E.7")
    print(result.to_string(index=False, formatters={"Porcentaje": "{:.1f}%".format}))


if __name__ == "__main__":
    main()
