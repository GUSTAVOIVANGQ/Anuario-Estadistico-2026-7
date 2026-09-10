import pandas as pd
import numpy as np

# 1. Leer el Excel (Asegúrate de poner tu ruta correcta)
# Leemos sin encabezados para evitar que Pandas se confunda con las celdas combinadas del INEGI
df = pd.read_excel(r'C:\Users\ivan-\Documents\GitHub\anuario\datos\F.3\mociba2023_tabulados.xlsx', sheet_name='1.16', header=None)

states_data = []
seen_states = set()
total_nacional = 0

col_entidad_idx = None
col_victimas_idx = None

# 2. BÚSQUEDA DINÁMICA (Cero hardcodeo)
for i, row in df.iterrows():
    row_str = row.astype(str).str.strip()
    
    if 'Estados Unidos Mexicanos' in row_str.values:
        # Detectar en qué columna están los estados
        col_entidad_idx = row_str[row_str == 'Estados Unidos Mexicanos'].index[0]
        
        # Extraer todos los valores numéricos válidos de esta fila
        numeros_en_fila = []
        for col_idx, val in row.items():
            if col_idx == col_entidad_idx: continue
            try:
                num = float(str(val).replace(',', '').strip())
                if not pd.isna(num):
                    numeros_en_fila.append((col_idx, num))
            except ValueError:
                continue
        
        # El formato INEGI es: [0] Población Total, [1] Víctimas Absolutas, [2] Prevalencia %...
        # Por lo tanto, tomamos la posición 1 (el segundo número numérico)
        if len(numeros_en_fila) >= 2:
            col_victimas_idx = numeros_en_fila[1][0]
            total_nacional = numeros_en_fila[1][1]
        break

# 3. EXTRACCIÓN Y LIMPIEZA
if col_entidad_idx is not None and col_victimas_idx is not None:
    for i, row in df.iterrows():
        entidad = str(row[col_entidad_idx]).strip()
        
        # Filtro anticongelante: Detener si llegamos al pie de página del INEGI
        if entidad in ['Estimaciones puntuales', 'Errores estándar'] or 'Coeficientes' in entidad:
            break
            
        # Ignorar vacíos, el total nacional y los subgrupos de edad
        if pd.isna(entidad) or entidad == 'nan' or entidad == '' or entidad == 'Estados Unidos Mexicanos' or entidad.startswith('De '):
            continue
            
        try:
            victimas_raw = str(row[col_victimas_idx]).replace(',', '').strip()
            victimas = float(victimas_raw)
        except ValueError:
            continue
            
        # Guardar solo estados únicos
        if entidad not in seen_states and not pd.isna(victimas):
            seen_states.add(entidad)
            states_data.append({
                'Entidad': entidad,
                'Victimas_Absolutas': victimas
            })
            
        if len(seen_states) == 32:
            break

    # 4. CÁLCULO Y RESULTADO FINAL
    df_states = pd.DataFrame(states_data)
    
    if not df_states.empty:
        df_states['Porcentaje_Calculado'] = (df_states['Victimas_Absolutas'] / total_nacional) * 100
        df_states['Porcentaje_Grafica'] = df_states['Porcentaje_Calculado'].round(1)
        df_states = df_states.sort_values(by="Porcentaje_Grafica", ascending=False).reset_index(drop=True)
        
        print(f"\nTotal nacional de víctimas detectado: {total_nacional:,.0f} (Debe ser ~18.3 millones)")
        print("-" * 65)
        print(df_states[['Entidad', 'Victimas_Absolutas', 'Porcentaje_Grafica']].to_string())
    else:
        print("No se extrajeron estados.")
else:
    print("Error: No se encontró la fila 'Estados Unidos Mexicanos' o no hay suficientes datos numéricos.")