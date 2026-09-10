import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
import sys
import os
import numpy as np

# ─── Configuración del Logger ─────────────────────────────────────────────────────
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()

# ─── Rutas ────────────────────────────────────────────────────────────────────────
INPUT  = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\F.2\TD_EMPLEO_SEXO_VA.csv"
OUTPUT = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_F2.png"
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# ─── Lectura y Filtros ────────────────────────────────────────────────────────────
df_empleo = pd.read_csv(INPUT, encoding='utf-8-sig')

# Filtrar para Año 2024, Trimestre 2
df_2024_q2 = df_empleo[(df_empleo['ANIO'] == 2024) & (df_empleo['TRIM'] == 2)]
res = df_2024_q2.groupby('SEXO')[['EMP_RADIO', 'EMP_TELECOM']].sum()

CATEGORIAS = ['Mujeres', 'Hombres']

# Extraer totales por sector
radio = {c: res.loc[c, 'EMP_RADIO'] for c in CATEGORIAS}
telecom = {c: res.loc[c, 'EMP_TELECOM'] for c in CATEGORIAS}

# ─── Estilos y Colores Institucionales ────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
C_TEXT = '#3c3c3b'
color_borde_caja = '#D1D1DF'
color_lineas = '#A0A0B0'

# Utilizando los tonos verdes exactos extraídos de la Figura B.16
COLORS = {
    "Mujeres": "#64a0a1",  # Verde azulado medio
    "Hombres": "#132b2d"   # Verde muy oscuro
}

# Estilo para los chips flotantes de porcentaje
chip_style = dict(boxstyle="round,pad=0.4", fc="white", ec="#D1D1DF", lw=1.2)

# ─── Layout General y Eje de Fondo ────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 10), facecolor='white')

# Eje de fondo para dibujar las cajas de la UI
bg_ax = fig.add_axes([0, 0, 1, 1], zorder=0)
bg_ax.axis('off')
bg_ax.set_xlim(0, 1)
bg_ax.set_ylim(0, 1)

# ─── Funciones de Dibujo UI ───────────────────────────────────────────────────────
def draw_pie_with_labels(ax, totals):
    sizes = [totals[c] for c in CATEGORIAS]
    colors = [COLORS[c] for c in CATEGORIAS]
    
    # Gráfica de pastel sólida (eliminado el width=0.45 de dona)
    wedges, _ = ax.pie(sizes, colors=colors, startangle=90, counterclock=True,
                       wedgeprops=dict(edgecolor="white", linewidth=1.5))
    ax.set_aspect("equal")
    ax.patch.set_alpha(0)
    
    total = sum(sizes)
    for i, p in enumerate(wedges):
        pct = sizes[i] / total * 100
        if pct < 0.05: continue
        
        # Calcular el borde exterior para anclar la flecha
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y_edge = np.sin(np.deg2rad(ang))
        x_edge = np.cos(np.deg2rad(ang))
        
        c_name = CATEGORIAS[i]
        
        # Posicionamiento dinámico hacia afuera para que los chips no se encimen
        x_text = x_edge * 1.35
        y_text = y_edge * 1.35
            
        ha = "left" if x_text > 0 else "right"
        
        # Dibujar el chip de porcentaje con la línea apuntando al borde del pastel
        chip_text = f"{pct:.1f}%"
        ax.annotate(chip_text, xy=(x_edge, y_edge), xytext=(x_text, y_text),
                    ha=ha, va="center",
                    arrowprops=dict(arrowstyle="-", color=color_lineas, lw=1.2),
                    bbox=chip_style, color=COLORS[c_name], fontweight='bold', fontsize=12,
                    annotation_clip=False)
        
        # Posicionar la etiqueta de la categoría ("Mujeres" / "Hombres")
        y_label_offset = 0.18 if y_text > 0 else -0.18
        va_label = "bottom" if y_text > 0 else "top"
        
        ax.text(x_text, y_text + y_label_offset, c_name, ha=ha, va=va_label,
                fontsize=11, fontweight='bold', color='#6C6C85', clip_on=False)

def draw_section(offset_x, title, totals):
    # 1. Caja principal del panel (Bordes grises claros)
    box_main = patches.FancyBboxPatch((0.02 + offset_x, 0.08), 0.45, 0.78, 
                                      boxstyle="round,pad=0.02", ec=color_borde_caja, fc="white", lw=1.5)
    bg_ax.add_patch(box_main)
    
    center_x = 0.02 + 0.45 / 2 + offset_x
    
    # 2. Chip con el título del panel ("Radiodifusión" / "Telecomunicaciones")
    w_title = 0.22
    t_box = patches.FancyBboxPatch((center_x - w_title/2, 0.85), w_title, 0.05, 
                                   boxstyle="round,pad=0.02", ec="#EEEEEE", fc="white", lw=1)
    bg_ax.add_patch(t_box)
    bg_ax.text(center_x, 0.875, title, 
               fontsize=16, fontweight='bold', color=C_TEXT, ha='center', va='center')

    # 3. Burbuja de Totales (Centrada en la parte inferior del panel)
    bubble = patches.FancyBboxPatch((center_x - 0.12, 0.12), 0.24, 0.09, 
                                    boxstyle="round,pad=0.01", ec="#EEEEEE", fc="white", lw=1)
    bg_ax.add_patch(bubble)
    bg_ax.text(center_x, 0.180, "Personas empleadas a\nnivel nacional:", 
               fontsize=10, color='#6C6C85', ha='center', va='center')
    bg_ax.text(center_x, 0.142, f"{int(sum(totals.values())):,}", 
               fontsize=18, fontweight='bold', color=C_TEXT, ha='center', va='center')

    # 4. Gráfica de Pastel Principal (Centrada en la caja, sin ser dona)
    ax_pie = fig.add_axes([center_x - 0.16, 0.25, 0.32, 0.55], zorder=5)
    draw_pie_with_labels(ax_pie, totals)

# Renderizar ambos paneles
draw_section(0.00, "Radiodifusión", radio)
draw_section(0.49, "Telecomunicaciones", telecom)

# ─── Encabezado y Pie Institucional ───────────────────────────────────────────────
# Cuadrito decorativo y texto del título
bg_ax.text(0.028, 0.952, '   ', fontsize=2, va='center',
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))
bg_ax.text(0.046, 0.952, 'Figura F.2.', fontsize=13, fontweight='bold', color=C_TEXT, va='center')
bg_ax.text(0.105, 0.952, 'Distribución de personas empleadas por sexo (Segundo trimestre de 2024)', 
           fontsize=13, color=C_TEXT, va='center')

# Notas al pie
bg_ax.text(0.040, 0.045, "Fuente:", fontweight='bold', fontsize=8, color=C_TEXT)
bg_ax.text(0.075, 0.045, "IFT con datos proporcionados por los operadores de telecomunicaciones y radiodifusión.", fontsize=8, color=C_TEXT)

# ─── Guardado ─────────────────────────────────────────────────────────────────────
plt.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor="white", edgecolor='none')
plt.close()
print(f"Figura guardada exitosamente en: {OUTPUT}")