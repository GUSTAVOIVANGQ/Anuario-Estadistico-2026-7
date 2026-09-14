# -*- coding: utf-8 -*-
"""D.8: calcula e imprime los datos; no genera gráfica."""

from collections import OrderedDict

from _ecsi_d_common import load_ecsi, weighted_distribution

CODES = OrderedDict([
    (1, "Nada"),
    (2, "Poco"),
    (3, "Le es indiferente"),
    (4, "Algo"),
    (5, "Mucho"),
    (9, "NS/NR"),
])


def main() -> None:
    resultados = weighted_distribution(load_ecsi(), "conf_int", CODES)

    print("D.8 - Resultados usados para la gráfica")
    print(f"{'Percepción':22s} {'Porcentaje':>10s}")
    print("-" * 34)
    for categoria, porcentaje in resultados.items():
        print(f"{categoria:22s} {porcentaje:9.1f}%")


if __name__ == "__main__":
    main()
