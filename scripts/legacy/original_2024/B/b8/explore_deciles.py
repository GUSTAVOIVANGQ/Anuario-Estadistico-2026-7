import os
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", 'datos', 'A.7', 'deciles')

with open(os.path.join(os.path.dirname(__file__), 'deciles_parsed.txt'), 'w', encoding='utf-8') as f:
    for filename in ['Hogares_13.xlsx', 'Hogares_14.xlsx', 'Hogares_15.xlsx']:
        path = os.path.join(BASE, filename)
        f.write(f"\n--- Leyendo {filename} ---\n")
        try:
            df = pd.read_excel(path)
            f.write(df.head(20).to_string())
            f.write("\n")
        except Exception as e:
            f.write(f"Error reading {filename}: {e}\n")
