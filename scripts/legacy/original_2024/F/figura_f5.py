import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import numpy as np

print("Iniciando el procesamiento de datos para Figura F.5...")

# ==========================================
# 1. EXTRAER LOS DATOS EXACTOS
# ==========================================
ruta_archivo = r'C:\Users\ivan-\Documents\GitHub\anuario\datos\F.5\mociba2023_tabulados.xlsx'

# Leemos las hojas sin saltar filas para mantener los índices correctos
df_mujeres = pd.read_excel(ruta_archivo, sheet_name='1.18')
df_hombres = pd.read_excel(ruta_archivo, sheet_name='1.17')

# La fila 17 tiene el Total. La columna 3 tiene los "Absolutos" de "Sí vivió ciberacoso"
total_mujeres = float(df_mujeres.iloc[17, 3])
total_hombres = float(df_hombres.iloc[17, 3])

# Las filas 18 a la 23 tienen los 6 rangos de edad
absolutos_mujeres = df_mujeres.iloc[18:24, 3].astype(float)
absolutos_hombres = df_hombres.iloc[18:24, 3].astype(float)

# Calculamos los porcentajes exactos
pct_mujeres = (absolutos_mujeres / total_mujeres) * 100
pct_hombres = (absolutos_hombres / total_hombres) * 100

# Etiquetas corregidas (sin errores de codificación)
edades = ['De 12 a\n19 años', 'De 20 a\n29 años', 'De 30 a\n39 años', 'De 40 a\n49 años', 'De 50 a\n59 años', 'De 60 años\ny más']


# ==========================================
# 2. GENERACIÓN DE LA GRÁFICA (Estilo F.16)
# ==========================================
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

# Tonos institucionales (Teal de la Guía)
COLOR_MUJERES = '#86adae'  # Teal claro
COLOR_HOMBRES = '#335a5c'  # Teal oscuro
color_texto = '#3c3c3b'

# Lienzo unificado
fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

x = np.arange(len(edades))
width = 0.35

# Dibujar barras agrupadas
rects1 = ax.bar(x - width/2, pct_hombres, width, label='Hombres', color=COLOR_HOMBRES, edgecolor='none', zorder=2)
rects2 = ax.bar(x + width/2, pct_mujeres, width, label='Mujeres', color=COLOR_MUJERES, edgecolor='none', zorder=2)

# Etiquetas de datos (Chips institucionales)
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

autolabel(rects1)
autolabel(rects2)

# Diseño limpio de Ejes
ax.set_xticks(x)
ax.set_xticklabels(edades, fontsize=10, fontweight='normal', color=color_texto)

ax.set_ylim(0, max(max(pct_hombres), max(pct_mujeres)) * 1.3) # Margen dinámico superior
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

ax.annotate("Figura F.5.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Distribución de la población víctima de ciberacoso por grupo de edad y sexo", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(95, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Leyenda inferior
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=2, fontsize=10, frameon=False, handlelength=2.5)

# Notas al pie y Fuente solicitada
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = 'IFT con datos del MOCIBA 2023, del INEGI. Para mas informacion consultar https://www.inegi.org.mx/programas/mociba/2023/.'
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.04
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
nota_text = 'Datos expresados como porcentaje del total de la población víctima de ciberacoso por sexo.'
fig.text(x_start + 0.025, y_nota, nota_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# Ajustar márgenes y Guardar
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
nombre_salida = r'C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_F5.png'
plt.savefig(nombre_salida, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')

print(f"¡Terminado! Gráfica guardada exitosamente como '{nombre_salida}'.")