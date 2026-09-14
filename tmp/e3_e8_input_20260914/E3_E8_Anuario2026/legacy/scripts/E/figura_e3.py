# -*- coding: utf-8 -*-
"""Figura E.3 — Índice General de Satisfacción (IGS) por servicio y tamaño.

Versión sin gráfica: calcula, valida e imprime en consola los datos que
originalmente se utilizaban para generar la figura.
"""
from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _mipymes_common import load_year, weighted_igs, size_col, resolve_size_value, validate

ORDER = ["Micro", "Pequeña", "Mediana"]
EXPECTED_2022 = {
    "Internet fijo": {"Micro": 74.0, "Pequeña": 76.0, "Mediana": 73.9},
    "Telefonía fija": {"Micro": 75.0, "Pequeña": 76.9, "Mediana": 74.1},
}
EXPECTED_2023 = {
    "Internet fijo": {"Micro": 74.4, "Pequeña": 76.9, "Mediana": 79.2},
    "Telefonía fija": {"Micro": 75.2, "Pequeña": 76.0, "Mediana": 78.2},
}
EXPECTED_2024 = {
    "Internet fijo": {"Micro": 76.2, "Pequeña": 76.1, "Mediana": 75.6},
    "Telefonía fija": {"Micro": 76.8, "Pequeña": 77.5, "Mediana": 78.9},
}


def calc_year(df):
    sc = size_col(df)
    out = {"Internet fijo": {}, "Telefonía fija": {}}
    for size in ORDER:
        real = resolve_size_value(df, size)
        sub = df[df[sc] == real]
        out["Internet fijo"][size] = weighted_igs(sub, "internet")
        out["Telefonía fija"][size] = weighted_igs(sub, "telefonia")
    return out


def main():
    # Reconstrucción y validación histórica.
    d22 = calc_year(load_year(2022))
    d23 = calc_year(load_year(2023))
    validate("E.3 / 2022", d22, EXPECTED_2022, tolerance=0.16)
    validate("E.3 / 2023", d23, EXPECTED_2023, tolerance=0.16)

    # Actualización 2024.
    d24 = calc_year(load_year(2024))
    validate("E.3 / 2024 contra reporte oficial", d24, EXPECTED_2024, tolerance=0.16)

    # Estos son exactamente los valores que alimentaban la gráfica 2023-2024.
    rows = []
    for year, data in [(2023, d23), (2024, d24)]:
        for service in ["Internet fijo", "Telefonía fija"]:
            for size in ORDER:
                rows.append(
                    {
                        "Año": year,
                        "Servicio": service,
                        "Tamaño": size,
                        "IGS": data[service][size],
                    }
                )

    result = pd.DataFrame(rows)
    print("\nDATOS USADOS PARA LA FIGURA E.3")
    print(result.to_string(index=False, formatters={"IGS": "{:.1f}".format}))


if __name__ == "__main__":
    main()
