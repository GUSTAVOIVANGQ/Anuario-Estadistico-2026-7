# -*- coding: utf-8 -*-
"""D.11: calcula e imprime los datos; no genera gráfica."""

from collections import OrderedDict

from _ecsi_d_common import infer_security_model_by_sex_with_total, load_ecsi

EXPECTED_2024 = OrderedDict([
    ("Total", OrderedDict([("Muy seguro", 3.5), ("Seguro", 48.8), ("Ni seguro / Ni inseguro", 15.5), ("Inseguro", 18.3), ("NS/NR", 12.8)])),
    ("Mujeres", OrderedDict([("Muy seguro", 2.8), ("Seguro", 43.1), ("Ni seguro / Ni inseguro", 16.2), ("Inseguro", 22.1), ("NS/NR", 14.7)])),
    ("Hombres", OrderedDict([("Muy seguro", 4.4), ("Seguro", 55.4), ("Ni seguro / Ni inseguro", 14.6), ("Inseguro", 14.0), ("NS/NR", 10.5)])),
])

ORDER = ["NS/NR", "Inseguro", "Ni seguro / Ni inseguro", "Seguro", "Muy seguro"]


def main() -> None:
    best = infer_security_model_by_sex_with_total(
        load_ecsi(),
        value_var="seg_redes",
        relevant_var="ui_redes",
        expected_2024=EXPECTED_2024,
    )
    resultados = best["table"]

    print("D.11 - Resultados usados para la gráfica")
    print(f"{'Grupo':10s} | {'Nivel de seguridad':24s} | {'Porcentaje':>10s}")
    print("-" * 52)
    for grupo in ["Total", "Mujeres", "Hombres"]:
        for nivel in ORDER:
            print(f"{grupo:10s} | {nivel:24s} | {resultados[grupo][nivel]:9.1f}%")


if __name__ == "__main__":
    main()
