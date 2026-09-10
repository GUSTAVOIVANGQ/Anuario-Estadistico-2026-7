import zipfile
import pandas as pd
import numpy as np

zip_path = r'C:\Users\ivan-\Documents\GitHub\anuario\datos\A.2\enoe_2024_trim2_csv.zip'
with zipfile.ZipFile(zip_path, 'r') as z:
    for name in z.namelist():
        if 'SDEMT' in name.upper():
            with z.open(name) as f:
                df = pd.read_csv(f, usecols=['scian', 'clase2'], encoding='latin-1')
                print("SDEMT scian values:")
                print(df[df['clase2']==1]['scian'].dropna().astype(str).str.len().value_counts())
                print(df[df['clase2']==1]['scian'].dropna().astype(str).head())
        if 'COE1' in name.upper():
            with z.open(name) as f:
                df = pd.read_csv(f, usecols=['p4a'], encoding='latin-1')
                print("COE1 p4a values:")
                print(df['p4a'].dropna().astype(str).str.len().value_counts())
                print(df['p4a'].dropna().astype(str).head())
