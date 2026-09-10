import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path

# ─── Rutas ────────────────────────────────────────────────────────────────────────
OUTPUT = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_C3.png"
Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)

# ─── Datos ────────────────────────────────────────────────────────────────────────
datos = {
    "Hacen uso de servicios móviles": 78,
    "No hacen uso de servicios móviles": 22
}
TECNO_PRINCIPALES = list(datos.keys())

# ─── Estilos y Colores ──────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
C_TEXT = '#3c3c3b'
color_borde_caja = '#D1D1DF'

COLORS = {
    "Hacen uso de servicios móviles": "#3b6667",
    "No hacen uso de servicios móviles": "#132b2d"
}

# ─── Layout General ───────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(6, 9), facecolor='white')

bg_ax = fig.add_axes([0, 0, 1, 1], zorder=0)
bg_ax.axis('off')
bg_ax.set_xlim(0, 1)
bg_ax.set_ylim(0, 1)

# ─── Encabezado institucional (estilo Guia_colores.md) ────────────────────────────
# Cuadrado decorativo institucional (#4a7d75)
bg_ax.annotate(' ', xy=(0.04, 0.945), xycoords='data', xytext=(0, 0), textcoords='offset points',
               bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'),
               fontsize=2, va='center')

# Número de figura en negrita
bg_ax.annotate('Figura C.3.', xy=(0.04, 0.945), xycoords='data', xytext=(15, 0), textcoords='offset points',
               fontsize=14, fontweight='bold', color=C_TEXT, va='center')

# Título de la figura en peso medium
bg_ax.annotate('Porcentaje del uso de los servicios\nmóviles de telecomunicaciones', 
               xy=(0.04, 0.945), xycoords='data', xytext=(105, 0), textcoords='offset points',
               fontsize=14, fontweight='medium', color=C_TEXT, va='center')


# ─── Subtítulo "Población de 6 años o más:" ───────────────────────────────────────
bg_ax.text(0.50, 0.822, 'Población de 6 años o más:',
           fontsize=10, fontweight='bold', color=C_TEXT,
           ha='center', va='center',
           bbox=dict(boxstyle='round,pad=0.5', fc='white', ec=color_borde_caja, lw=1.0),
           zorder=3)

# ─── Posiciones de etiquetas: a la derecha, apiladas verticalmente ────────────────
PIE_LBL_POS = {
    "No hacen uso de servicios móviles":  (1.05, 0.55),   # arriba derecha
    "Hacen uso de servicios móviles":      (1.05, -0.55),  # abajo derecha
}

# ─── Función principal de dibujo del pie ─────────────────────────────────────────
def draw_pie_with_labels(ax, totals):
    sizes = [totals[t] for t in TECNO_PRINCIPALES]
    colors = [COLORS[t] for t in TECNO_PRINCIPALES]

    wedges, _ = ax.pie(
        sizes, colors=colors,
        startangle=90, counterclock=True,
        wedgeprops=dict(edgecolor="white", linewidth=2.0)
    )
    ax.set_aspect("equal")
    ax.patch.set_alpha(0)

    total = sum(sizes)
    for i, p in enumerate(wedges):
        pct = sizes[i] / total * 100
        if pct < 0.05:
            continue

        t_name = TECNO_PRINCIPALES[i]
        
        # Obtenemos la posición predeterminada para el texto
        x_text, y_text = PIE_LBL_POS.get(t_name, (1.05, 0))

        # Chip del porcentaje (sin arrowprops para eliminar la línea)
        chip_text = f"{pct:.0f}%"
        ax.annotate(
            chip_text,
            xy=(x_text, y_text - 0.12),
            ha='left', va='center',
            bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="#D1D1DF", lw=1.2),
            color=C_TEXT, fontweight='bold', fontsize=14,
            annotation_clip=False,
            zorder=10
        )

        # Nombre de la categoría encima del chip
        display_name = t_name.replace(" de servicios", "\nde servicios")
        ax.text(x_text, y_text + 0.08, display_name,
                ha='left', va='bottom',
                fontsize=9, fontweight='bold', color='#6C6C85',
                clip_on=False, zorder=10)

# ─── Eje del pie: desplazado a la izquierda ───────────────────────────────────────
ax_pie = fig.add_axes([-0.05, 0.22, 0.75, 0.62], zorder=5)
draw_pie_with_labels(ax_pie, datos)

# ─── Pie de página (fuente) ───────────────────────────────────────────────────────
# Coordenadas Y elevadas a 0.23 y 0.215 para acercar el bloque a la gráfica
bg_ax.text(0.06, 0.23, "Fuente:", fontweight='bold', fontsize=7.5, color=C_TEXT)
bg_ax.text(0.135, 0.23, "IFT con datos de la ENDUTIH 2023, del INEGI.", fontsize=7.5, color=C_TEXT)
bg_ax.text(0.06, 0.215, "Datos disponibles en https://www.inegi.org.mx/programas/endutih/2023/#tabulados.",
           fontsize=7.5, color=C_TEXT)

# ─── Guardado ─────────────────────────────────────────────────────────────────────
plt.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor="white", edgecolor='none')
plt.close()
print(f"Figura guardada en: {OUTPUT}")