import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()

# ==========================================
# 1. CÁLCULO DE DATOS EXACTOS
# ==========================================

file_path = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\E.6\Base de datos_Cuarta Encuesta 2023_MiPymes.xlsx"
df = pd.read_excel(file_path)

vender_internet_col = '¿Cuál de las siguientes actividades realiza a través de Internet? Vender servicios o productos'
beneficio_col = '¿Cuál es el principal beneficio de que la empresa venda a través de Internet?'
size_col = 'Clasificación de la empresa por su tamaño'
factor_col = 'Factor de Expansión Final'

df_vende = df[df[vender_internet_col] == 'Sí']

def obtener_porcentajes(df_subset):
    peso_total = df_subset[factor_col].sum()
    resultados = {}
    for cat in df_subset[beneficio_col].unique():
        if pd.isna(cat): continue
        peso_cat = df_subset[df_subset[beneficio_col] == cat][factor_col].sum()
        resultados[cat] = (peso_cat / peso_total) * 100
    return resultados

datos_general = obtener_porcentajes(df_vende)
datos_micro = obtener_porcentajes(df_vende[df_vende[size_col] == 'Micro'])
datos_pequena = obtener_porcentajes(df_vende[df_vende[size_col] == 'Pequeña'])
datos_mediana = obtener_porcentajes(df_vende[df_vende[size_col] == 'Mediana'])

categorias = [
    'Incremento de ventas', 
    'Ampliar canales de venta', 
    'Inclusión de marketing digital', 
    'La rapidez en la que se realizan las ventas o compras', 
    'Otro'
]

etiquetas_x = [
    'Incremento de ventas', 
    'Ampliar canales\nde venta', 
    'Inclusión de\nmarketing digital', 
    'La rapidez en la que se\nrealizan las ventas...', 
    'Otros'
]

valores_general = [datos_general.get(cat, 0) for cat in categorias]
valores_micro = [datos_micro.get(cat, 0) for cat in categorias]
valores_pequena = [datos_pequena.get(cat, 0) for cat in categorias]
valores_mediana = [datos_mediana.get(cat, 0) for cat in categorias]


# ==========================================
# 2. GENERACIÓN DE LA GRÁFICA (Estilo F.16)
# ==========================================

plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

# Mismos tonos del "Teal" exacto dictado en F.16 / Guía 
# General toma el gris de F.16, Micro el claro, Mediana el oscuro y Pequeña un punto medio del Teal
COLOR_GENERAL = '#afafaf'
COLOR_MICRO   = '#86adae'
COLOR_PEQUENA = '#5c9596'
COLOR_MEDIANA = '#335a5c'
color_texto   = '#3c3c3b'

x = np.arange(len(categorias))
ancho_barra = 0.20

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Dibujar las barras con zorder=2 y bordes invisibles
barras_general = ax.bar(x - ancho_barra*1.5, valores_general, ancho_barra, label='General', color=COLOR_GENERAL, edgecolor='none', zorder=2)
barras_micro = ax.bar(x - ancho_barra*0.5, valores_micro, ancho_barra, label='Micro', color=COLOR_MICRO, edgecolor='none', zorder=2)
barras_pequena = ax.bar(x + ancho_barra*0.5, valores_pequena, ancho_barra, label='Pequeña', color=COLOR_PEQUENA, edgecolor='none', zorder=2)
barras_mediana = ax.bar(x + ancho_barra*1.5, valores_mediana, ancho_barra, label='Mediana', color=COLOR_MEDIANA, edgecolor='none', zorder=2)

# Etiquetas de datos (Chips estilo F.16)
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        bar_color = rect.get_facecolor()
        if height > 0:
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 6),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                        bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

autolabel(barras_general)
autolabel(barras_micro)
autolabel(barras_pequena)
autolabel(barras_mediana)

# Diseño limpio de Ejes
ax.set_xticks(x)
ax.set_xticklabels(etiquetas_x, fontsize=9, fontweight='normal', color=color_texto)

ax.set_ylim(0, 75)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# Títulos Institucionales
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura E.6.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Beneficios de vender a través de Internet fijo", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(95, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Leyenda inferior (idéntica al estilo F.16)
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=4, fontsize=10, frameon=False, handlelength=2.5)

# Notas al pie y Fuente
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = ('IFT con información de la Cuarta Encuesta 2023, Usuarios de Servicios de Telecomunicaciones (MiPymes).\n'
               'Para mayor información consultar: https://www.ift.org.mx/usuarios-y-audiencias/')
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.04
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
nota_text = 'Respuesta múltiple. Segmentos clasificados por tamaño de empresa.'
fig.text(x_start + 0.025, y_nota, nota_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# Ajustar y Guardar
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
plt.savefig(r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_E6.png", dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("¡Cálculo finalizado y gráfica guardada exitosamente!")