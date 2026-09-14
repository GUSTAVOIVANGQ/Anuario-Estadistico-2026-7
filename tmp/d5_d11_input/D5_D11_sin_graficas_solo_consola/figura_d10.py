# -*- coding: utf-8 -*-
"""D.10: calcula e imprime los datos; no genera gráfica."""

from collections import OrderedDict

from _ecsi_d_common import infer_grouped_security_model, load_ecsi

AGES = OrderedDict([
    (1, "18 a 24 años"),
    (2, "25 a 34 años"),
    (3, "35 a 44 años"),
    (4, "45 a 54 años"),
    (5, "55 a más años"),
])

EXPECTED_2024 = OrderedDict([
    ("18 a 24 años", OrderedDict([("Muy seguro", 5.2), ("Seguro", 58.8), ("Ni seguro / Ni inseguro", 9.6), ("Inseguro", 11.3), ("NS/NR", 14.9)])),
    ("25 a 34 años", OrderedDict([("Muy seguro", 4.8), ("Seguro", 52.8), ("Ni seguro / Ni inseguro", 7.5), ("Inseguro", 16.4), ("NS/NR", 17.1)])),
    ("35 a 44 años", OrderedDict([("Muy seguro", 4.4), ("Seguro", 47.4), ("Ni seguro / Ni inseguro", 7.4), ("Inseguro", 19.8), ("NS/NR", 20.1)])),
    ("45 a 54 años", OrderedDict([("Muy seguro", 6.8), ("Seguro", 45.4), ("Ni seguro / Ni inseguro", 7.9), ("Inseguro", 18.5), ("NS/NR", 20.0)])),
    ("55 a más años", OrderedDict([("Muy seguro", 3.5), ("Seguro", 33.9), ("Ni seguro / Ni inseguro", 6.8), ("Inseguro", 21.0), ("NS/NR", 32.1)])),
])


def main() -> None:
    best = infer_grouped_security_model(
        load_ecsi(),
        group_var="edad_gpos",
        groups=AGES,
        value_var="seg_banca",
        relevant_var="ui_banca",
        expected_2024=EXPECTED_2024,
    )
    resultados = best["table"]

    print("D.10 - Resultados usados para la gráfica")
    print(f"{'Grupo de edad':14s} | {'Nivel de seguridad':24s} | {'Porcentaje':>10s}")
    print("-" * 56)
    for edad, datos in resultados.items():
        for nivel, porcentaje in datos.items():
            print(f"{edad:14s} | {nivel:24s} | {porcentaje:9.1f}%")


if __name__ == "__main__":
    main()
