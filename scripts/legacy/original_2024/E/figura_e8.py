import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os

try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

# ==========================================
# 1. RUTA Y CARGA DE DATOS
# ==========================================
ruta_2023 = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\E.8\Base de datos_Cuarta Encuesta 2023_MiPymes.xlsx"

try:
    df = pd.read_excel(ruta_2023, engine='openpyxl')
    print("¡Base de datos 2023 cargada exitosamente!")
except Exception as e:
    print(f"Error al cargar el archivo Excel: {e}")
    exit()

col_tam = [c for c in df.columns if 'tama' in c.lower() or 'tam' in c.lower()][0]
col_fac = [c for c in df.columns if 'factor' in c.lower() or 'expans' in c.lower()][0]

def calcular_pct_ponderado(df_filtro, col_val, col_peso):
    df_valido = df_filtro[df_filtro[col_val].notna()]
    if df_valido.empty: return 0.0
    peso_si = df_valido.loc[df_valido[col_val].astype(str).str.startswith('S', na=False), col_peso].sum()
    peso_total = df_valido[col_peso].sum()
    return (peso_si / peso_total) * 100 if peso_total > 0 else 0

categorias = ['General', 'Micro', 'Pequeña', 'Mediana']

beneficios_config = [
    {"titulo": "El contacto con los clientes\nes más rápido", "clave": "contacto con los clientes"},
    {"titulo": "La solicitud de pedidos\nes más ágil", "clave": "solicitud de pedidos"},
    {"titulo": "Mayor competitividad\nen el mercado", "clave": "competitividad"},
    {"titulo": "Facilita el control\nde ventas", "clave": "control de ventas"}
]

resultados = {}
for ben in beneficios_config:
    titulo = ben['titulo']
    cols_encontradas = [c for c in df.columns if 'beneficios de contar con una aplicaci' in c.lower() and ben['clave'].lower() in c.lower()]
    
    if not cols_encontradas:
        continue
        
    col_exacta = cols_encontradas[0]
    lista_pcts = []
    lista_pcts.append(calcular_pct_ponderado(df, col_exacta, col_fac))
    
    for cat in categorias[1:]:
        nombre_real = [t for t in df[col_tam].dropna().unique() if cat[:4].lower() in t.lower()][0]
        df_tam = df[df[col_tam] == nombre_real]
        lista_pcts.append(calcular_pct_ponderado(df_tam, col_exacta, col_fac))
        
    resultados[titulo] = lista_pcts

# ==========================================
# 3. GENERACIÓN DE LA GRÁFICA ESTILO A.9
# ==========================================
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, axes = plt.subplots(2, 2, figsize=(16, 10))
fig.patch.set_facecolor('white')

# Tono exacto de Figura A.9
COLOR_BARRA = '#335a5c'  
color_texto = '#3c3c3b'

x = np.arange(len(categorias))
width = 0.55 
axes_planos = axes.flatten()

for i, ax in enumerate(axes_planos):
    ax.set_facecolor('#F8F8FA')
    config = beneficios_config[i]
    titulo = config['titulo']
    datos = resultados[titulo]
    
    # Dibujar barras
    rects = ax.bar(x, datos, width, color=COLOR_BARRA, edgecolor='none', zorder=2)
    
    # Estilo del panel
    ax.set_title(titulo, loc='center', fontsize=12, fontweight='bold', color=color_texto, pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(categorias, fontsize=10, fontweight='normal', color=color_texto)
    
    # Cuadrícula y bordes (al ser vertical, ponemos la cuadrícula en Y)
    ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False) # ocultamos la izquierda para mayor limpieza en múltiples paneles
    ax.spines['bottom'].set_color('#7c7c7c')
    ax.tick_params(axis='y', left=False, labelleft=False) # Escondemos ticks en y
    
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 5), textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='normal', color=color_texto, zorder=3)

    max_h = max(datos)
    ax.set_ylim(0, max_h + (max_h * 0.25))

# TÍTULOS GLOBALES (Bloque Institucional)
fig.text(0.08, 0.95, '   ', va='center', ha='left', fontsize=2,
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

fig.text(0.095, 0.95, 'Figura E.8.', fontsize=14, fontweight='bold', color=color_texto, va='center', ha='left')

fig.text(0.16, 0.95, 'Beneficios principales percibidos al utilizar aplicaciones móviles', 
         fontsize=14, fontweight='medium', color=color_texto, va='center', ha='left')


# NOTAS AL PIE
font_size_notes = 8
x_start = 0.08

y_fuente = 0.06
fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fig.text(x_start + 0.033, y_fuente, "IFT con información de la Cuarta Encuesta 2023, Usuarios de Servicios de Telecomunicaciones (MiPymes).", 
         fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.04
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fig.text(x_start + 0.026, y_nota, "Respuesta espontánea y múltiple no suma 100%.", 
         fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# ==========================================
# 4. EXPORTACIÓN
# ==========================================
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.15, hspace=0.4)

ruta_salida_dir = r"C:\Users\ivan-\Documents\GitHub\anuario\output"
os.makedirs(ruta_salida_dir, exist_ok=True)
ruta_completa = os.path.join(ruta_salida_dir, "Figura_E8.png")

fig.savefig(ruta_completa, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"¡Gráfica exportada exitosamente en: {ruta_completa}!")