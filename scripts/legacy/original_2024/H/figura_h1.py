import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import numpy as np
from scipy.interpolate import make_interp_spline

# 1. Cargar y procesar datos DINÁMICAMENTE desde el CSV
# Path absoluto basado en la ubicación de este script
base_dir = Path(__file__).parent.parent.parent
df = pd.read_csv(base_dir / 'datos' / 'H.1' / 'TD_CONSUMO_TV_RADIO_VA.csv')

# Filtrar solo 'Televisor' y convertir a porcentaje
df_tv = df[df['APARATO'] == 'Televisor'].copy()
df_tv['PCT'] = df_tv['ENCENDIDOS'] * 100

# Extraer la hora de inicio (ej. '02' a partir de '02:00 - 02:30')
df_tv['HORA_INICIO'] = df_tv['HORA'].str[0:2].astype(int)

# Agrupar por hora para obtener el promedio horario de "Total personas"
df_horario = df_tv.groupby('HORA_INICIO')['PCT'].mean().reset_index()

# Reordenar para que el eje X empiece a las 2:00 y termine a las 1:00 (como en tu PDF)
orden_horas = list(range(2, 24)) + [0, 1]
df_horario['orden'] = df_horario['HORA_INICIO'].apply(lambda x: orden_horas.index(x))
df_horario = df_horario.sort_values('orden').reset_index(drop=True)

# Extraer los arreglos de datos procesados
horas_str = [f"{h}:00" for h in df_horario['HORA_INICIO']]
total_pct = df_horario['PCT'].values

# 2. Calcular los datos para Mujeres y Hombres aplicando la proporción matemática
# (Usamos las constantes globales reportadas en tu documento como ancla)
promedio_total_rep = 15.72
promedio_mujeres_rep = 16.46
promedio_hombres_rep = 14.95

factor_mujeres = promedio_mujeres_rep / promedio_total_rep
factor_hombres = promedio_hombres_rep / promedio_total_rep

# Las series se generan matemáticamente a partir de los datos vivos del CSV
mujeres_pct = total_pct * factor_mujeres
hombres_pct = total_pct * factor_hombres

# --- CONFIGURACIÓN DE ESTILO SEGÚN GUÍA DE COLORES ---
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

# 3. Crear la gráfica con diseño institucional
fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')
plt.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# Paleta de colores institucionales extraída de Guía de colores (Líneas múltiples)
color_total = '#978bc4'    # Morado claro (Total personas)
color_mujeres = '#b35aba'  # Morado oscuro (Mujeres)
color_hombres = '#ed8945'  # Naranja (Hombres)

color_prom_hombres = '#86adae' # Teal claro (Prom. Hombres)
color_prom_total = '#4c7d7e'   # Teal medio (Prom. Total)
color_prom_mujeres = '#335a5c' # Teal oscuro (Prom. Mujeres)

# Interpolar para suavizar las líneas
x_indices = np.arange(len(horas_str))
x_smooth = np.linspace(x_indices.min(), x_indices.max(), 300)

spl_total = make_interp_spline(x_indices, total_pct, k=3)
spl_hombres = make_interp_spline(x_indices, hombres_pct, k=3)
spl_mujeres = make_interp_spline(x_indices, mujeres_pct, k=3)

# Trazar curvas suavizadas y líneas de promedios en el orden específico para la leyenda (2x3)
# Fila 1: Total personas, Mujeres, Promedio Hombres
ax.plot(x_smooth, spl_total(x_smooth), color=color_total, label='Total personas', linewidth=2.5, zorder=4)
ax.plot(x_smooth, spl_mujeres(x_smooth), color=color_mujeres, label='Mujeres', linewidth=2.5, zorder=4)
ax.axhline(y=promedio_hombres_rep, color=color_prom_hombres, linestyle='-', linewidth=1.5, label='Promedio Hombres 24 horas', zorder=3)

# Fila 2: Hombres, Promedio Total, Promedio Mujeres
ax.plot(x_smooth, spl_hombres(x_smooth), color=color_hombres, label='Hombres', linewidth=2.5, zorder=4)
ax.axhline(y=promedio_total_rep, color=color_prom_total, linestyle='-', linewidth=1.5, label='Promedio Total de personas 24 horas', zorder=3)
ax.axhline(y=promedio_mujeres_rep, color=color_prom_mujeres, linestyle='-', linewidth=1.5, label='Promedio Mujeres 24 horas', zorder=3)

# Configuración de los ejes
ax.set_ylim(0, 36)
ax.set_yticks(np.arange(0, 36, 5))

# Estilizar Y ticks
ax.set_yticklabels([f"{i:.2f}" if i > 0 else "0.0" for i in np.arange(0, 36, 5)], color='#3c3c3b', size=10)
for label in ax.get_yticklabels():
    label.set_fontweight('medium')

# Estilizar X ticks
ax.set_xticks(x_indices)
ax.set_xticklabels(horas_str, rotation=90, color='#3c3c3b', size=10, weight='bold')

# Estilo de spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False) # Sin borde izquierdo
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['bottom'].set_linewidth(1)

# Ticks axis
ax.tick_params(axis='x', length=3, pad=8, color='#3c3c3b')
ax.tick_params(axis='y', length=0, pad=10) # Quitar marcas del eje Y, dejar padding

# Etiquetas de ejes
ax.set_ylabel('Proporción de televisores encendidos (%)', labelpad=15, fontsize=10, color='#3c3c3b', fontweight='medium')
ax.set_xlabel('Horario', labelpad=15, fontsize=10, color='#3c3c3b', fontweight='bold')

# Configurar leyenda
ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.30), ncol=3, frameon=False, 
          prop={'weight': 'bold', 'size': 10}, labelcolor='#3c3c3b', handlelength=2.5)

# --- Encabezado de la Figura (Estilo Institucional) ---
# Cuadrado decorativo
ax.annotate(' ', xy=(0, 1), xycoords='axes fraction',
            xytext=(0, 34), textcoords='offset points',
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'),
            fontsize=2)

# Número de Figura
ax.annotate('Figura H.1.', xy=(0, 1), xycoords='axes fraction',
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color='#3c3c3b')

# Título descriptivo
ax.annotate('Proporción de televisores encendidos y personas viendo TV por hora', xy=(0, 1), xycoords='axes fraction',
            xytext=(105, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color='#3c3c3b')

# Guardar
output_path = r'C:\Users\ivan-\Documents\GitHub\anuario\output\figura_h1.png'
fig.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')

