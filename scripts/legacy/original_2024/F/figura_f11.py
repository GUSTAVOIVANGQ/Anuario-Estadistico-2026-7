import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import numpy as np

print("Cargando y procesando la base de datos...")
# 1. Cargar datos
df = pd.read_excel(r'C:\Users\ivan-\Documents\GitHub\anuario\datos\F.11\Tercera Encuesta 2023_Int&TV.xlsx')

# 2. Definir columnas clave
w_col = [col for col in df.columns if 'Normalizado' in col and 'Factor' in col][0]
df[w_col] = pd.to_numeric(df[w_col], errors='coerce')

col_internet = [col for col in df.columns if 'Internet fijo en su hogar' in col][0]

# 3. Filtrar usuarios de Internet Fijo
df_internet = df[df[col_internet].astype(str).str.upper().str.startswith('S')].copy()

# Encontrar columna de género
col_genero = [col for col in df.columns if 'nero' in col.lower() and col.lower().startswith('g')][0]

# 4. Calcular pesos totales de la muestra poblacional por género
w_hombres = df_internet[df_internet[col_genero].astype(str).str.upper().str.startswith('H')][w_col].sum()
w_mujeres = df_internet[df_internet[col_genero].astype(str).str.upper().str.startswith('M')][w_col].sum()

# 5. Diccionario y orden de categorías según la Figura F.11
label_mapping = {
    'Menores de edad': 'Niños, niñas y\nadolescentes',
    'Mujeres': 'Mujeres',
    'Adultos mayores / Personas de la tercera edad': 'Personas adultas\nmayores',
    'Personas con discapacidad': 'Personas con\ndiscapacidad',
    'Integrantes de la comunidad LGBTIQ+': 'Personas de la\ncomunidad LGBTIQ+',
    'Personas ind': 'Personas indígenas',
    'Hombres': 'Hombres',
    'Personas negras o afrodescendientes': 'Personas\nafrodescendientes',
    'Todas las personas son vulnerables': 'Todas las personas\nson vulnerables'
}

pdf_order = [
    'Niños, niñas y\nadolescentes',
    'Mujeres',
    'Personas adultas\nmayores',
    'Personas con\ndiscapacidad',
    'Personas de la\ncomunidad LGBTIQ+',
    'Personas indígenas',
    'Hombres',
    'Personas\nafrodescendientes',
    'Todas las personas\nson vulnerables'
]

# 6. Cálculo dinámico iterando sobre las columnas de violencia
violencia_cols = [col for col in df.columns if 'mayor riesgo' in col.lower()]
results_hombres = {}
results_mujeres = {}

for col in violencia_cols:
    if '? ' in col:
        category = col.split('? ')[1]
        label = None
        for k, v in label_mapping.items():
            if k in category:
                label = v
                break
        
        if label:
            # Filtramos los que respondieron que "Sí"
            mask_si = df_internet[col].astype(str).str.strip().str.upper().str.startswith('S')
            df_si = df_internet[mask_si]
            
            # Sumamos los ponderadores de los "Sí" separados por género
            w_si_hombres = df_si[df_si[col_genero].astype(str).str.upper().str.startswith('H')][w_col].sum()
            w_si_mujeres = df_si[df_si[col_genero].astype(str).str.upper().str.startswith('M')][w_col].sum()
            
            # Calculamos porcentaje matemático final
            results_hombres[label] = (w_si_hombres / w_hombres) * 100 if w_hombres else 0
            results_mujeres[label] = (w_si_mujeres / w_mujeres) * 100 if w_mujeres else 0

# Preparar listas para la gráfica
categorias = pdf_order
valores_hombres = [results_hombres[cat] for cat in categorias]
valores_mujeres = [results_mujeres[cat] for cat in categorias]

# 7. Configuración de Gráfica
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Colores institucionales extraídos de figura_a9.py
COLOR_HOMBRES = '#335a5c'  # Teal oscuro
COLOR_MUJERES = '#86adae'  # Teal claro
color_texto = '#3c3c3b'

x = np.arange(len(categorias))
width = 0.38 # Grosor de las barras

# Crear las dos barras paralelas por categoría
rects_hom = ax.bar(x - width/2, valores_hombres, width=width, label='Hombres', color=COLOR_HOMBRES, edgecolor='none', zorder=2)
rects_muj = ax.bar(x + width/2, valores_mujeres, width=width, label='Mujeres', color=COLOR_MUJERES, edgecolor='none', zorder=2)

# 8. Etiquetas de datos (Chips estilo A.2)
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

# 9. Diseño limpio de Ejes
ax.set_xticks(x)
ax.set_xticklabels(categorias, fontsize=9, fontweight='normal', color=color_texto)

ax.set_ylim(0, max(max(valores_hombres), max(valores_mujeres)) * 1.2)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

# Restaurar grid en eje Y y bordes
ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# 10. Títulos (Bloque Institucional UI)
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura F.11.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Personas usuarias con mayor riesgo de ser víctimas de violencia digital a través de la Internet, por sexo", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# 11. Leyenda
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=2, fontsize=10, frameon=False, handlelength=2.5)

# 12. Notas al pie
font_size_notes = 8
x_start = 0.08 # Alineado con el eje Y y el título
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')

fuente_text = ('IFT con información de la Tercera Encuesta 2023, Usuarios de Servicios de Telecomunicaciones.\n'
               'Para mayor información consultar: https://www.ift.org.mx/usuarios-y-audiencias/tercer-encuesta-2023-usuarios-de-servicios-de-telecomunicaciones.')
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.04 # Ajuste de espacio ordenado debajo de la fuente
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')

nota_text = 'Respuesta espontánea y múltiple no suma 100%. La pregunta corresponde al cuestionario de Internet fijo.'
fig.text(x_start + 0.025, y_nota, nota_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# 13. Guardar
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
plt.savefig(r'C:\Users\ivan-\Documents\GitHub\anuario\output\figura_f11.png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("¡Listo! Figura F.11 generada dinámicamente con estilo A.9.")