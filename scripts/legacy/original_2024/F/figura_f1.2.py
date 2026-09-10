import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
import sys
import os

sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()

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

# ─── 1. CARGA Y PREPARACIÓN DE DATOS ─────────────────────────────────────────
ruta_datos = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\F.1.2\tr_endutih_usuarios_anual_2023.csv"
print("Cargando la base de datos y calculando valores reales para F.1.2...")
df = pd.read_csv(ruta_datos, low_memory=False)

for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Universo base: Usuarios de internet de 6 años o más
df_int = df[(df['P7_1'] == 1) & (df['EDAD'] >= 6)].copy()

# Gobierno: OR de las 4 sub-preguntas
df_int['GOB'] = (
    (df_int['P7_35_1'] == 1) | (df_int['P7_35_2'] == 1) |
    (df_int['P7_35_3'] == 1) | (df_int['P7_35_4'] == 1)
).astype(int)

usuarios_sexo = df_int.groupby('SEXO')['FAC_PER'].sum()
tot_m = usuarios_sexo.get(2, 1)
tot_h = usuarios_sexo.get(1, 1)

def get_pct(col):
    sub = df_int[df_int[col] == 1].groupby('SEXO')['FAC_PER'].sum()
    m = round(sub.get(2, 0) / tot_m * 100)
    h = round(sub.get(1, 0) / tot_h * 100)
    return m, h

# Panel destacado superior derecho
pct_f_yt, pct_m_yt = get_pct('P7_13_3')

# Fila 1 (6 tarjetas)
actividades_row1 = [
    ("Escuchar música gratis\n(Spotify, Google music,\netcétera)", 'P7_13_4'),
    ("Películas, series y\naudiovisuales de pago\n(Netflix, OTT, etc.)", 'P7_13_2'),
    ("Leer periódicos,\nrevistas o libros", 'P7_13_1'),
    ("Compras\npor Internet", 'P7_21'),
    ("Interacción con\nel gobierno", 'GOB'),
    ("Jugar en línea", 'P7_13_5')
]
row1_data = [(t, *get_pct(c)) for t, c in actividades_row1]

# Fila 2 (5 tarjetas)
actividades_row2 = [
    ("Pagos por Internet", 'P7_28'),
    ("Uso de la banca\nelectrónica", 'P7_33'),
    ("TV en web (canales\nabiertos por Internet)", 'P7_13_7'),
    ("Ventas por Internet", 'P7_19'),
    ("Radio AM y FM", 'P7_18_1')
]
row2_data = [(t, *get_pct(c)) for t, c in actividades_row2]

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
    
    ax.text(x + w/2, y + h - 0.035, title, ha='center', va='top', 
            fontsize=8.5, color=TEXT_MAIN, fontweight='bold', linespacing=1.2)

    x_text = x + w * 0.65
    y_f_label = y + h * 0.52
    y_f_pct   = y + h * 0.38
    y_m_label = y + h * 0.22
    y_m_pct   = y + h * 0.08

    ax.text(x_text, y_f_label, "Mujeres", ha='center', va='center', fontsize=8, color=TEXT_MAIN, fontweight='medium')
    ax.text(x_text, y_f_pct, f"{pct_f}%", ha='center', va='center', fontsize=16, color=COLOR_MUJERES, fontweight='bold')

    ax.text(x_text, y_m_label, "Hombres", ha='center', va='center', fontsize=8, color=TEXT_MAIN, fontweight='medium')
    ax.text(x_text, y_m_pct, f"{pct_m}%", ha='center', va='center', fontsize=16, color=COLOR_HOMBRES, fontweight='bold')

# ─── CONFIGURACIÓN DEL LIENZO ───────────────────────────────────────────────
fig = plt.figure(figsize=(16, 8.5), facecolor=BG_FIG)
ax = fig.add_axes((0.08, 0.22, 0.84, 0.63), facecolor=BG_AXES)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# ─── ENCABEZADO ─────────────────────────────────────────────────────────────
ax.text(0.0, 1.15, '   ', bbox=dict(boxstyle='round,pad=0.4,rounding_size=0.1', facecolor=SQUARE_COL, edgecolor='none'))
ax.text(0.025, 1.15, "Figura F.1.", fontweight='bold', fontsize=14, color=TEXT_MAIN, va='center')
ax.text(0.12, 1.15, "Actividades realizadas en Internet", fontweight='medium', fontsize=14, color=TEXT_MAIN, va='center')

# ─── PANELES SUPERIORES ─────────────────────────────────────────────────────
# 1. Panel Izquierdo
add_rounded_box(ax, 0.0, 0.74, 0.20, 0.28, bg_color=CARD_BG, r=0.02)
ax.text(0.10, 0.88, "Actividades realizadas\nen Internet", ha='center', va='center', fontsize=12, color=TEXT_MAIN, fontweight='bold', linespacing=1.3)

# 2. Panel Central
add_rounded_box(ax, 0.22, 0.74, 0.43, 0.28, bg_color=CARD_BG, r=0.02)
ax.text(0.435, 0.94, "Usuarios de Internet", ha='center', va='center', fontsize=11, color=TEXT_MAIN, fontweight='bold')

ax.text(0.33, 0.87, "Mujeres", ha='center', va='center', fontsize=9, color=TEXT_MAIN, fontweight='medium')
ax.text(0.33, 0.80, f"{int(tot_m):,}", ha='center', va='center', fontsize=18, color=COLOR_MUJERES, fontweight='bold')

ax.text(0.54, 0.87, "Hombres", ha='center', va='center', fontsize=9, color=TEXT_MAIN, fontweight='medium')
ax.text(0.54, 0.80, f"{int(tot_h):,}", ha='center', va='center', fontsize=18, color=COLOR_HOMBRES, fontweight='bold')

# 3. Panel Derecho
add_rounded_box(ax, 0.67, 0.74, 0.33, 0.28, bg_color=CARD_BG, r=0.02)
ax.text(0.835, 0.96, "Porcentajes respecto al total\nde usuarios de Internet", ha='center', va='center', fontsize=8, color=TEXT_LIGHT, linespacing=1.2)
ax.text(0.835, 0.90, "Películas, series y audiovisuales\ngratuitos (YouTube)", ha='center', va='center', fontsize=9, color=TEXT_MAIN, fontweight='bold', linespacing=1.2)

ax.text(0.76, 0.83, "Mujeres", ha='center', va='center', fontsize=9, color=TEXT_MAIN, fontweight='medium')
ax.text(0.76, 0.78, f"{pct_f_yt}%", ha='center', va='center', fontsize=18, color=COLOR_MUJERES, fontweight='bold')

ax.text(0.91, 0.83, "Hombres", ha='center', va='center', fontsize=9, color=TEXT_MAIN, fontweight='medium')
ax.text(0.91, 0.78, f"{pct_m_yt}%", ha='center', va='center', fontsize=18, color=COLOR_HOMBRES, fontweight='bold')


# ─── CUADRÍCULA FILA 1 (6 tarjetas) ─────────────────────────────────────────
ROW1_Y = 0.37
ROW1_H = 0.35
GAP = 0.015

w_total_row1 = 1.0 - (GAP * 5)
w_card_row1 = w_total_row1 / 6

for i, (title, pf, pm) in enumerate(row1_data):
    cx = i * (w_card_row1 + GAP)
    draw_activity_card(ax, cx, ROW1_Y, w_card_row1, ROW1_H, title, pf, pm)

# ─── CUADRÍCULA FILA 2 (5 tarjetas) ─────────────────────────────────────────
ROW2_Y = 0.00
ROW2_H = 0.35

w_total_row2 = 1.0 - (GAP * 4)
w_card_row2 = w_total_row2 / 5

for i, (title, pf, pm) in enumerate(row2_data):
    cx = i * (w_card_row2 + GAP)
    draw_activity_card(ax, cx, ROW2_Y, w_card_row2, ROW2_H, title, pf, pm)

# ─── PIE DE PÁGINA ──────────────────────────────────────────────────────────
fig.text(0.08, 0.12, "Fuente:", fontweight='bold', fontsize=8, color=TEXT_MAIN)
fig.text(0.115, 0.12, "IFT con datos de la ENDUTIH 2023, del INEGI. Datos disponibles en https://www.inegi.org.mx/programas/endutih/2023/", fontweight='normal', fontsize=8, color=TEXT_MAIN)

fig.text(0.08, 0.09, "Notas:", fontweight='bold', fontsize=8, color=TEXT_MAIN)
fig.text(0.115, 0.09, "Todos los usuarios se refieren a personas de 6 años o más.", fontweight='normal', fontsize=8, color=TEXT_MAIN)

# ─── GUARDAR Y MOSTRAR ──────────────────────────────────────────────────────
output_dir = r"C:\Users\ivan-\Documents\GitHub\anuario\output"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "figura_f1.2.png")

plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=BG_FIG, edgecolor='none')
print(f"✅ Infografía F.1.2 generada con diseño CRT en: {output_path}")

plt.show()