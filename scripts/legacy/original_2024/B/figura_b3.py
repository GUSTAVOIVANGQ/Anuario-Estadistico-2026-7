"""
Figura B.3 — Distribución de los Servicios Fijos con respecto del total
de hogares en las zonas urbanas.
Fuente: IFT con datos de la ENDUTIH 2023, del INEGI.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from dbfread import DBF

# ── 1. RUTA ──────────────────────────────────────────────────────────────────
DBF_PATH = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\b.3\tic_2023_hogares.DBF"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'Figura_B3.png')

# ── 2. CARGA ─────────────────────────────────────────────────────────────────
print("Cargando DBF (Urbano)...")
records = list(DBF(DBF_PATH, encoding="latin-1"))
df = pd.DataFrame(records)

for col in ["P4_4", "P4_5", "P5_1", "P5_5", "DOMINIO"]:
    df[col] = df[col].astype(str).str.strip()
df["FAC_HOG"] = pd.to_numeric(df["FAC_HOG"], errors="coerce").fillna(0)

df["internet_fijo"] = ((df["P4_4"] == "1") & (df["P4_5"].isin(["1", "3"]))).astype(int)
df["tv_paga"]       = (df["P5_1"] == "1").astype(int)
df["tel_fija"]      = (df["P5_5"] == "1").astype(int)
df["num_servicios"] = df["internet_fijo"] + df["tv_paga"] + df["tel_fija"]

# ── 3. FILTRO URBANO ─────────────────────────────────────────────────────────
urb = df[df["DOMINIO"] == "U"].copy()
TOTAL_HOG = urb["FAC_HOG"].sum()

# ── 4. CÁLCULO ───────────────────────────────────────────────────────────────
def pct(mask):
    return urb.loc[mask, "FAC_HOG"].sum() / TOTAL_HOG * 100

v = {
    "tres":    pct(urb["num_servicios"] == 3),
    "dos":     pct(urb["num_servicios"] == 2),
    "uno":     pct(urb["num_servicios"] == 1),
    "ninguno": pct(urb["num_servicios"] == 0),
}

un_srv = {
    'Solo\nTV Rest.': pct((urb["tv_paga"]==1) & (urb["internet_fijo"]==0) & (urb["tel_fija"]==0)),
    'Solo\nTelefonía': pct((urb["tel_fija"]==1) & (urb["internet_fijo"]==0) & (urb["tv_paga"]==0)),
    'Solo\nInternet': pct((urb["internet_fijo"]==1) & (urb["tv_paga"]==0) & (urb["tel_fija"]==0))
}

dos_srv = {
    'Internet +\nTelefonía': pct((urb["internet_fijo"]==1) & (urb["tel_fija"]==1) & (urb["tv_paga"]==0)),
    'TV Rest. +\nInternet': pct((urb["tv_paga"]==1) & (urb["internet_fijo"]==1) & (urb["tel_fija"]==0)),
    'TV Rest. +\nTelefonía': pct((urb["tv_paga"]==1) & (urb["tel_fija"]==1) & (urb["internet_fijo"]==0))
}

# ── 5. ESTILOS ───────────────────────────────────────────────────────────────
C_TRES    = '#132b2d'
C_DOS     = '#3b6667'
C_UNO     = '#64a0a1'
C_NINGUNO = '#86adae'
C_TEXT    = '#3c3c3b'

plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
fig = plt.figure(figsize=(16, 9), facecolor='white')

# ══════════════════════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════════════════════
def draw_bubble(ax, bx, by, bw, bh, side='left', fc='white', ec='#b0b0b0', lw=1.0, zorder=5, corner=0.07, tail_frac=0.22):
    mid_x, mid_y = bx + bw / 2, by + bh / 2
    tw, td = min(bw, bh) * tail_frac, min(bw, bh) * 0.28

    if side == 'left':
        p1, p2, tip = (bx, mid_y + tw / 2), (bx, mid_y - tw / 2), (bx - td, mid_y)
    elif side == 'right':
        p1, p2, tip = (bx + bw, mid_y - tw / 2), (bx + bw, mid_y + tw / 2), (bx + bw + td, mid_y)
    elif side == 'bottom':
        p1, p2, tip = (mid_x - tw / 2, by), (mid_x + tw / 2, by), (mid_x, by - td)
    else:  # top
        p1, p2, tip = (mid_x + tw / 2, by + bh), (mid_x - tw / 2, by + bh), (mid_x, by + bh + td)

    rect = FancyBboxPatch((bx, by), bw, bh, boxstyle=f'round,pad=0.0,rounding_size={corner}',
                          linewidth=lw, edgecolor=ec, facecolor=fc, zorder=zorder)
    ax.add_patch(rect)
    ax.add_patch(plt.Polygon([p1, tip, p2], closed=True, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder))
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=fc, lw=lw + 1.2, zorder=zorder + 1)
    return tip

# ══════════════════════════════════════════════════════════════════════════════
# ENCABEZADO
# ══════════════════════════════════════════════════════════════════════════════
fig.text(0.028, 0.952, '   ', fontsize=2, va='center',
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))
fig.text(0.046, 0.952, 'Figura B.3.', fontsize=13, fontweight='bold', color=C_TEXT, va='center')
fig.text(0.130, 0.952, 'Distribución de los Servicios Fijos con respecto del total de hogares en las zonas urbanas',
         fontsize=13, color=C_TEXT, va='center')

# ══════════════════════════════════════════════════════════════════════════════
# PASTEL
# ══════════════════════════════════════════════════════════════════════════════
ax_pie = fig.add_axes([0.00, 0.11, 0.53, 0.78])
ax_pie.set_aspect('equal'); ax_pie.set_xlim(-1.65, 1.65); ax_pie.set_ylim(-1.38, 1.38); ax_pie.axis('off')

# Mapa de Fondo
bg_path = r"C:\Users\ivan-\Documents\GitHub\anuario\Mapa_de_México_verde_background_202605131702.jpeg"
if os.path.exists(bg_path):
    img = plt.imread(bg_path)
    ax_pie.imshow(img, extent=[-1.65, 1.65, -1.38, 1.38], aspect='auto', zorder=0, alpha=0.6)

r_pie = 0.68
sizes      = [v["tres"], v["dos"], v["uno"], v["ninguno"]]
colors_pie = [C_TRES, C_DOS, C_UNO, C_NINGUNO]

wedges, _ = ax_pie.pie(
    sizes, colors=colors_pie, explode=(0.03,)*4,
    startangle=90, counterclock=False, radius=r_pie,
    wedgeprops=dict(linewidth=2.0, edgecolor='white')
)

bubble_cfg = [
    (0.60,  0.54,  0.62,  0.52, 'left',  f'{v["tres"]:.0f}%', 'Tres servicios\n(Telefonia Fija +\nTV Restringida + Internet)'),
    (0.60, -0.68,  0.50,  0.38, 'left',  f'{v["dos"]:.0f}%',  'Dos servicios'),
    (-1.23, -0.56, 0.50,  0.38, 'right', f'{v["uno"]:.0f}%',  'Un servicio'),
    (-1.23,  0.24, 0.50,  0.32, 'right', f'{v["ninguno"]:.0f}%','Ninguno'),
]

for bx, by, bw, bh, side, pct_txt, lbl in bubble_cfg:
    draw_bubble(ax_pie, bx, by, bw, bh, side=side, fc='white', ec='#b0b0b0', lw=0.9, corner=0.06, zorder=5)
    ax_pie.text(bx + bw/2, by + bh * 0.68, pct_txt, ha='center', va='center', fontsize=21, fontweight='bold', color=C_TEXT, zorder=7)
    ax_pie.text(bx + bw/2, by + bh * 0.26, lbl, ha='center', va='center', fontsize=7.0, color=C_TEXT, linespacing=1.3, zorder=7)

# Callout "Total de hogares"
tbx, tby, tbw, tbh = -1.22, -1.22, 0.82, 0.38
ax_pie.add_patch(FancyBboxPatch((tbx, tby), tbw, tbh, boxstyle='round,pad=0.0,rounding_size=0.06',
                                linewidth=0.9, edgecolor='#b0b0b0', facecolor='white', zorder=5))
ax_pie.text(tbx + tbw/2, tby + tbh * 0.72, 'Total de hogares en zonas urbanas:', ha='center', va='center', fontsize=7.5, color=C_TEXT, zorder=7)
ax_pie.text(tbx + tbw/2, tby + tbh * 0.28, f'{TOTAL_HOG:,.0f}', ha='center', va='center', fontsize=12.5, fontweight='bold', color=C_TEXT, zorder=7)

# ══════════════════════════════════════════════════════════════════════════════
# PANELES LATERALES
# ══════════════════════════════════════════════════════════════════════════════
def draw_panel_bubble(fig, left, bottom, width, height, cats, vals, bar_colors, title, title_color):
    ax_bg = fig.add_axes([left, bottom, width, height], zorder=2)
    ax_bg.set_xlim(0, 1); ax_bg.set_ylim(0, 1); ax_bg.axis('off'); ax_bg.patch.set_visible(False)
    ax_bg.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle='round,pad=0.0,rounding_size=0.012', linewidth=1.0, edgecolor='#c0c0c0', facecolor='#F8F8FA', transform=ax_bg.transAxes, zorder=1, clip_on=False))

    mid_y, tw_ax, td_adj = 0.50, 0.09, 0.046 * (height / width)
    p1, p2, tip = (0.0, mid_y + tw_ax / 2), (0.0, mid_y - tw_ax / 2), (-td_adj, mid_y)
    ax_bg.add_patch(plt.Polygon([p1, tip, p2], closed=True, facecolor='#F8F8FA', edgecolor='#c0c0c0', linewidth=1.0, transform=ax_bg.transAxes, zorder=1, clip_on=False))
    ax_bg.plot([0, 0], [p1[1], p2[1]], color='#F8F8FA', lw=2.5, transform=ax_bg.transAxes, zorder=2, clip_on=False)

    fig.text(left + width * 0.07, bottom + height * 0.91, title, fontsize=10, color=title_color, fontweight='bold', ha='left', va='center', zorder=10)

    pad_l, pad_r, pad_b, pad_t = 0.10, 0.04, 0.24, 0.24
    ax = fig.add_axes([left + width * pad_l, bottom + height * pad_b, width * (1 - pad_l - pad_r), height * (1 - pad_b - pad_t)], zorder=3)
    ax.set_facecolor('none')

    xs, bar_width = np.arange(len(cats)), 0.45
    bars = ax.bar(xs, vals, color=bar_colors, width=bar_width, edgecolor='white', linewidth=1.2, zorder=3)

    y_max = max(vals) if max(vals) > 0 else 1
    ax.set_ylim(0, y_max * 1.80)

    for bar, v_val in zip(bars, vals):
        cx_, cy_ = bar.get_x() + bar.get_width() / 2, bar.get_height()
        ax.text(cx_, cy_ + y_max * 0.05, f'{v_val:.0f}%', ha='center', va='bottom', fontsize=11, fontweight='bold', color=C_TEXT, zorder=6,
                bbox=dict(boxstyle='round,pad=0.25,rounding_size=0.4', facecolor='white', edgecolor=title_color, linewidth=0.9))

    ax.tick_params(left=False, bottom=False, labelleft=False)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.set_xticks(xs); ax.set_xticklabels(cats, fontsize=8.0, color=C_TEXT, linespacing=1.2)
    ax.tick_params(axis='x', pad=4, length=0); ax.set_xlim(-0.65, len(cats) - 1 + 0.65)

draw_panel_bubble(fig, left=0.527, bottom=0.510, width=0.448, height=0.388,
                  cats=list(un_srv.keys()), vals=list(un_srv.values()), bar_colors=['#5c9596', '#64a0a1', '#86adae'], title='Un servicio', title_color=C_UNO)

draw_panel_bubble(fig, left=0.527, bottom=0.103, width=0.448, height=0.388,
                  cats=list(dos_srv.keys()), vals=list(dos_srv.values()), bar_colors=['#234244', '#3b6667', '#4c7d7e'], title='Dos servicios', title_color=C_DOS)

# ══════════════════════════════════════════════════════════════════════════════
# NOTAS Y FUENTE
# ══════════════════════════════════════════════════════════════════════════════
fig.text(0.040, 0.055, "Fuente:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.083, 0.055, "IFT con datos de la ENDUTIH 2023, del INEGI. Datos disponibles en https://www.inegi.org.mx/programas/endutih/2023/.", fontsize=8, color=C_TEXT)
fig.text(0.040, 0.033, "Nota:", fontweight='bold', fontsize=8, color=C_TEXT)
fig.text(0.073, 0.033, "Los porcentajes pueden no sumar 100% debido al redondeo.", fontsize=8, color=C_TEXT)

plt.savefig(OUTPUT_PATH, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"Figura guardada en: {OUTPUT_PATH}")
plt.close()