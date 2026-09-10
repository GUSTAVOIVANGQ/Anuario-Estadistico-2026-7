"""
Scan Excel files in datos/B.1 for telecom household tabulados.

Usage: from the repository root run
    py -3 scripts\find_tabulados_b1.py

What the script does:
- iterates all .xlsx files in datos/B.1
- reads all sheets and searches for keyword matches
- prints the file, sheet, matching rows and a few rows after (to show totals)

This is a lightweight helper to locate the table and the exact values in the
local Tabulados folder.
"""
import re
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1] / 'datos' / 'B.1'
KEYWORDS = [
    'servicios fijos', 'servicios fijas', 'telefon', 'telefoni', 'internet',
    'televisión', 'televis', 'hogares', 'total de hogares', 'tv restringida',
    'televisión restringida',
    # combination labels often used in the figure
    'tres servicios', 'dos servicios', 'un servicio', 'ninguno',
    'solo internet', 'solo telefon', 'solo tv', 'solo televisión', 'solo televisión restringida',
    'combinacion', 'combinación', 'combinación de servicios'
]

NUM_RE = re.compile(r"[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?%")


def scan_file(path: Path):
    try:
        xls = pd.read_excel(path, sheet_name=None, header=None, dtype=str)
    except Exception as e:
        print(f"ERROR reading {path.name}: {e}")
        return

    for sheet_name, df in xls.items():
        # convert all to strings
        arr = df.fillna('').astype(str).values
        for i, row in enumerate(arr):
            line = ' '.join(cell.strip() for cell in row if cell.strip())
            if not line:
                continue
            lower = line.lower()
            if any(k in lower for k in KEYWORDS):
                print('\n' + '='*80)
                print(f'File: {path.name}  |  Sheet: {sheet_name}  |  Row: {i+1}')
                print('-'*80)
                # print the matching row and the next 6 rows to show totals nearby
                nrows = arr.shape[0]
                for j in range(i, min(i+7, nrows)):
                    rowline = ' | '.join(cell.strip() for cell in arr[j] if cell.strip())
                    if not rowline:
                        continue
                    numbers = NUM_RE.findall(rowline)
                    print(f'R{j+1:4d}: {rowline}')
                    if numbers:
                        print(f'      → Numbers found: {numbers}')


def main():
    if not BASE.exists():
        print(f'Path not found: {BASE}')
        return

    xls_files = sorted(BASE.glob('*.xlsx'))
    if not xls_files:
        print('No .xlsx files found in', BASE)
        return

    print(f'Found {len(xls_files)} .xlsx files in {BASE}\n')
    for f in xls_files:
        scan_file(f)


if __name__ == '__main__':
    main()
