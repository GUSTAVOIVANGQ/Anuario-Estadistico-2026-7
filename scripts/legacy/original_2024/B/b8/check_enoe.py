import zipfile
import pandas as pd
import os
import io

zip_path = r'C:\Users\ivan-\Documents\GitHub\anuario\datos\A.2\enoe_2024_trim2_csv.zip'
with zipfile.ZipFile(zip_path, 'r') as z:
    for name in z.namelist():
        if 'COE1' in name.upper() or 'SDEMT' in name.upper():
            with z.open(name) as f:
                # Read just the header to get exact column names
                header = pd.read_csv(f, nrows=0, encoding='latin-1').columns.tolist()
                header = [c.lower() for c in header]
                
                print(f"File {name} columns:")
                if 'p4a' in header:
                    print(" - HAS p4a (SCIAN code)")
                if 'fac_tri' in header or 'fac' in header or 'fac15' in header:
                    print(" - HAS expansion factor")
                
                with open('col_check.txt', 'a') as out:
                    out.write(f"{name}: {header}\n")
