# -*- coding: utf-8 -*-
"""D.5: calcula e imprime los datos; no genera gráfica."""

from collections import OrderedDict

from _ecsi_d_common import internet_users, load_ecsi, weighted_pct_binary

VARS = OrderedDict([
    ("apren_uso_int_1", "Por su cuenta"),
    ("apren_uso_int_2", "Capacitación en el trabajo"),
    ("apren_uso_int_3", "Curso en la escuela"),
    ("apren_uso_int_4", "Curso en centro comunitario"),
    ("apren_uso_int_5", "Curso particular"),
    ("apren_uso_int_6", "Amigos o familiares"),
    ("apren_uso_int_8", "Otros"),
    ("apren_uso_int_9", "NS/NR"),
])


def main() -> None:
    usuarios = internet_users(load_ecsi())

    resultados = OrderedDict()
    for var, etiqueta in VARS.items():
        resultados[etiqueta] = weighted_pct_binary(usuarios, var)

    print("D.5 - Resultados usados para la gráfica")
    print(f"{'Categoría':40s} {'Porcentaje':>10s}")
    print("-" * 52)
    for categoria, porcentaje in resultados.items():
        print(f"{categoria:40s} {porcentaje:9.1f}%")


if __name__ == "__main__":
    main()
