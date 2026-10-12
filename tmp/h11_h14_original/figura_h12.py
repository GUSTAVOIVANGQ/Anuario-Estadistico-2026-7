# -*- coding: utf-8 -*-
"""Figura H.12 – Radio: Ciudad de México."""
from inram_radio_core import argumentos_base, calcular_figura, graficar_radio, imprimir_resumen

if __name__ == '__main__':
    args = argumentos_base('H12').parse_args()
    curvas, estudios = calcular_figura(args.datos, 'H12')
    imprimir_resumen('H12', curvas, estudios)
    ruta = graficar_radio(curvas, 'H12', args.salida, ylim_max=25, ystep=5)
    print(f'Figura guardada en: {ruta}')
