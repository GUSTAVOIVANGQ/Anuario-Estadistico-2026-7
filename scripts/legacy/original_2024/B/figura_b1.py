"""
Figura B.1 — Distribución de los Servicios Fijos con respecto del total de hogares a nivel nacional
Fuente: IFT con datos de la ENDUTIH 2023, del INEGI.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'Figura_B1.png')

TOTAL_HOG   = 38_627_319
pct_tres    = 21
pct_dos     = 34
pct_uno     = 25
pct_ninguno = 20

un_srv  = {'Solo\nTV Rest.': 6, 'Solo\nTelefonía': 1, 'Solo\nInternet': 18}
dos_srv = {'Internet +\nTelefonía': 20, 'TV Rest. +\nInternet': 13, 'TV Rest. +\nTelefonía': 1}

C_TRES    = '#132b2d'
C_DOS     = '#3b6667'
C_UNO     = '#64a0a1'
C_NINGUNO = '#86adae'
C_TEXT    = '#3c3c3b'

plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
fig = plt.figure(figsize=(16, 9), facecolor='white')


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: nube de dialogo con cola triangular
# ══════════════════════════════════════════════════════════════════════════════
def draw_bubble(ax, bx, by, bw, bh, side='left',
                fc='white', ec='#b0b0b0', lw=1.0, zorder=5, corner=0.07,
                tail_frac=0.22):
    mid_x = bx + bw / 2
    mid_y = by + bh / 2
    tw = min(bw, bh) * tail_frac
    td = min(bw, bh) * 0.28

    if side == 'left':
        p1  = (bx, mid_y + tw / 2)
        p2  = (bx, mid_y - tw / 2)
        tip = (bx - td, mid_y)
    elif side == 'right':
        p1  = (bx + bw, mid_y - tw / 2)
        p2  = (bx + bw, mid_y + tw / 2)
        tip = (bx + bw + td, mid_y)
    elif side == 'bottom':
        p1  = (mid_x - tw / 2, by)
        p2  = (mid_x + tw / 2, by)
        tip = (mid_x, by - td)
    else:  # top
        p1  = (mid_x + tw / 2, by + bh)
        p2  = (mid_x - tw / 2, by + bh)
        tip = (mid_x, by + bh + td)

    rect = FancyBboxPatch((bx, by), bw, bh,
                          boxstyle=f'round,pad=0.0,rounding_size={corner}',
                          linewidth=lw, edgecolor=ec, facecolor=fc, zorder=zorder)
    ax.add_patch(rect)
    tri = plt.Polygon([p1, tip, p2], closed=True,
                      facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder)
    ax.add_patch(tri)
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=fc, lw=lw + 1.2, zorder=zorder + 1)
    return tip


# ══════════════════════════════════════════════════════════════════════════════
# ENCABEZADO — un solo renglón
# ══════════════════════════════════════════════════════════════════════════════
fig.text(0.028, 0.952, '   ', fontsize=2, va='center',
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2',
                   facecolor='#4a7d75', edgecolor='none'))
fig.text(0.046, 0.952, 'Figura B.1.', fontsize=13, fontweight='bold',
         color=C_TEXT, va='center')
fig.text(0.130, 0.952,
         'Distribución de los Servicios Fijos con respecto del total de hogares a nivel nacional',
         fontsize=13, color=C_TEXT, va='center')

# ══════════════════════════════════════════════════════════════════════════════
# PASTEL — eje mas amplio para que las nubes no se corten
# ══════════════════════════════════════════════════════════════════════════════
ax_pie = fig.add_axes([0.00, 0.11, 0.53, 0.78])
ax_pie.set_aspect('equal')
ax_pie.set_xlim(-1.65, 1.65)
ax_pie.set_ylim(-1.38, 1.38)
ax_pie.axis('off')

# ── Imagen de fondo (Mapa de México) ──────────────────────────────────────────
bg_path = r"C:\Users\ivan-\Documents\GitHub\anuario\Mapa_de_México_verde_background_202605131702.jpeg"
if os.path.exists(bg_path):
    img = plt.imread(bg_path)
    # Se coloca al fondo (zorder=0) y con cierta transparencia para no saturar
    ax_pie.imshow(img, extent=[-1.65, 1.65, -1.38, 1.38], aspect='auto', 
                  zorder=0, alpha=0.6)


r_pie = 0.68
sizes      = [pct_tres, pct_dos, pct_uno, pct_ninguno]
colors_pie = [C_TRES, C_DOS, C_UNO, C_NINGUNO]

wedges, _ = ax_pie.pie(
    sizes, colors=colors_pie, explode=(0.03,)*4,
    startangle=90, counterclock=False, radius=r_pie,
    wedgeprops=dict(linewidth=2.0, edgecolor='white')
)

# ── Nubes del pastel ──────────────────────────────────────────────────────────
# Calculadas para que la PUNTA de la cola quede sobre el borde del wedge.
# tip_x (side='left')  = bx - bh*0.28   → queremos ≈ r_pie*cos(theta_mid)
# tip_x (side='right') = bx+bw + bh*0.28

bubble_cfg = [
    # wi,  bx,    by,    bw,    bh,    side,    pct_txt,         lbl
    (0,   0.60,  0.54,  0.62,  0.52,  'left',  f'{pct_tres}%',
     'Tres servicios\n(Telefonia Fija +\nTV Restringida + Internet)'),
    (1,   0.60, -0.68,  0.50,  0.38,  'left',  f'{pct_dos}%',   'Dos servicios'),
    (2,  -1.23, -0.56,  0.50,  0.38,  'right', f'{pct_uno}%',   'Un servicio'),
    (3,  -1.23,  0.24,  0.50,  0.32,  'right', f'{pct_ninguno}%','Ninguno'),
]

for wi, bx, by, bw, bh, side, pct_txt, lbl in bubble_cfg:
    draw_bubble(ax_pie, bx, by, bw, bh, side=side,
                fc='white', ec='#b0b0b0', lw=0.9, corner=0.06, zorder=5)
    ax_pie.text(bx + bw/2, by + bh * 0.68, pct_txt,
                ha='center', va='center', fontsize=21, fontweight='bold',
                color=C_TEXT, zorder=7)
    ax_pie.text(bx + bw/2, by + bh * 0.26, lbl,
                ha='center', va='center', fontsize=7.0, color=C_TEXT,
                linespacing=1.3, zorder=7)

# ── Callout "Total de hogares" — solo rectángulo redondeado, sin cola ─────────
tbx, tby, tbw, tbh = -1.22, -1.22, 0.82, 0.38
rect_tot = FancyBboxPatch((tbx, tby), tbw, tbh,
                          boxstyle='round,pad=0.0,rounding_size=0.06',
                          linewidth=0.9, edgecolor='#b0b0b0', facecolor='white',
                          zorder=5)
ax_pie.add_patch(rect_tot)
ax_pie.text(tbx + tbw/2, tby + tbh * 0.72, 'Total de hogares en México:',
            ha='center', va='center', fontsize=7.5, color=C_TEXT, zorder=7)
ax_pie.text(tbx + tbw/2, tby + tbh * 0.28, f'{TOTAL_HOG:,}',
            ha='center', va='center', fontsize=12.5, fontweight='bold',
            color=C_TEXT, zorder=7)


# ══════════════════════════════════════════════════════════════════════════════
# PANELES LATERALES DE BARRAS
# ══════════════════════════════════════════════════════════════════════════════
def draw_panel_bubble(fig, left, bottom, width, height,
                      cats, vals, bar_colors, title, title_color):
    """
    Panel de barras con caja redondeada y cola izquierda.
    Correcciones:
      - Titulo via fig.text para alineacion izquierda limpia (no encima de barras).
      - ylim generoso para que chips queden dentro.
      - xlim simetrico para centrar barras.
      - pad_b amplio para xticklabels de dos lineas.
    """
    # Fondo redondeado
    ax_bg = fig.add_axes([left, bottom, width, height], zorder=2)
    ax_bg.set_xlim(0, 1)
    ax_bg.set_ylim(0, 1)
    ax_bg.axis('off')
    ax_bg.patch.set_visible(False)

    rect = FancyBboxPatch((0, 0), 1, 1,
                          boxstyle='round,pad=0.0,rounding_size=0.012',
                          linewidth=1.0, edgecolor='#c0c0c0', facecolor='#F8F8FA',
                          transform=ax_bg.transAxes, zorder=1, clip_on=False)
    ax_bg.add_patch(rect)

    # Cola izquierda
    mid_y  = 0.50
    tw_ax  = 0.09
    td_adj = 0.046 * (height / width)
    p1  = (0.0, mid_y + tw_ax / 2)
    p2  = (0.0, mid_y - tw_ax / 2)
    tip = (-td_adj, mid_y)
    tri = plt.Polygon([p1, tip, p2], closed=True,
                      facecolor='#F8F8FA', edgecolor='#c0c0c0', linewidth=1.0,
                      transform=ax_bg.transAxes, zorder=1, clip_on=False)
    ax_bg.add_patch(tri)
    ax_bg.plot([0, 0], [p1[1], p2[1]], color='#F8F8FA',
               lw=2.5, transform=ax_bg.transAxes, zorder=2, clip_on=False)

    # Titulo alineado izquierda, encima del area de barras
    fig.text(left + width * 0.07,
             bottom + height * 0.91,
             title,
             fontsize=10, color=title_color, fontweight='bold',
             ha='left', va='center', zorder=10)

    # Margenes del axes de barras
    pad_l = 0.10   # izquierda (cola)
    pad_r = 0.04   # derecha
    pad_b = 0.24   # abajo (xticklabels 2 lineas)
    pad_t = 0.24   # arriba (titulo + chips)

    ax = fig.add_axes([
        left   + width  * pad_l,
        bottom + height * pad_b,
        width  * (1 - pad_l - pad_r),
        height * (1 - pad_b - pad_t),
    ], zorder=3)
    ax.set_facecolor('none')

    n = len(cats)
    xs = np.arange(n)
    bar_width = 0.45

    bars = ax.bar(xs, vals, color=bar_colors,
                  width=bar_width, edgecolor='white', linewidth=1.2, zorder=3)

    y_max = max(vals)
    ax.set_ylim(0, y_max * 1.80)   # espacio generoso para chips

    for bar, v in zip(bars, vals):
        cx_ = bar.get_x() + bar.get_width() / 2
        cy_ = bar.get_height()
        ax.text(cx_, cy_ + y_max * 0.05, f'{v}%',
                ha='center', va='bottom',
                fontsize=11, fontweight='bold', color=C_TEXT, zorder=6,
                bbox=dict(boxstyle='round,pad=0.25,rounding_size=0.4',
                          facecolor='white', edgecolor=title_color, linewidth=0.9))

    ax.tick_params(left=False, bottom=False, labelleft=False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xticks(xs)
    ax.set_xticklabels(cats, fontsize=8.0, color=C_TEXT, linespacing=1.2)
    ax.tick_params(axis='x', pad=4, length=0)
    ax.set_xlim(-0.65, n - 1 + 0.65)   # centrado simetrico


# ── Panel "Un servicio" ───────────────────────────────────────────────────────
draw_panel_bubble(
    fig,
    left=0.527, bottom=0.510, width=0.448, height=0.388,
    cats=list(un_srv.keys()), vals=list(un_srv.values()),
    bar_colors=['#5c9596', '#64a0a1', '#86adae'],
    title='Un servicio', title_color=C_UNO,
)

# ── Panel "Dos servicios" ─────────────────────────────────────────────────────
draw_panel_bubble(
    fig,
    left=0.527, bottom=0.103, width=0.448, height=0.388,
    cats=list(dos_srv.keys()), vals=list(dos_srv.values()),
    bar_colors=['#234244', '#3b6667', '#4c7d7e'],
    title='Dos servicios', title_color=C_DOS,
)

# ══════════════════════════════════════════════════════════════════════════════
# NOTAS Y FUENTE
# ══════════════════════════════════════════════════════════════════════════════
fig.text(0.040, 0.055, "Fuente:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.083, 0.055,
         "IFT con datos de la ENDUTIH 2023, del INEGI. "
         "Datos disponibles en https://www.inegi.org.mx/programas/endutih/2023/.",
         fontsize=8, color=C_TEXT)
fig.text(0.040, 0.033, "Nota:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.073, 0.033,
         "Los porcentajes pueden no sumar 100% debido al redondeo.",
         fontsize=8, color=C_TEXT)

# ══════════════════════════════════════════════════════════════════════════════
# GUARDADO
# ══════════════════════════════════════════════════════════════════════════════
plt.savefig(OUTPUT_PATH, dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"Figura guardada en: {OUTPUT_PATH}")
plt.close()
print("Listo.")