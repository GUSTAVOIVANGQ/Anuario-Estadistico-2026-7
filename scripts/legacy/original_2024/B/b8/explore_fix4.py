import os
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", 'datos', 'A.7', 'microdatos')

gh = pd.read_csv(os.path.join(BASE, 'gastoshogar.csv'), usecols=['folioviv', 'foliohog', 'clave', 'gasto', 'gasto_tri', 'frecuencia'])

# Claves de Fijas
fijas = gh[gh['clave'].isin(['E001', 'E003', 'E004', 'E005'])]

with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", 'fijas_sample.txt'), 'w', encoding='utf-8') as f:
    f.write("=== Distribución del gasto transaction (no trimestralizado) ===\n")
    f.write(fijas['gasto'].describe().to_string() + "\n\n")
    f.write("=== Distribución del gasto_tri ===\n")
    f.write(fijas['gasto_tri'].describe().to_string() + "\n\n")
    f.write("=== frecuencias ===\n")
    f.write(fijas['frecuencia'].value_counts().to_string() + "\n\n")
    
    f.write("=== Sample of 20 random rows ===\n")
    f.write(fijas.sample(20).to_string() + "\n")
