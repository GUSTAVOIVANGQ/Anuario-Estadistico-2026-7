import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys

try:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

print("Cargando y procesando la base de datos...")
# 1. Cargar datos
df = pd.read_excel(r'C:\Users\ivan-\Documents\GitHub\anuario\datos\F.10\Tercera Encuesta 2023_Int&TV.xlsx')

# 2. Definir columnas clave
w_col = 'Factor de Expansión Final Normalizado que considera calibración (post-estratificación) por sexo y grupos de edad 5 (redondeos corregidos) (a cifras del Censo INEGI, 2020)'
df[w_col] = pd.to_numeric(df[w_col], errors='coerce')

col_internet = 'De la siguiente lista de servicios, ¿podría decirme cuáles tiene contratados o cuenta con ellos en su hogar? Conexión a Internet fijo en su hogar (incluye conexión Wi-Fi)'

# 3. Filtrar a los usuarios de Internet Fijo y calcular el peso total
df_internet = df[df[col_internet] == 'Sí'].copy()
total_weight = df_internet[w_col].sum()

# 4. Diccionario para mapear
label_mapping = {
    'Menores de edad': 'Niños, niñas y\nadolescentes',
    'Mujeres': 'Mujeres',
    'Todas las personas son vulnerables': 'Todas las personas\nson vulnerables',
    'Adultos mayores / Personas de la tercera edad': 'Personas adultas\nmayores',
    'Personas con discapacidad': 'Personas con\ndiscapacidad',
    'Integrantes de la comunidad LGBTIQ+': 'Personas de la\ncomunidad LGBTIQ+',
    'Personas indígenas': 'Personas indígenas',
    'Hombres': 'Hombres',
    'Personas negras o afrodescendientes': 'Personas\nafrodescendientes'
}

# 5. Calcular porcentajes dinámicamente
resultados_dinamicos = {}
violencia_cols = [col for col in df.columns if 'mayor riesgo' in col.lower()]

for col in violencia_cols:
    if '? ' in col:
        category = col.split('? ')[1] 
        if category in label_mapping:
            label = label_mapping[category]
            mask = df_internet[col].apply(lambda x: str(x).strip().lower() == 'sí')
            weighted_sum = df_internet.loc[mask, w_col].sum()
            pct = (weighted_sum / total_weight) * 100
            resultados_dinamicos[label] = pct

# 6. Ordenar resultados (Descendente para lectura de izquierda a derecha)
resultados_ordenados = sorted(resultados_dinamicos.items(), key=lambda item: item[1], reverse=True)
categorias = [item[0] for item in resultados_ordenados]
valores = [item[1] for item in resultados_ordenados]

# ==============================================================================
# 7. GRÁFICA VERTICAL ESTILO INSTITUCIONAL
# ==============================================================================
print("\nGenerando figura F.10 (Vertical)...")
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Colores institucionales
COLOR_DESTACADO = '#335a5c'  # Teal oscuro (para los top 2)
COLOR_RESTO = '#86adae'      # Teal claro
color_texto = '#3c3c3b'

# Asignar color dinámico (los primeros 2 lugares)
colores = [COLOR_DESTACADO if i < 2 else COLOR_RESTO for i in range(len(categorias))]

barras = ax.bar(categorias, valores, color=colores, width=0.6, edgecolor='none', zorder=2)

# Configuración de Ejes
ax.set_ylim(0, max(valores) * 1.15) # Margen para que las etiquetas no se corten arriba
ax.tick_params(axis='x', labelsize=10, colors=color_texto, length=0)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

# Grid y bordes canónicos
ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

# Etiquetas de datos (Chips estilo A.2)
for barra in barras:
    altura = barra.get_height()
    bar_color = barra.get_facecolor()
    ax.annotate(f'{altura:.1f}%',
                xy=(barra.get_x() + barra.get_width() / 2, altura),
                xytext=(0, 6),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

# ==============================================================================
# 8. ENCABEZADO Y NOTAS (BLOQUE INSTITUCIONAL)
# ==============================================================================
# Títulos
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura F.10.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Personas usuarias con mayor riesgo de ser víctimas de violencia digital a través de Internet", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Notas al pie
font_size_notes = 8
x_start = 0.08
y_fuente = 0.06

ax.annotate("Fuente: ", xy=(x_start, y_fuente), xycoords='figure fraction',
            fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
note1_content = 'IFT con datos de la Tercera Encuesta 2023.'
ax.annotate(note1_content, xy=(x_start, y_fuente), xycoords='figure fraction',
            xytext=(35, 0), textcoords='offset points',
            fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# Ajustes de layout
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

# Exportar
output_path = r'C:\Users\ivan-\Documents\GitHub\anuario\output\figura_f10.png'
plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"¡Listo! Gráfica generada y guardada en: {output_path}")
plt.close(fig)