import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import os
import textwrap

# ── Configuración de la fuente institucional ──
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

# Configuración de la figura
fig, ax = plt.subplots(figsize=(16, 10))
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis('off')

# Fondo de la figura (Blanco institucional según Guia_colores)
fig.patch.set_facecolor('white') 

# ── Colores Institucionales CRT y Configuración Base ──────────────────
CRT_VERDE_OSCURO = '#1a4043'
CRT_AZUL_VERDE   = '#2D7B8A'
CRT_DECORATIVO   = '#4a7d75'
CRT_VERDE_CLARO  = '#6cacad'

BLANCO           = '#ffffff'
COLOR_TEXTO      = '#3c3c3b'  # Gris institucional canónico
FONDO_TARJETA    = '#F8F8FA'  # facecolor_axes base

# ══════════════════════════════════════════
# Funciones helper
# ══════════════════════════════════════════
def caja(ax, x, y, w, h, color, radius=0.3, zorder=2):
    """Dibuja una caja con bordes redondeados."""
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle=f"round,pad=0,rounding_size={radius}",
                          linewidth=0, facecolor=color, zorder=zorder)
    ax.add_patch(rect)

def burbuja(ax, x, y, w, h, texto, fontsize=10.5):
    """Dibuja una burbuja blanca y auto-ajusta el texto en su interior de forma centrada."""
    caja(ax, x, y, w, h, BLANCO, radius=0.2, zorder=4)
    
    lineas = texto.split('\n')
    texto_final = ""
    for linea in lineas:
        texto_final += textwrap.fill(linea, width=48) + "\n"
        
    ax.text(x + 0.3, y + (h / 2), texto_final.strip(),
            fontsize=fontsize, va='center', ha='left',
            color=COLOR_TEXTO, linespacing=1.5, zorder=5)

def dibujar_icono_placeholder(ax, x, y, color_base, es_ia=True):
    """Dibuja formas para los iconos usando la paleta institucional."""
    caja(ax, x, y, 1.6, 1.6, color_base, radius=0.2, zorder=3)
    if es_ia:
        circle = plt.Circle((x+0.8, y+0.9), 0.4, color='white', alpha=0.9, zorder=4)
        ax.add_patch(circle)
        ax.text(x+0.8, y+0.9, '</>', fontsize=12, fontweight='bold', color=CRT_VERDE_OSCURO, ha='center', va='center', zorder=5)
    else:
        rect = FancyBboxPatch((x+0.3, y+0.6), 1.0, 0.6, boxstyle="round,pad=0,rounding_size=0.1", color='white', alpha=0.9, zorder=4)
        ax.add_patch(rect)
        ax.text(x+0.8, y+0.9, 'CHAT', fontsize=11, fontweight='bold', color=CRT_AZUL_VERDE, ha='center', va='center', zorder=5)

# ══════════════════════════════════════════
# Fondo principal (Tarjeta gris claro institucional)
# ══════════════════════════════════════════
caja(ax, 0.2, 0.2, 15.6, 9.6, FONDO_TARJETA, radius=0.3, zorder=1)

# ══════════════════════════════════════════
# Encabezado de la Figura (Normativa de Títulos)
# ══════════════════════════════════════════
# Cuadrado decorativo oficial (CRT Verde Decorativo)
caja(ax, 0.5, 9.3, 0.15, 0.25, color=CRT_DECORATIVO, radius=0.04, zorder=2)

# Título dividido por pesos (14 pt)
ax.text(0.8, 9.42, 'Figura E.2.', fontsize=14, fontweight='bold', color=COLOR_TEXTO, va='center')
ax.text(2.1, 9.42, 'Principales hallazgos de la Inteligencia Artificial (IA) y Chat GPT', fontsize=14, fontweight='medium', color=COLOR_TEXTO, va='center')

# ══════════════════════════════════════════
# PANEL IZQUIERDO – Inteligencia Artificial
# ══════════════════════════════════════════
# Fondo Verde muy oscuro CRT
caja(ax, 0.5, 1.2, 7.3, 7.8, CRT_VERDE_OSCURO, radius=0.4)

# Icono con contraste (Verde Decorativo)
dibujar_icono_placeholder(ax, 1.0, 5.0, CRT_DECORATIVO, es_ia=True)
ax.text(1.8, 4.0, 'Inteligencia\nArtificial (IA)', fontsize=14, fontweight='bold', color=BLANCO, ha='center', va='top', zorder=5, linespacing=1.3)

# Textos Panel Izquierdo
txt1 = "> Es accesible, amigable y aporta muchos beneficios en diferentes áreas de la vida: laboral, escolar, salud y hogar, entre los más mencionados."
burbuja(ax, 3.1, 7.6, 4.4, 1.1, txt1)

txt2 = ("> Los programas de IA pueden agruparse en tres categorías:\n"
        "1. Los programas en formato de texto que sirven como una introducción a la IA: ChatGPT, IA Bing y Bard de Google.\n"
        "2. Los programas que se utilizan para hacer presentaciones y para desarrollar contenido en redes sociales, como: Canva, Beautiful.ai, Synthesia y Pictory.\n"
        "3. Los programas dirigidos a segmentos muy concretos como publicidad, negocios, atención a clientes son: Jasper, Brand24 y ManyChat.")
burbuja(ax, 3.1, 3.5, 4.4, 3.8, txt2)

txt3 = "> Las desventajas que pudieran tenerse son que no se dé la protección de privacidad de datos y los ciberdelitos. Es por ello que los entrevistados reconocen la importancia de la regulación del uso de estos programas."
burbuja(ax, 3.1, 1.5, 4.4, 1.7, txt3)

# ══════════════════════════════════════════
# PANEL DERECHO – ChatGPT
# ══════════════════════════════════════════
# Fondo Azul Verde CRT
caja(ax, 8.2, 1.2, 7.3, 7.8, CRT_AZUL_VERDE, radius=0.4)

# Icono con contraste (Verde Claro)
dibujar_icono_placeholder(ax, 8.7, 5.0, CRT_VERDE_CLARO, es_ia=False)
ax.text(9.5, 4.0, 'ChatGPT', fontsize=14, fontweight='bold', color=BLANCO, ha='center', va='top', zorder=5)

# Textos Panel Derecho
txt4 = "> Es el programa de Inteligencia Artificial más conocido y utilizado."
burbuja(ax, 10.8, 7.6, 4.4, 1.1, txt4)

txt5 = "> Sorprende favorablemente la capacidad de resolver dudas, de redactar la información de forma concreta, organizada y sintetizada; además de que lo hace con una rapidez que agiliza el trabajo y tareas de cualquier persona que lo utilice."
burbuja(ax, 10.8, 5.6, 4.4, 1.7, txt5)

txt6 = "> Es atractivo para consultar temas laborales, escolares, de investigación, así como de cualquier cuestión de la vida cotidiana, desde recetas de cocina, consejos de salud, de entretenimiento, planes alimenticios, etcétera."
burbuja(ax, 10.8, 3.6, 4.4, 1.7, txt6)

txt7 = ("> Entre las desventajas del ChatGPT se encuentran:\n"
        "a) no brinda respuestas completas o da respuestas imprecisas y\n"
        "b) se tiene presente el hackeo, problemas con la privacidad de los datos personales y que puede ser utilizado para cometer fraudes y ciberdelitos.")
burbuja(ax, 10.8, 1.5, 4.4, 1.8, txt7)

# ══════════════════════════════════════════
# Pie de figura (Alineación estricta de Notas y Fuentes)
# ══════════════════════════════════════════
fuente_texto_1 = "IFT, con información del Estudio Cualitativo. Conocimiento y Percepción Sobre La Inteligencia Artificial (IA) y ChatGPT 2023. Para más información consultar:"
fuente_texto_2 = "https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/estudiodeiaychatgpt2023_0.pdf"
nota_texto = "Reporte sobre el estudio cualitativo de un grupo de personas."

# Separación Bold/Normal vía offsets (8 pt)
ax.annotate("Fuente:", xy=(0.5, 0.85), xycoords='data', fontweight='bold', fontsize=8, color=COLOR_TEXTO, va='top')
ax.annotate(fuente_texto_1, xy=(0.5, 0.85), xycoords='data', xytext=(42, 0), textcoords='offset points', fontweight='normal', fontsize=8, color=COLOR_TEXTO, va='top')

# URL con el color destacado Azul Verde de la CRT
ax.annotate(fuente_texto_2, xy=(0.5, 0.65), xycoords='data', fontweight='normal', fontsize=8, color=CRT_AZUL_VERDE, va='top')

ax.annotate("Nota:", xy=(0.5, 0.45), xycoords='data', fontweight='bold', fontsize=8, color=COLOR_TEXTO, va='top')
ax.annotate(nota_texto, xy=(0.5, 0.45), xycoords='data', xytext=(32, 0), textcoords='offset points', fontweight='normal', fontsize=8, color=COLOR_TEXTO, va='top')

# ══════════════════════════════════════════
# Exportación (DPI canónico a 200)
# ══════════════════════════════════════════
plt.tight_layout(pad=0)
output_dir = r"C:\Users\ivan-\Documents\GitHub\anuario\output"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "figura_e2.png")

fig.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')

print("Guardado correctamente aplicando la Guía de Estilos de la CRT.")