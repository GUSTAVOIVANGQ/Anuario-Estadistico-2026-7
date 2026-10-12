# -*- coding: utf-8 -*-
"""Figura H.14 – Radio: Monterrey."""
from inram_radio_core import argumentos_base, calcular_figura, graficar_radio, imprimir_resumen

if __name__ == '__main__':
    args = argumentos_base('H14').parse_args()
    curvas, estudios = calcular_figura(args.datos, 'H14')
    imprimir_resumen('H14', curvas, estudios)
    ruta = graficar_radio(curvas, 'H14', args.salida, ylim_max=18, ystep=2)
    print(f'Figura guardada en: {ruta}')
