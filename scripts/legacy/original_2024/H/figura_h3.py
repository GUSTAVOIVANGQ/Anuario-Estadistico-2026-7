import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import numpy as np
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches

# 1. Cargar los datos
df = pd.read_csv(r'C:\Users\ivan-\Documents\GitHub\anuario\datos\H.3\TD_CONSUMO_TV_RADIO_VA.csv', encoding='latin1')

# Filtrar solo el aparato Televisor
tv_data = df[df['APARATO'] == 'Televisor'].copy()

# Convertir a porcentaje (0-100%)
tv_data['Proporcion'] = tv_data['ENCENDIDOS'] * 100

# 2. Configurar colores y figura (Colores extraÃ­dos de la paleta original)
color_total = '#3A2E5D'   # Morado oscuro
color_hombres = '#3B8BBA' # Azul (Para cuando tengas los datos)
color_mujeres = '#ED5B5A' # Coral (Para cuando tengas los datos)

fig, ax = plt.subplots(figsize=(16, 5), facecolor='white')

x = np.arange(len(tv_data))
y_total = tv_data['Proporcion'].values
avg_total = tv_data['Proporcion'].mean()

# 3. Graficar la lÃ­nea y el Ã¡rea sombreada para Total
ax.fill_between(x, y_total, color=color_total, alpha=0.15, zorder=3)
ax.plot(x, y_total, color=color_total, linewidth=3.5, label='Total personas', zorder=4)

# LÃ­nea de promedio general
ax.plot(x, [avg_total]*len(x), color=color_total, linestyle='--', linewidth=2, zorder=4)

# 4. Configurar Eje Y (Escala y Formato)
ax.set_ylim(0, 40)
ax.set_yticks(np.arange(0, 40.1, 5))
ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
ax.set_ylabel('ProporciÃ³n de televisores encendidos (%)\nPorcentaje de personas\nviendo la TV por hora (%)', 
              fontsize=9, color='#666666', fontweight='bold', labelpad=15)

# 5. Configurar Eje X (Horarios)
tick_positions = np.arange(0, len(tv_data), 2)

# Extraer la hora de inicio de cada intervalo (ej. "02:00 - 02:30" -> "2:00")
tick_labels = [h.split(' ')[0] for h in tv_data['HORA'].iloc[tick_positions]]
tick_labels = [str(int(l.split(':')[0])) + ':00' for l in tick_labels]

ax.set_xticks(tick_positions)
ax.set_xticklabels(tick_labels, fontsize=9, color='#666666')
ax.set_xlabel('Horario', fontsize=10, color='#666666', fontweight='bold', labelpad=10)

# 6. Estilos, cuadrÃ­cula y bordes limpios
ax.grid(axis='both', linestyle='-', color='#EFEFEF', zorder=0)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.spines['bottom'].set_visible(True)
ax.spines['bottom'].set_color('#DDDDDD')
ax.spines['bottom'].set_linewidth(1.5)

ax.tick_params(axis='x', length=0, pad=10)
ax.tick_params(axis='y', length=0, pad=10)

# 7. Leyenda (Preparada para las 3 variables)
legend_elements = [
    mpatches.Patch(color=color_total, label='Total personas'),
    mpatches.Patch(color=color_hombres, label='Hombres'),
    mpatches.Patch(color=color_mujeres, label='Mujeres'),
    Line2D([0], [0], color=color_total, lw=2, linestyle='--', label='Promedio Total de personas 24 horas'),
    Line2D([0], [0], color=color_hombres, lw=2, linestyle='--', label='Promedio Hombres 24 horas'),
    Line2D([0], [0], color=color_mujeres, lw=2, linestyle='--', label='Promedio Mujeres 24 horas')
]
fig.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=6, frameon=False, fontsize=8, columnspacing=1)

# 8. TÃ­tulo / Marca de agua
plt.text(0.01, 1.05, "Figura H.3. Porcentaje de personas que vieron la televisiÃ³n por hora en Ciudad de MÃ©xico\n(DemostraciÃ³n con datos nacionales parciales)", 
         transform=ax.transAxes, fontsize=11, fontweight='bold', color='#333333', va='bottom')

# Guardar la imagen final
plt.subplots_adjust(bottom=0.2)
plt.savefig('grafica_h3_parcial.png', dpi=300, bbox_inches='tight')

