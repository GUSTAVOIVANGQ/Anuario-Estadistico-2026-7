# -*- coding: utf-8 -*-
"""D.7: calcula e imprime los datos; no genera gráfica."""

from collections import OrderedDict

from _ecsi_d_common import internet_users, load_ecsi, weighted_pct_binary

AGES = OrderedDict([
    (1, "18 a 24 años"),
    (2, "25 a 34 años"),
    (3, "35 a 44 años"),
    (4, "45 a 54 años"),
    (5, "55 a más años"),
])

VARS = OrderedDict([
    ("Recibir mensajes no deseados", "expp_mensnd"),
    ("Han publicado información personal sin su permiso", "expp_pubipi"),
    ("Han usado sus datos para pedir préstamos o créditos sin su permiso", "expp_datpre"),
    ("Han robado sus contraseñas", "expp_robcon"),
])


def main() -> None:
    df = internet_users(load_ecsi())

    resultados = OrderedDict()
    for age_code, age_label in AGES.items():
        sub = df[df["edad_gpos"] == age_code].copy()
        resultados[age_label] = OrderedDict()
        for etiqueta, var in VARS.items():
            resultados[age_label][etiqueta] = weighted_pct_binary(sub, var)

    print("D.7 - Resultados usados para la gráfica")
    print(f"{'Grupo de edad':14s} | {'Experiencia':68s} | {'Porcentaje':>10s}")
    print("-" * 100)
    for edad, datos in resultados.items():
        for experiencia, porcentaje in datos.items():
            print(f"{edad:14s} | {experiencia:68s} | {porcentaje:9.1f}%")


if __name__ == "__main__":
    main()
