# -*- coding: utf-8 -*-
"""D.6: calcula e imprime los datos; no genera gráfica."""

from collections import OrderedDict

from _ecsi_d_common import internet_users, load_ecsi, weighted_pct_binary

VARS = OrderedDict([
    ("expp_mensnd", "Recibir mensajes no deseados"),
    ("expp_pubipi", "Han publicado información personal sin su permiso"),
    ("expp_datpre", "Han usado sus datos para pedir préstamos o créditos sin su permiso"),
    ("expp_robcon", "Han robado sus contraseñas"),
])


def main() -> None:
    df = internet_users(load_ecsi())
    grupos = OrderedDict([
        ("Hombres", df[df["sexo"] == 2].copy()),
        ("Mujeres", df[df["sexo"] == 1].copy()),
        ("Total", df.copy()),
    ])

    resultados = OrderedDict()
    for grupo, sub in grupos.items():
        resultados[grupo] = OrderedDict()
        for var, etiqueta in VARS.items():
            resultados[grupo][etiqueta] = weighted_pct_binary(sub, var)

    print("D.6 - Resultados usados para la gráfica")
    print(f"{'Grupo':10s} | {'Experiencia':68s} | {'Porcentaje':>10s}")
    print("-" * 96)
    for grupo, datos in resultados.items():
        for experiencia, porcentaje in datos.items():
            print(f"{grupo:10s} | {experiencia:68s} | {porcentaje:9.1f}%")


if __name__ == "__main__":
    main()
