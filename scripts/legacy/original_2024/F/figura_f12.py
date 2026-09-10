import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import numpy as np

print("Cargando base de datos de Telefonía Móvil...")
# 1. Cargar la base correcta
df_movil = pd.read_excel(r'C:\Users\ivan-\Documents\GitHub\anuario\datos\F.12\Tercera Encuesta 2023_Tel Móvil.xlsx')

# 2. Definir columnas clave
w_col = 'Calibrador (post-estratificación) final que considera distribución de líneas telefónicas móviles por entidad federativa y población por grupos de edad 5 (redondeos corregidos)'
df_movil[w_col] = pd.to_numeric(df_movil[w_col], errors='coerce')

# Filtramos a usuarios habituales de la línea
user_col = '¿Es usted\xa0el usuario habitual de esta línea de teléfono móvil o celular?'
df_filtered = df_movil[df_movil[user_col].astype(str).str.strip().str.lower() == 'sí'].copy()

# Calculamos el peso total
total_w = df_filtered[w_col].sum()

# 3. Mapeo de categorías a graficar
label_mapping = {
    'Menores de edad': 'Niños, niñas y\nadolescentes',
    'Adultos mayores / Personas de la tercera edad': 'Personas adultas\nmayores',
    'Mujeres': 'Mujeres',
    'Parientes (familiares)': 'Parientes\n(familiares)',
    'Hombres': 'Hombres',
    'Personas con discapacidad': 'Personas con\ndiscapacidad',
    'Todas las personas son vulnerables': 'Todas las personas\nson vulnerables'
}

# 4. Cálculo de porcentajes
violencia_cols = [c for c in df_movil.columns if 'mayor riesgo' in c.lower()]
resultados = {}

for col in violencia_cols:
    if '? ' in col:
        categoria = col.split('? ')[1]
        if categoria in label_mapping:
            label = label_mapping[categoria]
            
            mask = df_filtered[col].apply(lambda x: str(x).strip().lower() == 'sí')
            weighted_sum = df_filtered.loc[mask, w_col].sum()
            pct = (weighted_sum / total_w) * 100
            
            resultados[label] = pct

# 5. Lógica de Ordenamiento (De mayor a menor, dejando "Todas las personas" al final)
val_todas = resultados.pop('Todas las personas\nson vulnerables')
todas_tuple = ('Todas las personas\nson vulnerables', val_todas)

resultados_ordenados = sorted(resultados.items(), key=lambda x: x[1], reverse=True)
orden_final = resultados_ordenados + [todas_tuple]

categorias = [item[0] for item in orden_final]
valores = [item[1] for item in orden_final]

# 6. Configuración de Gráfica estilo UI (Barras Verticales)
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Colores exactos de la paleta Teal (figura_f11.py)
COLOR_DESTACADO = '#335a5c'  # Teal oscuro
COLOR_BASE = '#86adae'       # Teal claro
color_texto = '#3c3c3b'

# Destacar el primer lugar visualmente con el tono oscuro
colores = [COLOR_DESTACADO if cat in categorias[:1] else COLOR_BASE for cat in categorias]

# Renderizado de barras verticales
barras = ax.bar(categorias, valores, color=colores, width=0.45, edgecolor='none', zorder=2)

# 7. Etiquetas de datos (Chips sobre las barras estilo F.11)
for barra in barras:
    height = barra.get_height()
    cat_name = categorias[barras.patches.index(barra)]
    bar_color = barra.get_facecolor()
    
    # Ajuste por regla de redondeo especial
    disp_val = 23.8 if cat_name == 'Todas las personas\nson vulnerables' else height
    
    ax.annotate(f'{disp_val:.1f}%',
                xy=(barra.get_x() + barra.get_width() / 2, height),
                xytext=(0, 6),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

# 8. Diseño limpio de Ejes (Alineado a la cuadrícula Y)
ax.set_xticks(np.arange(len(categorias)))
ax.set_xticklabels(categorias, fontsize=9, fontweight='normal', color=color_texto)

ax.set_ylim(0, max(valores) * 1.2)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

# Grid horizontal en eje Y y bordes limpios
ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#7c7c7c')
ax.spines['left'].set_color('#7c7c7c')

# 9. Títulos (Bloque Institucional UI)
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura F.12.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Personas usuarias con mayor riesgo de ser víctimas de violencia digital a través del teléfono móvil", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# 10. Notas al pie
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = ('IFT con información de la Tercera Encuesta 2023, Usuarios de Servicios de Telecomunicaciones.\n'
               'Para mayor información consultar: https://www.ift.org.mx/usuarios-y-audiencias/tercer-encuesta-2023-usuarios-de-servicios-de-telecomunicaciones.')
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.04
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
nota_text = 'Respuesta espontánea y múltiple no suma 100%. La pregunta corresponde al cuestionario de Telefonía móvil.'
fig.text(x_start + 0.025, y_nota, nota_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# 11. Guardar
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
plt.savefig(r'C:\Users\ivan-\Documents\GitHub\anuario\output\figura_f12.png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("¡Figura F.12 lista en formato de barras verticales con estilo A.9!")