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
# 1. Cargar datos
df = pd.read_excel(r'C:\Users\ivan-\Documents\GitHub\anuario\datos\F.15\Tercera Encuesta 2023_Int&TV.xlsx')

# 2. Factor de expansión
w_col = [col for col in df.columns if 'Normalizado' in col and 'Factor' in col][0]
df[w_col] = pd.to_numeric(df[w_col], errors='coerce')

# 3. Filtrar Usuarios de Internet Fijo
col_internet = [col for col in df.columns if 'Internet fijo en su hogar' in col][0]
df_internet = df[df[col_internet].astype(str).str.upper().str.startswith('S')].copy()

# Encontrar columna de género
col_genero = [col for col in df.columns if 'nero' in col.lower() and col.lower().startswith('g')][0]

# 4. Suma de Pesos Poblacionales Totales y por Sexo
total_w = df_internet[w_col].sum()
w_hombres = df_internet[df_internet[col_genero].astype(str).str.upper().str.startswith('H')][w_col].sum()
w_mujeres = df_internet[df_internet[col_genero].astype(str).str.upper().str.startswith('M')][w_col].sum()

# 5. Mapeo de columnas con el texto exacto a mostrar en la gráfica
label_mapping = {
    'Evitar compartir información personal': 'Evitar compartir\ninformación\npersonal',
    'Evitar compartir contraseñas de sus dispositivos y/o aplicaciones': 'Evitar compartir\ncontraseñas de sus\ndispositivos y\naplicaciones',
    'Revisar un perfil antes de aceptarlo': 'Revisar un perfil\nantes de aceptarlo',
    'Ser más precavido al abrir links o archivos recibidos': 'Ser más precavido (a)\nal abrir links\no archivos recibidos',
    'Evitar subir información donde sea fácil ubicarle a usted o a su familia': 'Evitar subir información\ndonde sea fácil ubicarte\na usted o a su familia\n(ubicación, fotos y/o\nvideos)',
    'Redes sociales privadas solo para familiares y/o amistades': 'Redes sociales\nprivadas solo para\nfamiliares y/o\namistades',
    'Publicar fotos y/o videos con restricciones para no recibir acoso y evitar comentarios': 'Publicar fotos y/o\nvideos con restricciones\npara no recibir\nacoso y evitar\ncomentarios',
    'Cuestionarse sobre el contenido que publicará': 'Cuestionarse sobre\nel contenido que\npublicará',
    'Evitar ser muy activo en redes sociales': 'Evitar ser muy activo (a)\nen redes sociales\n(limitar publicaciones y\nno interactuar en\nredes sociales)',
    'Comentar con otras personas sobre lo que sucede y ve en redes sociales': 'Comentar con\notras personas\nsobre lo que\nsucede y ves en\nredes sociales'
}

cols_acciones = [col for col in df.columns if 'acciones realiza para protegerse o prevenir' in col.lower()]
cols_acciones = [c for c in cols_acciones if 'Ninguna' not in c and 'Otro' not in c and 'Ns/Nc' not in c and 'Ns / Nc' not in c]

# 6. Cálculo dinámico iterando sobre las acciones
results_gen, results_muj, results_hom, labels = [], [], [], []

for col in cols_acciones:
    label_found = None
    col_clean = col.split('? ')[-1].split('(')[0].strip().lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
    
    for k, v in label_mapping.items():
        k_clean = k.split('(')[0].strip().lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
        if k_clean in col_clean or col_clean in k_clean:
            label_found = v
            break
            
    if label_found:
        labels.append(label_found)
        mask_si = df_internet[col].astype(str).str.strip().str.upper().str.startswith('S')
        df_si = df_internet[mask_si]
        
        w_si_total = df_si[w_col].sum()
        w_si_hom = df_si[df_si[col_genero].astype(str).str.upper().str.startswith('H')][w_col].sum()
        w_si_muj = df_si[df_si[col_genero].astype(str).str.upper().str.startswith('M')][w_col].sum()
        
        results_gen.append((w_si_total / total_w) * 100 if total_w else 0)
        results_muj.append((w_si_muj / w_mujeres) * 100 if w_mujeres else 0)
        results_hom.append((w_si_hom / w_hombres) * 100 if w_hombres else 0)

# 7. Configuración de Gráfica (Estilo F.16)
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(18, 9.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Colores institucionales alineados a F.16
COLOR_GENERAL = '#afafaf'  # Gris verde
COLOR_MUJERES = '#86adae'  # Teal claro
COLOR_HOMBRES = '#335a5c'  # Teal oscuro
color_texto = '#3c3c3b'

x = np.arange(len(labels))
width = 0.25 

rects1 = ax.bar(x - width, results_gen, width, label='General', color=COLOR_GENERAL, edgecolor='none', zorder=2)
rects2 = ax.bar(x, results_muj, width, label='Mujeres', color=COLOR_MUJERES, edgecolor='none', zorder=2)
rects3 = ax.bar(x + width, results_hom, width, label='Hombres', color=COLOR_HOMBRES, edgecolor='none', zorder=2)

# 8. Etiquetas de datos (Chips estilo F.16, rotados a 90 por espacio)
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        bar_color = rect.get_facecolor()
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3, rotation=0,
                    bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

autolabel(rects1)
autolabel(rects2)
autolabel(rects3)

# 9. Diseño limpio de Ejes
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=9, fontweight='normal', color=color_texto)

ax.set_ylim(0, max(max(results_gen), max(results_muj), max(results_hom)) * 1.35)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.grid(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)

# 10. Títulos (Estilo F.16)
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura F.15.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Acciones realizadas para protegerse o prevenir la violencia digital a través de Internet (por sexo)", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# 11. Leyenda
handles, labels_leg = ax.get_legend_handles_labels()
fig.legend(handles, labels_leg, loc='lower center', bbox_to_anchor=(0.5, 0.09), ncol=3, fontsize=10, frameon=False, handlelength=2.5)

# 12. Notas al pie
font_size_notes = 8
x_start = 0.05
y_fuente = 0.06

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = ('IFT con información de la Tercera Encuesta 2023, Usuarios de Servicios de Telecomunicaciones.\n'
               'Para mayor información consultar: https://www.ift.org.mx/usuarios-y-audiencias/tercer-encuesta-2023-usuarios-de-servicios-de-telecomunicaciones.')
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.02
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
nota_text = 'Respuesta múltiple no suma 100%. La pregunta corresponde al cuestionario de Internet fijo.'
fig.text(x_start + 0.025, y_nota, nota_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# 13. Guardar
fig.subplots_adjust(left=0.05, right=0.95, top=0.85, bottom=0.24)
plt.savefig(r'C:\Users\ivan-\Documents\GitHub\anuario\output\figura_f15.png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("¡Figura F.15 construida y validada con el estilo F.16!")