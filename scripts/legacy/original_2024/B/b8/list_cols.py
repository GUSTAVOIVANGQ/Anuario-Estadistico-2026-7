import os
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", 'datos', 'A.7', 'microdatos')

conc = pd.read_csv(os.path.join(BASE, 'concentradohogar.csv'), nrows=100)
with open(os.path.join(os.path.dirname(__file__), 'cols_conc.txt'), 'w', encoding='utf-8') as f:
    f.write("\n".join(list(conc.columns)))
