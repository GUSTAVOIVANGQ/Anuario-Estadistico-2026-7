# -*- coding: utf-8 -*-
"""Figura H.13 – Radio: Guadalajara."""
from inram_radio_core import argumentos_base, calcular_figura, graficar_radio, imprimir_resumen

if __name__ == '__main__':
    args = argumentos_base('H13').parse_args()
    curvas, estudios = calcular_figura(args.datos, 'H13')
    imprimir_resumen('H13', curvas, estudios)
    ruta = graficar_radio(curvas, 'H13', args.salida, ylim_max=18, ystep=2)
    print(f'Figura guardada en: {ruta}')
