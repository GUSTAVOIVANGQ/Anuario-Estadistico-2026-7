# -*- coding: utf-8 -*-
"""D.9: calcula e imprime los datos; no genera gráfica."""

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
    ("18 a 24 años", OrderedDict([("Muy seguro", 3.4), ("Seguro", 52.7), ("Ni seguro / Ni inseguro", 14.1), ("Inseguro", 17.6), ("NS/NR", 11.9)])),
    ("25 a 34 años", OrderedDict([("Muy seguro", 3.9), ("Seguro", 52.1), ("Ni seguro / Ni inseguro", 11.0), ("Inseguro", 16.7), ("NS/NR", 15.5)])),
    ("35 a 44 años", OrderedDict([("Muy seguro", 3.8), ("Seguro", 49.6), ("Ni seguro / Ni inseguro", 7.5), ("Inseguro", 18.3), ("NS/NR", 19.8)])),
    ("45 a 54 años", OrderedDict([("Muy seguro", 4.5), ("Seguro", 52.7), ("Ni seguro / Ni inseguro", 7.4), ("Inseguro", 18.2), ("NS/NR", 16.8)])),
    ("55 a más años", OrderedDict([("Muy seguro", 2.9), ("Seguro", 43.2), ("Ni seguro / Ni inseguro", 8.0), ("Inseguro", 15.7), ("NS/NR", 29.1)])),
])


def main() -> None:
    best = infer_grouped_security_model(
        load_ecsi(),
        group_var="edad_gpos",
        groups=AGES,
        value_var="seg_comp",
        relevant_var="ui_comp",
        expected_2024=EXPECTED_2024,
    )
    resultados = best["table"]

    print("D.9 - Resultados usados para la gráfica")
    print(f"{'Grupo de edad':14s} | {'Nivel de seguridad':24s} | {'Porcentaje':>10s}")
    print("-" * 56)
    for edad, datos in resultados.items():
        for nivel, porcentaje in datos.items():
            print(f"{edad:14s} | {nivel:24s} | {porcentaje:9.1f}%")


if __name__ == "__main__":
    main()
