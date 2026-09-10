import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
PROJECT_ROOT = Path(__file__).resolve().parents[2]
import numpy as np

# 1. Cargar las dos bases de datos históricas (2022 y 2023)
df_2022 = pd.read_excel(PROJECT_ROOT / "datos" / "E.2" / "Base de datos_Cuarta Encuesta 2022_MiPymes.xlsx")
df_2023 = pd.read_excel(PROJECT_ROOT / "datos" / "E.2" / "Base de datos_Cuarta Encuesta 2023_MiPymes.xlsx")

# 2. Identificar columnas (son iguales en ambos años)
col_clasif = 'Clasificación de la empresa por su tamaño'
col_int = 'En términos generales ¿qué tan satisfechos se encuentran con el servicio de Internet recibido en la empresa o negocio en los últimos 12 meses? Recodificada'
col_fija = 'En términos generales ¿qué tan satisfechos se encuentran con el servicio de telefonía fija recibido en la empresa o negocio en los últimos 12 meses? Recodificada'

# 3. Calcular promedios para 2022 y 2023
means_int_2022 = df_2022.groupby(col_clasif)[col_int].mean()
means_fija_2022 = df_2022.groupby(col_clasif)[col_fija].mean()

means_int_2023 = df_2023.groupby(col_clasif)[col_int].mean()
means_fija_2023 = df_2023.groupby(col_clasif)[col_fija].mean()

# 4. Ordenar los datos (Micro, Pequeña, Mediana)
order = ['Micro', 'Pequeña', 'Mediana']

val_int_2022 = [means_int_2022.get(x, 0) for x in order]
val_fija_2022 = [means_fija_2022.get(x, 0) for x in order]

val_int_2023 = [means_int_2023.get(x, 0) for x in order]
val_fija_2023 = [means_fija_2023.get(x, 0) for x in order]

# 5. Configuración de Gráfica UI (Estilo A.9/F.16)
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8.5))
fig.patch.set_facecolor('white')

# Colores institucionales
color_2022 = '#afafaf'  # Gris verde
color_2023 = '#86adae'  # Teal claro
color_texto = '#3c3c3b'

x = np.arange(len(order))
width = 0.25
gap = 0.02

# --- Gráfica 1: Internet Fijo ---
ax1.set_facecolor('#F8F8FA')
rects1_2022 = ax1.bar(x - width/2 - gap/2, val_int_2022, width, label='2022', color=color_2022, edgecolor='none', zorder=2)
rects1_2023 = ax1.bar(x + width/2 + gap/2, val_int_2023, width, label='2023', color=color_2023, edgecolor='none', zorder=2)

# --- Gráfica 2: Telefonía Fija ---
ax2.set_facecolor('#F8F8FA')
rects2_2022 = ax2.bar(x - width/2 - gap/2, val_fija_2022, width, label='2022', color=color_2022, edgecolor='none', zorder=2)
rects2_2023 = ax2.bar(x + width/2 + gap/2, val_fija_2023, width, label='2023', color=color_2023, edgecolor='none', zorder=2)

# Función de Chips UI
def autolabel(ax_obj, rects):
    for rect in rects:
        height = rect.get_height()
        bar_color = rect.get_facecolor()
        ax_obj.annotate(f'{height:.1f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                    bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

autolabel(ax1, rects1_2022)
autolabel(ax1, rects1_2023)
autolabel(ax2, rects2_2022)
autolabel(ax2, rects2_2023)

# Limpieza visual y configuración de ambos Ejes
max_val = max(max(val_int_2022), max(val_int_2023), max(val_fija_2022), max(val_fija_2023))

for ax, title in zip([ax1, ax2], ['Internet Fijo', 'Telefonía Fija']):
    ax.set_xticks(x)
    ax.set_xticklabels(order, fontsize=9, fontweight='normal', color=color_texto)
    
    ax.set_ylim(0, max_val * 1.25)
    ax.tick_params(axis='y', labelsize=9, colors=color_texto)
    
    ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#7c7c7c')
    ax.spines['bottom'].set_color('#7c7c7c')
    
    # Subtítulos de los ejes
    ax.set_title(title, fontweight='bold', fontsize=11, color=color_texto, pad=15)

# Títulos Generales (anclados al primer eje, ax1)
ax1.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 55), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax1.annotate("Figura E.3.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 55), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax1.annotate(" Servicios de telecomunicaciones contratados por las MiPymes", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(95, 55), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Leyenda unificada
handles, labels = ax1.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=2, fontsize=10, frameon=False, handlelength=2.5)

# Guardar y ajustar márgenes
fig.subplots_adjust(left=0.08, right=0.92, top=0.80, bottom=0.22, wspace=0.15)
plt.savefig(PROJECT_ROOT / "output" / "Figura_E3.png", dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("¡Figura E.3 construida y validada con la nueva UI!")
print(PROJECT_ROOT / "output" / "Figura_E3.png")