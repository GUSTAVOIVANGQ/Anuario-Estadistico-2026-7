import zipfile
import pandas as pd
import os
import glob

quarters = [
    (2013, 2), (2013, 4),
    (2014, 2), (2014, 4),
    (2015, 2), (2015, 4),
    (2016, 2), (2016, 4),
    (2017, 2), (2017, 4),
    (2018, 2), (2018, 4),
    (2019, 2), (2019, 4),
    (2020, 1), (2020, 4),
    (2021, 2), (2021, 4),
    (2022, 2), (2022, 4),
    (2023, 2), (2023, 4),
    (2024, 2)
]

data_dir = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\A.2"
results = []

for y, q in quarters:
    pattern = f"*{y}*trim{q}*.zip"
    matches = glob.glob(os.path.join(data_dir, pattern))
    if not matches:
        print(f"Missing {y} Q{q}")
        continue
    
    zip_path = matches[0]
    print(f"Processing {y} Q{q} -> {os.path.basename(zip_path)}")
    
    sdemt_cols = ['cd_a', 'ent', 'con', 'v_sel', 'n_hog', 'h_mud', 'n_ren', 'clase2', 'fac_tri', 'fac', 'scian']
    coe1_cols = ['cd_a', 'ent', 'con', 'v_sel', 'n_hog', 'h_mud', 'n_ren', 'p4a']
    
    df_sdemt = None
    df_coe1 = None
    
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

    if df_sdemt is not None and df_coe1 is not None:
        merge_keys = ['cd_a', 'ent', 'con', 'v_sel', 'n_hog', 'h_mud', 'n_ren']
        merge_keys = [k for k in merge_keys if k in df_sdemt.columns and k in df_coe1.columns]
        df = pd.merge(df_sdemt, df_coe1, on=merge_keys, how='inner')
    elif df_sdemt is not None:
        df = df_sdemt
    else:
        df = df_coe1
        
    df = df[df['clase2'] == 1]
    
    fac_col = 'fac_tri' if 'fac_tri' in df.columns else 'fac'
    
    scian_series = None
    if 'p4a' in df.columns:
        scian_series = df['p4a']
    elif 'scian' in df.columns:
        scian_series = df['scian']
        
    if scian_series is None:
        print("No scian column found!")
        continue
        
    scian_series = pd.to_numeric(scian_series, errors='coerce').fillna(0)
    scian_str = scian_series.astype(int).astype(str).str.zfill(4)
    
    is_telecom = scian_str.str.startswith('517')
    is_radio = scian_str.str.startswith('515')
    
    pop_telecom = df.loc[is_telecom, fac_col].sum()
    pop_radio = df.loc[is_radio, fac_col].sum()
    
    results.append({
        'year': y,
        'quarter': q,
        'telecom': pop_telecom,
        'radio': pop_radio
    })

df_res = pd.DataFrame(results)
df_res.to_csv("datos_a2_extracted.csv", index=False)
print("Finished extraction. Head:")
print(df_res.head())
print("Tail:")
print(df_res.tail())
