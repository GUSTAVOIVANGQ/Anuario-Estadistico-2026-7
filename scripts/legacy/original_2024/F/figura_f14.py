import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Polygon
import os
import textwrap

# ── Configuración de la fuente institucional ──
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

# Configuración de la figura
fig, ax = plt.subplots(figsize=(16, 10))
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis('off')

# Fondo de la figura
FONDO_TARJETA = '#F8F8FA'
fig.patch.set_facecolor('white') 

# ── Colores Institucionales CRT ──────────────────
CRT_VERDE_OSCURO = '#1a4043'
CRT_AZUL_VERDE   = '#2D7B8A'
CRT_DECORATIVO   = '#4a7d75'
CRT_VERDE_CLARO  = '#6cacad'

BLANCO           = '#ffffff'
COLOR_TEXTO      = '#3c3c3b'  # Gris institucional canónico
COLOR_ENLACE     = '#2D7B8A'  # Azul Verde de la CRT para el enlace

# ══════════════════════════════════════════
# Funciones helper
# ══════════════════════════════════════════
def caja(ax, x, y, w, h, color, radius=0.3, zorder=2):
    """Dibuja una caja con bordes redondeados."""
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle=f"round,pad=0,rounding_size={radius}",
                          linewidth=0, facecolor=color, zorder=zorder)
    ax.add_patch(rect)

def burbuja_dialogo(ax, x, y, w, h, texto, centrado=False, fontsize=10.5):
    """Dibuja una burbuja blanca con un pico a la izquierda y texto auto-ajustado."""
    # Caja principal de la burbuja
    caja(ax, x, y, w, h, BLANCO, radius=0.3, zorder=4)
    
    # Triángulo (pico) apuntando a la izquierda
    y_mid = y + (h / 2)
    pico = Polygon([[x, y_mid - 0.25], [x - 0.3, y_mid], [x, y_mid + 0.25]], 
                   closed=True, color=BLANCO, zorder=4)
    ax.add_patch(pico)
    
    if centrado:
        ax.text(x + (w / 2), y + (h / 2), texto,
                fontsize=fontsize, va='center', ha='center',
                color=COLOR_TEXTO, linespacing=1.5, zorder=5)
    else:
        lineas = texto.split('\n')
        texto_final = ""
        for linea in lineas:
            texto_final += textwrap.fill(linea, width=44) + "\n"
            
        ax.text(x + 0.35, y + (h / 2), texto_final.strip(),
                fontsize=fontsize, va='center', ha='left',
                color=COLOR_TEXTO, linespacing=1.5, zorder=5)

def dibujar_ilustracion_placeholder(ax, x, y, panel='izquierdo'):
    """Marcador visual de posición para las ilustraciones de las chicas."""
    circle = plt.Circle((x, y), 1.6, color=BLANCO, alpha=0.15, zorder=3)
    ax.add_patch(circle)
    texto = "[Ilustración\nLaptop]" if panel == 'izquierdo' else "[Ilustración\nManos]"
    ax.text(x, y, texto, fontsize=12, color=BLANCO, alpha=0.7, ha='center', va='center', zorder=5)

# ══════════════════════════════════════════
# Fondo principal (Tarjeta gris claro institucional)
# ══════════════════════════════════════════
caja(ax, 0.2, 1.2, 15.6, 8.7, FONDO_TARJETA, radius=0.3, zorder=1)

# ══════════════════════════════════════════
# Encabezado de la Figura
# ══════════════════════════════════════════
# Cuadrado decorativo
caja(ax, 0.5, 9.35, 0.12, 0.12, color=CRT_DECORATIVO, radius=0.02, zorder=2)

# Título de la figura F.14
ax.text(0.7, 9.4, 'Figura F.14.', fontsize=14, fontweight='bold', color=COLOR_TEXTO, va='center')
ax.text(2.1, 9.4, 'Medidas preventivas y de protección ante la violencia digital', fontsize=14, fontweight='medium', color=COLOR_TEXTO, va='center')

# ══════════════════════════════════════════
# PANEL IZQUIERDO – Medidas preventivas
# ══════════════════════════════════════════
# Fondo Verde Oscuro CRT
caja(ax, 0.6, 1.5, 7.3, 7.5, CRT_VERDE_OSCURO, radius=0.3)

# Placeholder de la chica con la laptop
dibujar_ilustracion_placeholder(ax, 2.2, 6.2, 'izquierdo')

# Título inferior del panel
ax.text(1.0, 3.8, 'Medidas preventivas\npara evitar ser\nvíctima de violencia\ndigital', 
        fontsize=16, fontweight='bold', color=BLANCO, ha='left', va='top', zorder=5, linespacing=1.2)

# Burbujas panel izquierdo
txt_izq_1 = "Cuidar el tipo de información que comparten, así como evitar compartir información personal privada, de ellas mismas y de sus familiares."
burbuja_dialogo(ax, 4.0, 7.2, 3.6, 1.3, txt_izq_1)

txt_izq_2 = "Tener contacto solamente con personas conocidas. No aceptar a desconocidos (as)."
burbuja_dialogo(ax, 4.0, 5.7, 3.6, 1.1, txt_izq_2)

txt_izq_3 = "No entrar a sitios, ni links desconocidos, aunque parezcan muy atractivos."
burbuja_dialogo(ax, 4.0, 4.2, 3.6, 1.1, txt_izq_3)

txt_izq_4 = "Utilizar los filtros de seguridad que las mismas plataformas digitales proporcionan para restringir a quienes se les comparte la información."
burbuja_dialogo(ax, 4.0, 2.0, 3.6, 1.6, txt_izq_4)

# ══════════════════════════════════════════
# PANEL DERECHO – Medidas de protección
# ══════════════════════════════════════════
# Fondo Azul Verde CRT
caja(ax, 8.3, 1.5, 7.3, 7.5, CRT_AZUL_VERDE, radius=0.3)

# Placeholder de la chica rodeada
dibujar_ilustracion_placeholder(ax, 9.8, 6.2, 'derecho')

# Título inferior del panel
ax.text(8.8, 4.1, 'Medidas de\nprotección una\nvez que han sido\nvíctimas de\nviolencia digital', 
        fontsize=16, fontweight='bold', color=BLANCO, ha='left', va='top', zorder=5, linespacing=1.2)

# Burbujas panel derecho
txt_der_1 = "En casos menos delicados hacer caso omiso a comentarios negativos, provocaciones, ataques."
burbuja_dialogo(ax, 11.5, 7.3, 3.7, 1.2, txt_der_1)

txt_der_2 = "Platicar su caso con familiares y amistades de mucha confianza para recibir su apoyo y consejo."
burbuja_dialogo(ax, 11.5, 5.6, 3.7, 1.3, txt_der_2)

txt_der_3 = "En casos mas graves, incluso acudir a la Policía Cibernética."
burbuja_dialogo(ax, 11.5, 4.1, 3.7, 1.1, txt_der_3)

txt_der_4 = "Ayuda psicológica."
burbuja_dialogo(ax, 11.5, 2.3, 3.7, 1.0, txt_der_4, centrado=True)

# ══════════════════════════════════════════
# Pie de figura (Fuentes y Notas)
# ══════════════════════════════════════════
# Coordenadas ajustadas al límite inferior
Y_FUENTE = 0.9
Y_URL = 0.7
Y_NOTA = 0.5

# Fuente
ax.annotate("Fuente:", xy=(0.5, Y_FUENTE), xycoords='data', fontweight='bold', fontsize=9, color=COLOR_TEXTO, va='center')
ax.annotate("IFT con información de la tercera Encuesta 2023, Usuarios de Servicios de Telecomunicaciones.", 
            xy=(0.5, Y_FUENTE), xycoords='data', xytext=(45, 0), textcoords='offset points', 
            fontweight='normal', fontsize=9, color=COLOR_TEXTO, va='center')

# URL
ax.annotate("Para más información consultar:", xy=(0.5, Y_URL), xycoords='data', fontweight='normal', fontsize=9, color=COLOR_TEXTO, va='center')
ax.annotate("https://www.ift.org.mx/usuarios-y-audiencias/tercer-encuesta-2023-usuarios-de-servicios-de-telecomunicaciones.", 
            xy=(0.5, Y_URL), xycoords='data', xytext=(175, 0), textcoords='offset points', 
            fontweight='normal', fontsize=9, color=COLOR_ENLACE, va='center')
# Subrayado simulado del link
ax.plot([3.15, 12.1], [Y_URL - 0.05, Y_URL - 0.05], color=COLOR_ENLACE, linewidth=0.7)

# Nota
ax.annotate("Nota:", xy=(0.5, Y_NOTA), xycoords='data', fontweight='bold', fontsize=9, color=COLOR_TEXTO, va='center')
ax.annotate("Información correspondiente al estudio cualitativo y no es representativo a nivel nacional.", 
            xy=(0.5, Y_NOTA), xycoords='data', xytext=(35, 0), textcoords='offset points', 
            fontweight='normal', fontsize=9, color=COLOR_TEXTO, va='center')

# ══════════════════════════════════════════
# Exportación
# ══════════════════════════════════════════
plt.tight_layout(pad=0)
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "figura_f14.png")

fig.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"Guardado correctamente en: {output_path}")