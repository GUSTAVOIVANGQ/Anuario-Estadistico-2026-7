import zipfile
import pandas as pd
import os
import glob
from itertools import combinations

y, q = 2013, 2
data_dir = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\A.2"
pattern = f"*{y}*trim{q}*.zip"
matches = glob.glob(os.path.join(data_dir, pattern))
zip_path = matches[0]

sdemt_cols = ['cd_a', 'ent', 'con', 'v_sel', 'n_hog', 'h_mud', 'n_ren', 'clase2', 'clase1', 'fac_tri', 'fac', 'eda', 'ur', 't_loc_tri', 't_loc_men', 'est_d_tri', 'pos_ocu', 'rama']
coe1_cols = ['cd_a', 'ent', 'con', 'v_sel', 'n_hog', 'h_mud', 'n_ren', 'p4a']
coe2_cols = ['cd_a', 'ent', 'con', 'v_sel', 'n_hog', 'h_mud', 'n_ren', 'p4a', 'p7a']

with zipfile.ZipFile(zip_path, 'r') as z:
    for name in z.namelist():
        upper = name.upper()
        if 'SDEMT' in upper and name.endswith('.csv'):
            with z.open(name) as f:
                header = pd.read_csv(f, nrows=0, encoding='latin-1').columns.str.lower()
                use_sdemt = [c for c in sdemt_cols if c in header]
                f.seek(0)
                df_sdemt = pd.read_csv(f, usecols=lambda x: x.lower() in use_sdemt, encoding='latin-1', low_memory=False)
                df_sdemt.columns = df_sdemt.columns.str.lower()
        elif 'COE1' in upper and name.endswith('.csv'):
            with z.open(name) as f:
                header = pd.read_csv(f, nrows=0, encoding='latin-1').columns.str.lower()
                use_coe1 = [c for c in coe1_cols if c in header]
                f.seek(0)
                df_coe1 = pd.read_csv(f, usecols=lambda x: x.lower() in use_coe1, encoding='latin-1', low_memory=False)
                df_coe1.columns = df_coe1.columns.str.lower()
        elif 'COE2' in upper and name.endswith('.csv'):
            with z.open(name) as f:
                header = pd.read_csv(f, nrows=0, encoding='latin-1').columns.str.lower()
                use_coe2 = [c for c in coe2_cols if c in header]
                f.seek(0)
                df_coe2 = pd.read_csv(f, usecols=lambda x: x.lower() in use_coe2, encoding='latin-1', low_memory=False)
                df_coe2.columns = df_coe2.columns.str.lower()

merge_keys = ['cd_a', 'ent', 'con', 'v_sel', 'n_hog', 'h_mud', 'n_ren']
df = pd.merge(df_sdemt, df_coe1, on=merge_keys, how='inner')
try:
    df = pd.merge(df, df_coe2, on=merge_keys, how='left')
except Exception as e:
    pass

scian_col = 'p4a_x' if 'p4a_x' in df.columns else 'p4a'
scian_series = pd.to_numeric(df[scian_col], errors='coerce').fillna(0)
scian_str = scian_series.astype(int).astype(str).str.zfill(4)
df['scian_str'] = scian_str

fac_col = 'fac_tri' if 'fac_tri' in df.columns else 'fac'
sum515 = df[(df['clase2'] == 1) & (df['scian_str'].str.startswith('515'))][fac_col].sum()
sum517 = df[(df['clase2'] == 1) & (df['scian_str'].str.startswith('517'))][fac_col].sum()

print("Target: 271,222")
print(f"515 (Radio): {sum515:,.0f}")
print(f"517 (Telecom): {sum517:,.0f}")
print(f"Total: {sum515 + sum517:,.0f}")

# Maybe there is a secondary occupation? variable p7a in coe2?
p7a_col = 'p7a' if 'p7a' in df.columns else None
if p7a_col:
    scian_series2 = pd.to_numeric(df[p7a_col], errors='coerce').fillna(0)
    scian_str2 = scian_series2.astype(int).astype(str).str.zfill(4)
    # add people who have 515 or 517 as secondary activity, and NOT as primary
    mask2_515 = (scian_str2.str.startswith('515')) & ~(df['scian_str'].str.startswith('515') | df['scian_str'].str.startswith('517'))
    mask2_517 = (scian_str2.str.startswith('517')) & ~(df['scian_str'].str.startswith('515') | df['scian_str'].str.startswith('517'))
    
    sec_515 = df[(df['clase2'] == 1) & mask2_515][fac_col].sum()
    sec_517 = df[(df['clase2'] == 1) & mask2_517][fac_col].sum()
    
    print(f"Secondary 515: {sec_515:,.0f}")
    print(f"Secondary 517: {sec_517:,.0f}")
    print(f"Total primary + secondary: {sum515 + sum517 + sec_515 + sec_517:,.0f}")
