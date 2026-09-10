import zipfile
import pandas as pd

zip_path = r'C:\Users\ivan-\Documents\GitHub\anuario\datos\A.2\2013trim2_csv.zip'
with zipfile.ZipFile(zip_path, 'r') as z:
    for name in z.namelist():
        if 'SDEMT' in name.upper() or 'COE1' in name.upper():
            with z.open(name) as f:
                header = pd.read_csv(f, nrows=0, encoding='latin-1').columns.tolist()
                header = [c.lower() for c in header]
                print(f"{name}: {header[:15]} ...")
                if 'scian' in header: print("HAS scian")
                if 'p4a' in header: print("HAS p4a")
                if 'clase2' in header: print("HAS clase2")
