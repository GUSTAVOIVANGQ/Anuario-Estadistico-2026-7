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
ruta_datos = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\F.1.3\tr_endutih_usuarios_anual_2023.csv"
print("Cargando la base de datos y calculando valores reales para F.1.3...")
df = pd.read_csv(ruta_datos, low_memory=False)

filtro_base = (df['EDAD'] >= 6) & (df['P6_1'] == 1)
filtro_mujeres = filtro_base & (df['SEXO'] == 2)
filtro_hombres = filtro_base & (df['SEXO'] == 1)

total_mujeres_compu = df.loc[filtro_mujeres, 'FAC_PER'].sum()
total_hombres_compu = df.loc[filtro_hombres, 'FAC_PER'].sum()

def get_pct(col):
    suma_mujeres = df.loc[filtro_mujeres & (df[col] == 1), 'FAC_PER'].sum()
    suma_hombres = df.loc[filtro_hombres & (df[col] == 1), 'FAC_PER'].sum()
    m_pct = round((suma_mujeres / total_mujeres_compu) * 100)
    h_pct = round((suma_hombres / total_hombres_compu) * 100)
    return m_pct, h_pct

# Panel destacado superior derecho
pct_f_email, pct_m_email = get_pct('P6_8_1')

# Fila 1 (4 tarjetas)
actividades_row1 = [
    ("Descargar contenidos\nde Internet", 'P6_8_2'),
    ("Crear archivos\nde texto", 'P6_8_4'),
    ("Copiar archivos entre\ndirectorios (carpetas)", 'P6_8_3'),
    ("Crear\npresentaciones", 'P6_8_6')
]
row1_data = [(t, *get_pct(c)) for t, c in actividades_row1]

# Fila 2 (4 tarjetas)
actividades_row2 = [
    ("Crear hojas\nde cálculo", 'P6_8_5'),
    ("Instalar dispositivos\nperiféricos", 'P6_8_7'),
    ("Crear o usar\nbases de datos", 'P6_8_8'),
    ("Programar en lenguaje\nespecializado", 'P6_8_9')
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
    y_f_label = y + h * 0.58
    y_f_pct   = y + h * 0.44
    y_m_label = y + h * 0.28
    y_m_pct   = y + h * 0.14

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
ax.text(0.12, 1.15, "Habilidades en la computadora", fontweight='medium', fontsize=14, color=TEXT_MAIN, va='center')

# ─── PANELES SUPERIORES ─────────────────────────────────────────────────────
# 1. Panel Izquierdo
add_rounded_box(ax, 0.0, 0.74, 0.20, 0.28, bg_color=CARD_BG, r=0.02)
ax.text(0.10, 0.88, "Habilidades en\nla computadora", ha='center', va='center', fontsize=12, color=TEXT_MAIN, fontweight='bold', linespacing=1.3)

# 2. Panel Central
add_rounded_box(ax, 0.22, 0.74, 0.43, 0.28, bg_color=CARD_BG, r=0.02)
ax.text(0.435, 0.94, "Usuarios de computadora", ha='center', va='center', fontsize=11, color=TEXT_MAIN, fontweight='bold')

ax.text(0.33, 0.89, "Mujeres", ha='center', va='center', fontsize=9, color=TEXT_MAIN, fontweight='medium')
ax.text(0.33, 0.82, f"{int(total_mujeres_compu):,}", ha='center', va='center', fontsize=18, color=COLOR_MUJERES, fontweight='bold')

ax.text(0.54, 0.89, "Hombres", ha='center', va='center', fontsize=9, color=TEXT_MAIN, fontweight='medium')
ax.text(0.54, 0.82, f"{int(total_hombres_compu):,}", ha='center', va='center', fontsize=18, color=COLOR_HOMBRES, fontweight='bold')

# 3. Panel Derecho
add_rounded_box(ax, 0.67, 0.74, 0.33, 0.28, bg_color=CARD_BG, r=0.02)
ax.text(0.835, 0.94, "Enviar y recibir\ncorreo electrónico", ha='center', va='center', fontsize=11, color=TEXT_MAIN, fontweight='bold', linespacing=1.2)

ax.text(0.76, 0.85, "Mujeres", ha='center', va='center', fontsize=9, color=TEXT_MAIN, fontweight='medium')
ax.text(0.76, 0.80, f"{pct_f_email}%", ha='center', va='center', fontsize=18, color=COLOR_MUJERES, fontweight='bold')

ax.text(0.91, 0.85, "Hombres", ha='center', va='center', fontsize=9, color=TEXT_MAIN, fontweight='medium')
ax.text(0.91, 0.80, f"{pct_m_email}%", ha='center', va='center', fontsize=18, color=COLOR_HOMBRES, fontweight='bold')


# ─── CUADRÍCULA DE ACTIVIDADES (4x2) ────────────────────────────────────────
ROW1_Y = 0.37
ROW1_H = 0.35
ROW2_Y = 0.00
ROW2_H = 0.35
GAP = 0.02

w_total_grid = 1.0 - (GAP * 3)
w_card = w_total_grid / 4

# Fila 1
for i, (title, pf, pm) in enumerate(row1_data):
    cx = i * (w_card + GAP)
    draw_activity_card(ax, cx, ROW1_Y, w_card, ROW1_H, title, pf, pm)

# Fila 2
for i, (title, pf, pm) in enumerate(row2_data):
    cx = i * (w_card + GAP)
    draw_activity_card(ax, cx, ROW2_Y, w_card, ROW2_H, title, pf, pm)

# ─── PIE DE PÁGINA ──────────────────────────────────────────────────────────
fig.text(0.08, 0.12, "Fuente:", fontweight='bold', fontsize=8, color=TEXT_MAIN)
fig.text(0.115, 0.12, "IFT con datos de la ENDUTIH 2023, del INEGI. Datos disponibles en https://www.inegi.org.mx/programas/endutih/2023/", fontweight='normal', fontsize=8, color=TEXT_MAIN)

fig.text(0.08, 0.09, "Notas:", fontweight='bold', fontsize=8, color=TEXT_MAIN)
fig.text(0.115, 0.09, "Todos los usuarios se refieren a personas de 6 años o más.", fontweight='normal', fontsize=8, color=TEXT_MAIN)


# ─── GUARDAR Y MOSTRAR ──────────────────────────────────────────────────────
output_dir = r"C:\Users\ivan-\Documents\GitHub\anuario\output"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "figura_f1.3.png")

plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=BG_FIG, edgecolor='none')
print(f"✅ Infografía F.1.3 generada con diseño CRT en: {output_path}")

plt.show()