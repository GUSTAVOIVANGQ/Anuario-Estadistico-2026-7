# -*- coding: utf-8 -*-
"""Figura E.4 — Servicios de telecomunicaciones que contratan las MiPymes.

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
SERVICES = {
    "Internet fijo": dict(required=["internet", "fijo"], prefer=["contrat"]),
    "Telefonía fija": dict(required=["telefon", "fija"], prefer=["contrat"]),
    "Telefonía móvil": dict(required=["telefon", "movil"], prefer=["contrat"]),
    "Datos móviles": dict(required=["datos", "movil"], prefer=["contrat"]),
    "Televisión de paga": dict(required=["television", "paga"], prefer=["contrat"]),
}
EXPECTED_2023 = {
    "Internet fijo": {"General": 84.4, "Micro": 89.3, "Pequeña": 89.8, "Mediana": 99.5},
    "Telefonía fija": {"General": 78.9, "Micro": 78.4, "Pequeña": 85.8, "Mediana": 94.6},
    "Telefonía móvil": {"General": 29.6, "Micro": 30.2, "Pequeña": 19.9, "Mediana": 27.4},
    "Datos móviles": {"General": 19.6, "Micro": 20.2, "Pequeña": 9.5, "Mediana": 15.9},
    "Televisión de paga": {"General": 25.4, "Micro": 25.7, "Pequeña": 21.7, "Mediana": 17.8},
}
EXPECTED_2024 = {
    "Internet fijo": {"General": 95.3, "Micro": 95.2, "Pequeña": 96.3, "Mediana": 98.1},
    "Telefonía fija": {"General": 69.0, "Micro": 68.3, "Pequeña": 78.6, "Mediana": 85.5},
    "Telefonía móvil": {"General": 29.0, "Micro": 28.7, "Pequeña": 34.9, "Mediana": 31.9},
    "Televisión de paga": {"General": 27.0, "Micro": 27.4, "Pequeña": 22.1, "Mediana": 20.9},
}


def service_col(df, name):
    spec = SERVICES[name]
    return find_column(
        df,
        required=spec["required"],
        prefer=spec["prefer"],
        reject=["pago", "importan", "satisfech", "beneficio"],
    )


def calc(df, names):
    w = factor_col(df)
    sc = size_col(df)
    out = {}
    for svc in names:
        col = service_col(df, svc)
        out[svc] = {"General": weighted_yes_pct(df, col, w)}
        for size in SIZES[1:]:
            real = resolve_size_value(df, size)
            out[svc][size] = weighted_yes_pct(df[df[sc] == real], col, w)
    return out


def main():
    # 2023 conserva todas las categorías para validar la serie histórica.
    d23 = calc(load_year(2023), list(SERVICES))
    validate("E.4 / 2023", d23, EXPECTED_2023, 0.16)

    # En 2024 "Datos móviles" ya no se publica como servicio separado.
    common = ["Internet fijo", "Telefonía fija", "Telefonía móvil", "Televisión de paga"]
    d24 = calc(load_year(2024), common)
    validate("E.4 / 2024 contra reporte oficial", d24, EXPECTED_2024, 0.16)

    # La gráfica original solo utilizaba estas cuatro categorías comunes.
    rows = []
    for year, data in [(2023, d23), (2024, d24)]:
        for svc in common:
            for size in SIZES:
                rows.append(
                    {
                        "Año": year,
                        "Servicio": svc,
                        "Tamaño": size,
                        "Porcentaje": data[svc][size],
                    }
                )

    result = pd.DataFrame(rows)
    print("\nDATOS USADOS PARA LA FIGURA E.4")
    print(result.to_string(index=False, formatters={"Porcentaje": "{:.1f}%".format}))
    print(
        "\nNota metodológica: Datos móviles no se incluye en la salida comparable "
        "2023-2024 porque en 2024 ya no se publica como servicio separado."
    )


if __name__ == "__main__":
    main()
