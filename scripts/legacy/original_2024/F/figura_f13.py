import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
import numpy as np

try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

print("Cargando base de datos de Telefonía Móvil...")
# 1. Cargar la base
df_movil = pd.read_excel(r'C:\Users\ivan-\Documents\GitHub\anuario\datos\F.13\Tercera Encuesta 2023_Tel Móvil.xlsx')

# 2. Definir factor de expansión y filtro
w_col = 'Calibrador (post-estratificación) final que considera distribución de líneas telefónicas móviles por entidad federativa y población por grupos de edad 5 (redondeos corregidos)'
df_movil[w_col] = pd.to_numeric(df_movil[w_col], errors='coerce')

user_col = '¿Es usted\xa0el usuario habitual de esta línea de teléfono móvil o celular?'
df_filtered = df_movil[df_movil[user_col].astype(str).str.strip().str.lower() == 'sí'].copy()

# 3. Pesos totales por género
w_hombres = df_filtered[df_filtered['Género'] == 'Hombre'][w_col].sum()
w_mujeres = df_filtered[df_filtered['Género'] == 'Mujer'][w_col].sum()

# 4. Mapeo
label_mapping = {
    'Menores de edad': 'Niños, niñas y\nadolescentes',
    'Adultos mayores / Personas de la tercera edad': 'Personas adultas\nmayores',
    'Mujeres': 'Mujeres',
    'Parientes (familiares)': 'Parientes\n(familiares)',
    'Hombres': 'Hombres',
    'Personas con discapacidad': 'Personas con\ndiscapacidad',
    'Todas las personas son vulnerables': 'Todas las personas\nson vulnerables'
}

categorias = [
    'Niños, niñas y\nadolescentes',
    'Personas adultas\nmayores',
    'Mujeres',
    'Parientes\n(familiares)',
    'Hombres',
    'Personas con\ndiscapacidad',
    'Todas las personas\nson vulnerables'
]

# 5. Cálculo dinámico
violencia_cols = [c for c in df_movil.columns if 'mayor riesgo' in c.lower()]
results_h = {}
results_m = {}

for col in violencia_cols:
    if '? ' in col:
        categoria_col = col.split('? ')[1]
        if categoria_col in label_mapping:
            label = label_mapping[categoria_col]
            mask_si = df_filtered[col].apply(lambda x: str(x).strip().lower() == 'sí')
            df_si = df_filtered[mask_si]
            
            w_si_h = df_si[df_si['Género'] == 'Hombre'][w_col].sum()
            w_si_m = df_si[df_si['Género'] == 'Mujer'][w_col].sum()
            
            results_h[label] = (w_si_h / w_hombres) * 100
            results_m[label] = (w_si_m / w_mujeres) * 100

valores_h = [results_h[cat] for cat in categorias]
valores_m = [results_m[cat] for cat in categorias]

# ==============================================================================
# 6. GRÁFICA VERTICAL AGRUPADA ESTILO INSTITUCIONAL
# ==============================================================================
print("\nGenerando figura F.13 (Vertical)...")
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

x = np.arange(len(categorias))
width = 0.38

COLOR_MUJERES = '#86adae' # Teal claro
COLOR_HOMBRES = '#335a5c' # Teal oscuro
color_texto = '#3c3c3b'

rects_muj = ax.bar(x - width/2, valores_m, width, label='Mujeres', color=COLOR_MUJERES, edgecolor='none', zorder=2)
rects_hom = ax.bar(x + width/2, valores_h, width, label='Hombres', color=COLOR_HOMBRES, edgecolor='none', zorder=2)

# 7. Formato de etiquetas y grilla
ax.set_xticks(x)
ax.set_xticklabels(categorias, fontsize=10, fontweight='normal', color=color_texto)

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)
ax.tick_params(axis='x', length=0)

# Espacio dinámico para que los labels no se salgan del gráfico
max_y = max(max(valores_m), max(valores_h))
ax.set_ylim(0, max_y * 1.15) 

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

# Función para porcentajes al tope de la barra (Chips estilo A.2)
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        bar_color = rect.get_facecolor()
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                    bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

autolabel(rects_muj)
autolabel(rects_hom)

# ==============================================================================
# 8. ENCABEZADO Y NOTAS (BLOQUE INSTITUCIONAL)
# ==============================================================================
# Títulos
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura F.13.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Personas usuarias con mayor riesgo de ser víctimas de violencia digital a través del teléfono móvil. Por sexo", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Leyenda
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=2, fontsize=10, frameon=False, handlelength=2.5)

# Notas al pie
font_size_notes = 8
x_start = 0.08
y_fuente = 0.06

ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note_content = 'IFT con datos de la Tercera Encuesta 2023.'
ax.annotate(note_content, xy=(x_start, y_fuente), xycoords='figure fraction',
            xytext=(35, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# Ajustes de layout
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# Exportar
output_path = r'C:\Users\ivan-\Documents\GitHub\anuario\output\figura_f13.png'
plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"¡Gráfica F.13 generada exitosamente en: {output_path}")
plt.close(fig)