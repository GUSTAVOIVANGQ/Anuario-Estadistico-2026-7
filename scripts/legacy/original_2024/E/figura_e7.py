import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import os

# ==========================================
# 1. RUTAS Y CARGA DE DATOS
# ==========================================
ruta_2022 = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\E.7\Base de datos_Cuarta Encuesta 2022_MiPymes.xlsx"
ruta_2023 = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\E.7\Base de datos_Cuarta Encuesta 2023_MiPymes.xlsx"

try:
    df_2022 = pd.read_excel(ruta_2022, engine='openpyxl')
    df_2023 = pd.read_excel(ruta_2023, engine='openpyxl')
    print("¡Bases de datos cargadas exitosamente!")
except Exception as e:
    print(f"Error fatal al cargar archivos Excel: {e}")
    exit()

# ==========================================
# 2. CONFIGURACIÓN Y FUNCIONES DE CÁLCULO
# ==========================================
categorias = ['General', 'Micro', 'Pequeña', 'Mediana']

configuracion_dispositivos = [
    {"titulo": "Teléfonos móviles inteligentes\n(Smartphones)", "clave": "Smartphone"},
    {"titulo": "Computadoras de escritorio", "clave": "escritorio"},
    {"titulo": "Terminal punto de venta fija,\npara celular (clip) o tableta", "clave": "Terminal"},
    {"titulo": "Laptop", "clave": "Laptop"},
    {"titulo": "Teléfonos móviles análogos", "clave": "sin acceso"},
    {"titulo": "Servidores de almacenamiento\nde información", "clave": "Servidores"}
]

def calcular_pct_ponderado(df, col_val, col_peso):
    df_valido = df[df[col_val].notna()]
    if df_valido.empty: return 0.0
    peso_si = df_valido.loc[df_valido[col_val].astype(str).str.startswith('S', na=False), col_peso].sum()
    peso_total = df_valido[col_peso].sum()
    return (peso_si / peso_total) * 100 if peso_total > 0 else 0

print("\nIniciando cálculo de datos al vuelo...")
resultados = {} 

for df, anio in [(df_2022, 2022), (df_2023, 2023)]:
    col_tam = [c for c in df.columns if 'tama' in c.lower() or 'tam' in c.lower()][0]
    col_fac = [c for c in df.columns if 'factor' in c.lower() or 'expans' in c.lower()][0]
    
    for dev in configuracion_dispositivos:
        titulo = dev['titulo']
        if titulo not in resultados: resultados[titulo] = {}
        
        col_dev = [c for c in df.columns if dev['clave'].lower() in c.lower()][0]
        
        lista_pcts = []
        lista_pcts.append(calcular_pct_ponderado(df, col_dev, col_fac))
        for cat in categorias[1:]:
            nombre_real = [t for t in df[col_tam].dropna().unique() if cat[:4].lower() in t.lower()][0]
            df_tam = df[df[col_tam] == nombre_real]
            lista_pcts.append(calcular_pct_ponderado(df_tam, col_dev, col_fac))
            
        resultados[titulo][anio] = lista_pcts

print("¡Cálculos completados! Generando gráfica...")

# ==========================================
# 3. GENERACIÓN DE LA GRÁFICA MULTIPANEL (Estilo F.16)
# ==========================================
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, axes = plt.subplots(2, 3, figsize=(18, 11), dpi=150)
fig.patch.set_facecolor('white')

# Colores institucionales alineados a F.16
COLOR_2022 = '#86adae'  # Teal claro
COLOR_2023 = '#335a5c'  # Teal oscuro
color_texto = '#3c3c3b'

x = np.arange(len(categorias))
width = 0.35 

axes_planos = axes.flatten()

for i, ax in enumerate(axes_planos):
    config = configuracion_dispositivos[i]
    titulo = config['titulo']
    
    data_2022 = resultados[titulo][2022]
    data_2023 = resultados[titulo][2023]

    ax.set_facecolor('#F8F8FA')
    
    # Pintar las barras
    rects1 = ax.bar(x - width/2, data_2022, width, label='2022', color=COLOR_2022, edgecolor='none', zorder=2)
    rects2 = ax.bar(x + width/2, data_2023, width, label='2023', color=COLOR_2023, edgecolor='none', zorder=2)
    
    ax.set_title(titulo, fontsize=11, fontweight='bold', color=color_texto, pad=15)
    
    # Diseño limpio de Ejes
    ax.set_xticks(x)
    ax.set_xticklabels(categorias, fontsize=10, fontweight='normal', color=color_texto)
    
    max_h = max(max(data_2022), max(data_2023))
    ax.set_ylim(0, max_h * 1.35)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax.tick_params(axis='y', labelsize=9, colors=color_texto)
    
    ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#7c7c7c')
    ax.spines['bottom'].set_color('#7c7c7c')
    
    # Etiquetas de datos (Chips estilo F.16)
    def autolabel(rects, ax_target):
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                bar_color = rect.get_facecolor()
                ax_target.annotate(f'{height:.1f}%',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 6), 
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                            bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

    autolabel(rects1, ax)
    autolabel(rects2, ax)

# 4. Títulos Globales (Estilo F.16)
fig.text(0.04, 0.94, '   ', fontsize=2,
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

fig.text(0.05, 0.94, "Figura E.7.", 
         fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

fig.text(0.11, 0.94, " Dispositivos que usan las MiPymes para realizar sus actividades (2022-2023)", 
         fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# 5. Leyenda Global Centralizada
handles = [mpatches.Patch(color=COLOR_2022, label='2022'), mpatches.Patch(color=COLOR_2023, label='2023')]
fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=2, fontsize=11, frameon=False, handlelength=2.5)

# 6. Notas al pie
font_size_notes = 8
x_start = 0.04
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = ('IFT con información de la Cuarta Encuesta 2023, Usuarios de Servicios de Telecomunicaciones (micro, pequeñas y medianas empresas).\n'
               'Para más información consultar: https://www.ift.org.mx/usuarios-y-audiencias/encuestas-trimestrales.')
fig.text(x_start + 0.028, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.04
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
nota_text = 'Respuesta múltiple, por lo que la suma no da 100%. Los resultados pueden presentar variaciones explicadas por el error teórico de cada encuesta.'
fig.text(x_start + 0.022, y_nota, nota_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# 7. Ajuste y Guardar
plt.subplots_adjust(wspace=0.15, hspace=0.35, top=0.88, bottom=0.22, left=0.04, right=0.96)

ruta_salida_dir = r"C:\Users\ivan-\Documents\GitHub\anuario\output"
nombre_imagen = "figura_e7.png"
ruta_completa = os.path.join(ruta_salida_dir, nombre_imagen)
os.makedirs(ruta_salida_dir, exist_ok=True)

plt.savefig(ruta_completa, facecolor='white', edgecolor='none', bbox_inches='tight', dpi=300)
print(f"¡Figura E.7 construida y validada con el estilo F.16 en: {ruta_completa}!")