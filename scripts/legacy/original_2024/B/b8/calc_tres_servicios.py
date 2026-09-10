#!/usr/bin/env python3
"""Calcular combinaciones de servicios (tres servicios) y exportar CSV con procedencia.

Uso: ejecutar desde la raíz: `python scripts/calc_tres_servicios.py`
Requiere: dbfread (ya instalado en el venv)
Salida: `scripts/tres_servicios_summary.csv`
"""
from dbfread import DBF
import csv
import os

DBF_PATH = 'datos/B.1/microdatos/endutih2023_bd_dbf/tic_2023_hogares.DBF'
OUT_CSV = 'scripts/tres_servicios_summary.csv'


def to_int(val):
    try:
        return int(val)
    except Exception:
        return None


def main():
    if not os.path.exists(DBF_PATH):
        print('DBF no encontrado en', DBF_PATH)
        return 1

    table = DBF(DBF_PATH, load=True, encoding='latin1')
    total_weight = 0.0
    total_unweighted = 0

    # counts for exactly 0..3 of the chosen services (Internet, TV de paga, Telefonía fija)
    weighted_counts = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}
    unweighted_counts = {0: 0, 1: 0, 2: 0, 3: 0}

    for r in table:
        fac = r.get('FAC_HOG')
        try:
            w = float(fac)
        except Exception:
            continue
        total_weight += w
        total_unweighted += 1

        # Use the three services defined for the figure: Internet (P5_7_1), TV de paga (P5_7_2), Telefonía fija (P5_7_3)
        internet = str(r.get('P5_7_1') or '').strip()
        tvpaga = str(r.get('P5_7_2') or '').strip()
        tel_fija = str(r.get('P5_7_3') or '').strip()

        # treat '1' as yes, everything else as no
        n = 0
        if internet == '1':
            n += 1
        if tvpaga == '1':
            n += 1
        if tel_fija == '1':
            n += 1

        weighted_counts[n] += w
        unweighted_counts[n] += 1

    # Write detailed summary CSV
    out_detail = 'scripts/tres_servicios_desagregado.csv'
    with open(out_detail, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['category', 'exact_number_services', 'weighted_count', 'percent_of_total', 'unweighted_count'])
        labels = {0: 'Ninguno', 1: 'Un servicio', 2: 'Dos servicios', 3: 'Tres servicios'}
        for k in [3,2,1,0]:
            wc = weighted_counts[k]
            pct = (wc / total_weight * 100) if total_weight > 0 else 0
            writer.writerow([labels[k], k, int(round(wc)), round(pct, 3), unweighted_counts[k]])

    # Also write a compact summary for backwards compatibility
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['metric', 'weighted_count', 'percent_of_total'])
        for k in [3,2,1,0]:
            label = labels[k]
            wc = weighted_counts[k]
            pct = (wc / total_weight * 100) if total_weight > 0 else 0
            writer.writerow([label, int(round(wc)), round(pct, 3)])

    print('Total peso (suma FAC_HOG):', int(round(total_weight)))
    print('Escritos:', OUT_CSV, 'y', out_detail)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
