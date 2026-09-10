import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# Habilitar el registro de datos si el archivo utilitario está presente
sys.path.append(str(Path(__file__).resolve().parent))
try:
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

import warnings
warnings.filterwarnings("ignore")

# ─── CONFIGURACIÓN DE COLORES Y ESTILOS (GUÍA CRT) ──────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

BG_FIG     = "#FFFFFF"
BG_AXES    = "#F8F8FA"
CARD_BG    = "#E8EEF2" 
TEXT_MAIN  = "#3c3c3b"
TEXT_LIGHT = "#7c7c7c"
SQUARE_COL = "#4a7d75"

COLOR_MUJERES = "#b35aba"
COLOR_HOMBRES = "#006157"

# ─── 1. DATOS CALCULADOS (ORDENADOS PARA LA CUADRÍCULA) ─────────────────────
actividades_grid = [
    # Fila 1 (Superiores)
    ("Comunicarse", 94.5, 92.1),
    ("Redes sociales", 92.5, 90.4),
    ("Entretenimiento", 86.4, 90.0),
    ("Buscar información", 87.6, 87.8),
    # Fila 2 (Inferiores)
    ("Capacitación o educación", 72.2, 72.0),
    ("Comprar productos\no servicios", 32.2, 34.6),
    ("Operaciones bancarias\nen línea", 15.1, 18.2),
    ("Ventas por internet", 12.1, 11.4)
]

# ─── FUNCIONES AUXILIARES DE INTERFAZ ───────────────────────────────────────
def add_rounded_box(ax, x, y, w, h, bg_color=CARD_BG, r=0.015, shadow=True, zorder=2):
    if shadow:
        shadow_patch = FancyBboxPatch(
            (x + 0.002, y - 0.003), w, h,
            boxstyle=f"round,pad=0,rounding_size={r}",
            facecolor="#000000", alpha=0.08, edgecolor="none", zorder=zorder-1, clip_on=False
        )
        ax.add_patch(shadow_patch)
    
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        facecolor=bg_color, edgecolor="none", zorder=zorder, clip_on=False
    )
    ax.add_patch(box)

def draw_activity_card(ax, x, y, w, h, title, pct_f, pct_m):
    add_rounded_box(ax, x, y, w, h, bg_color=CARD_BG, r=0.015)
    
    # Título superior (Réplica exacta de figura_f1.1.py)
    ax.text(x + w/2, y + h - 0.035, title, ha='center', va='top', 
            fontsize=8.5, color=TEXT_MAIN, fontweight='bold', linespacing=1.2)

    # Coordenadas X desplazadas al 65% del ancho de la tarjeta
    x_text = x + w * 0.65 

    # Coordenadas Y ajustadas simétricamente tal como en la UI original
    y_f_label = y + h * 0.58
    y_f_pct   = y + h * 0.44
    y_m_label = y + h * 0.28
    y_m_pct   = y + h * 0.14

    # Bloque Mujeres (Arriba) - Redondeado a entero sin decimales
    ax.text(x_text, y_f_label, "Mujeres", ha='center', va='center', fontsize=8, color=TEXT_MAIN, fontweight='medium')
    ax.text(x_text, y_f_pct, f"{round(pct_f)}%", ha='center', va='center', fontsize=16, color=COLOR_MUJERES, fontweight='bold')

    # Bloque Hombres (Abajo) - Redondeado a entero sin decimales
    ax.text(x_text, y_m_label, "Hombres", ha='center', va='center', fontsize=8, color=TEXT_MAIN, fontweight='medium')
    ax.text(x_text, y_m_pct, f"{round(pct_m)}%", ha='center', va='center', fontsize=16, color=COLOR_HOMBRES, fontweight='bold')


# ─── CONFIGURACIÓN DEL LIENZO ───────────────────────────────────────────────
fig = plt.figure(figsize=(16, 8.5), facecolor=BG_FIG)
ax = fig.add_axes((0.08, 0.22, 0.84, 0.63), facecolor=BG_AXES)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# ─── ENCABEZADO INSTITUCIONAL ───────────────────────────────────────────────
ax.text(0.0, 1.15, '   ', bbox=dict(boxstyle='round,pad=0.4,rounding_size=0.1', facecolor=SQUARE_COL, edgecolor='none'))
ax.text(0.025, 1.15, "Figura F.4.", fontweight='bold', fontsize=14, color=TEXT_MAIN, va='center')
ax.text(0.12, 1.15, "Usuarios de internet por principales usos y sexo, 2023", fontweight='medium', fontsize=14, color=TEXT_MAIN, va='center')

# ─── CONSTRUCCIÓN DE LA CUADRÍCULA (GRID UI CANÓNICA 2x4) ───────────────────
# Se ajustaron las coordenadas 'Y' para centrar verticalmente la cuadrícula.
# Esto mantiene la UI visual con el mismo tamaño de tarjetas (h=0.35) de f1.1.py.
ROW1_Y = 0.55
ROW1_H = 0.35
ROW2_Y = 0.10
ROW2_H = 0.35
GAP = 0.02

# Dimensionamiento dinámico exacto de las columnas
w_total_grid = 1.0 - (GAP * 3)
w_card = w_total_grid / 4

for i in range(4):
    # Fila 1 (Tarjetas Superiores)
    titulo1, pf1, pm1 = actividades_grid[i]
    cx1 = i * (w_card + GAP)
    draw_activity_card(ax, cx1, ROW1_Y, w_card, ROW1_H, titulo1, pf1, pm1)

    # Fila 2 (Tarjetas Inferiores)
    titulo2, pf2, pm2 = actividades_grid[i + 4]
    cx2 = i * (w_card + GAP)
    # CORRECCIÓN: Se reemplazó el error ROW2_H por ROW2_Y en la posición y de dibujado
    draw_activity_card(ax, cx2, ROW2_Y, w_card, ROW2_H, titulo2, pf2, pm2)


# ─── PIE DE PÁGINA (FUENTES Y NOTAS) ────────────────────────────────────────
fig.text(0.08, 0.12, "Fuente:", fontweight='bold', fontsize=8, color=TEXT_MAIN)
fig.text(0.115, 0.12, "IFT con datos de la ENDUTIH 2023, del INEGI. Datos disponibles en https://www.inegi.org.mx/programas/endutih/2023/", fontweight='normal', fontsize=8, color=TEXT_MAIN)

fig.text(0.08, 0.09, "Notas:", fontweight='bold', fontsize=8, color=TEXT_MAIN)
fig.text(0.115, 0.09, "Todos los usuarios se refieren a personas de 6 años o más.", fontweight='normal', fontsize=8, color=TEXT_MAIN)


# ─── EXPORTACIÓN Y RENDERIZADO ──────────────────────────────────────────────
output_dir = r"C:\Users\ivan-\Documents\GitHub\anuario\output"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "figura_f1.4.png")

plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=BG_FIG, edgecolor='none')
print(f"✅ Infografía de usos de internet corregida con la UI exacta en: {output_path}")

plt.show()