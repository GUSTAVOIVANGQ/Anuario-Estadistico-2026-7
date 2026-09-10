#!/usr/bin/env python3
"""Inspección y extracción básica de 'tres servicios' desde los DBF de ENDUTIH.

Fase 1: listar campos y mostrar ejemplos para identificar nombres de variables.
Ejecutar desde la raíz del repo: `python scripts/extract_tres_servicios.py`.
Requiere: dbfread (pip install dbfread)
"""
import sys
from collections import Counter

try:
    from dbfread import DBF
except Exception as e:
    print("Error importing dbfread:", e)
    print("Instala con: pip install dbfread")
    sys.exit(2)

DBF_PATH = 'datos/B.1/microdatos/endutih2023_bd_dbf/tic_2023_hogares.DBF'

import os


def try_open(path):
    # intenta abrir en binario para detectar permisos
    try:
        with open(path, 'rb') as f:
            head = f.read(16)
        print('Apertura binaria OK, primeros bytes:', head)
        return True
    except Exception as e:
        print('No se pudo abrir binariamente', path, '=>', type(e).__name__, e)
        return False


def inspect_dbf(path, max_rows=1000):
    print(f"Leyendo DBF: {path}")
    table = DBF(path, load=True, encoding='latin1')
    print('\nCampos (name : type length):')
    for f in table.field_names:
        print(' -', f)

    print('\nMuestra de primeras filas (hasta', max_rows, '):')
    cnt = 0
    samples = []
    for rec in table:
        samples.append(rec)
        cnt += 1
        if cnt >= max_rows:
            break

    # Show value counts for all fields to help identificar variables relevantes
    print('\nConteo de valores (muestra) por campo:')
    for field in table.field_names:
        c = Counter()
        for r in samples:
            val = r.get(field)
            if val is None:
                key = 'None'
            else:
                key = str(val)
            c[key] += 1
        # show up to 6 most common
        common = c.most_common(6)
        print(f" - {field}: {common}")


if __name__ == '__main__':
    try:
        abs_path = os.path.abspath(DBF_PATH)
        print('Ruta absoluta:', abs_path)
        # probar apertura binaria antes de pasar a dbfread
        ok = try_open(abs_path)
        if not ok:
            print('Intentando apertura con ruta relativa...')
            try_open(DBF_PATH)
        inspect_dbf(DBF_PATH)
    except FileNotFoundError:
        print('DBF no encontrado en', DBF_PATH)
        sys.exit(1)
    except Exception as e:
        print('Error leyendo DBF:', e)
        raise
