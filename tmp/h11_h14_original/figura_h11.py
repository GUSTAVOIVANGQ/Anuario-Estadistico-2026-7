# -*- coding: utf-8 -*-
"""Figura H.11 – Radio: CDMX + Guadalajara + Monterrey."""
from inram_radio_core import argumentos_base, calcular_figura, graficar_radio, imprimir_resumen

if __name__ == '__main__':
    args = argumentos_base('H11').parse_args()
    curvas, estudios = calcular_figura(args.datos, 'H11')
    imprimir_resumen('H11', curvas, estudios)
    ruta = graficar_radio(curvas, 'H11', args.salida, ylim_max=20, ystep=5)
    print(f'Figura guardada en: {ruta}')
