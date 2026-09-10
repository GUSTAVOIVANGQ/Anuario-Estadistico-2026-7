import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import numpy as np

print("Cargando la base de datos de Internet Fijo...")
# 1. Cargar Base de Datos
df = pd.read_excel(r'C:\Users\ivan-\Documents\GitHub\anuario\datos\F.16\Tercera Encuesta 2023_Int&TV.xlsx')

# 2. Factor de Expansión (Ponderador)
w_col = 'Factor de Expansión Final Normalizado que considera calibración (post-estratificación) por sexo y grupos de edad 5 (redondeos corregidos) (a cifras del Censo INEGI, 2020)'
df[w_col] = pd.to_numeric(df[w_col], errors='coerce')

# 3. Filtro para usuarios de Internet Fijo
col_internet = 'De la siguiente lista de servicios, ¿podría decirme cuáles tiene contratados o cuenta con ellos en su hogar? Conexión a Internet fijo en su hogar (incluye conexión Wi-Fi)'
df_internet = df[df[col_internet] == 'Sí'].copy()

# 4. Cálculo de ponderadores totales
total_w = df_internet[w_col].sum()
w_mujeres = df_internet[df_internet['Género'] == 'Mujer'][w_col].sum()
w_hombres = df_internet[df_internet['Género'] == 'Hombre'][w_col].sum()

def get_mask(col_name):
    full_name = f'Independientemente de si ha sido o no víctima de violencia en Internet, ¿qué haría si la experimentara o qué hizo en caso de haberla experimentado? {col_name}'
    return df_internet[full_name].apply(lambda x: str(x).strip().lower() == 'sí')

def get_pct(mask):
    w_t = df_internet.loc[mask, w_col].sum()
    w_m = df_internet.loc[mask & (df_internet['Género'] == 'Mujer'), w_col].sum()
    w_h = df_internet.loc[mask & (df_internet['Género'] == 'Hombre'), w_col].sum()
    return (w_t/total_w)*100, (w_m/w_mujeres)*100, (w_h/w_hombres)*100

# 5. Agrupación y Mapeo de Categorías
categories = [
    {'label': 'Denunciar ante la\nPolicía Cibernética', 'mask': get_mask('Denunciar ante la Policía Cibernética')},
    {'label': 'Denunciar a las autoridades\n(Ministerio Público, escolares\ny/o centro de trabajo, Seguridad\nPública, CNDH, SEDENA)',
     'mask': get_mask('Denunciar ante el Ministerio Público') | get_mask('Denunciar ante autoridades escolares/centro de trabajo') | get_mask('Denunciar a Seguridad Pública') | get_mask('Denunciar ante la Comisión Nacional de Derechos Humanos (CNDH)') | get_mask('Reportarlo ante la SEDENA') | get_mask('Denunciar/ Reportarlo (No especifica ante qué autoridades o dónde haría la denuncia/reporte)')},
    {'label': 'Bloquear a la persona', 'mask': get_mask('Bloquear a la persona')},
    {'label': 'Denunciar en la platafor-\nma digital/red social', 'mask': get_mask('Denunciar en la plataforma/red social')},
    {'label': 'Cerrar la cuenta\n(red social, correo\nelectrónico)', 'mask': get_mask('Cerrar la cuenta (red social/correo electrónico)')},
    {'label': 'No hacer algo/ Hacer\ncaso omiso/ Ignorar', 'mask': get_mask('No hacer caso/ Hacer caso omiso/ Ignorar') | get_mask('Nada')},
    {'label': 'Cambiar número de\nteléfono', 'mask': get_mask('Cambiar número de teléfono')}
]

labels = [c['label'] for c in categories]
results_gen, results_muj, results_hom = [], [], []

for c in categories:
    t, m, h = get_pct(c['mask'])
    results_gen.append(t)
    results_muj.append(m)
    results_hom.append(h)

# 6. Configuración de Gráfica
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Colores institucionales alineados a la Paleta Teal
COLOR_GENERAL = '#afafaf'  # Gris verde
COLOR_MUJERES = '#86adae'  # Teal claro
COLOR_HOMBRES = '#335a5c'  # Teal oscuro
color_texto = '#3c3c3b'

x = np.arange(len(labels))
width = 0.25 

# Dibujar las barras
rects1 = ax.bar(x - width, results_gen, width, label='General', color=COLOR_GENERAL, edgecolor='none', zorder=2)
rects2 = ax.bar(x, results_muj, width, label='Mujeres', color=COLOR_MUJERES, edgecolor='none', zorder=2)
rects3 = ax.bar(x + width, results_hom, width, label='Hombres', color=COLOR_HOMBRES, edgecolor='none', zorder=2)

# 7. Etiquetas de datos (Chips estilo F.11)
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

autolabel(rects1)
autolabel(rects2)
autolabel(rects3)

# 8. Diseño limpio de Ejes
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9, fontweight='normal', color=color_texto)

ax.set_ylim(0, max(max(results_gen), max(results_muj), max(results_hom)) * 1.25)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# 9. Títulos
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura F.16.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Acciones en caso de experimentar violencia digital en Internet", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# 10. Leyenda
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.12), ncol=3, fontsize=10, frameon=False, handlelength=2.5)

# 11. Notas al pie
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = ('IFT con información de la Tercera Encuesta 2023, Usuarios de Servicios de Telecomunicaciones.\n'
               'Para mayor información consultar: https://www.ift.org.mx/usuarios-y-audiencias/tercer-encuesta-2023-usuarios-de-servicios-de-telecomunicaciones.')
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.04
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
nota_text = 'Respuesta múltiple no suma 100%. La pregunta corresponde al cuestionario de Internet fijo.'
fig.text(x_start + 0.025, y_nota, nota_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# 12. Guardar
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
plt.savefig(r'C:\Users\ivan-\Documents\GitHub\anuario\output\figura_f16.png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("¡Figura F.16 construida y validada con estilo A.9!")