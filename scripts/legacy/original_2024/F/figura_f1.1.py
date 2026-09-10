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
ruta_datos = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\F.1.1\tr_endutih_usuarios_anual_2023.csv"
print("Cargando la base de datos y calculando valores reales...")
df = pd.read_csv(ruta_datos, low_memory=False)
df.columns = df.columns.str.upper()

# Filtrar el Universo Base (Usuarios de Internet mediante celular, 6+ años)
base_celular = df[(pd.to_numeric(df['EDAD'], errors='coerce') >= 6) & 
                  (pd.to_numeric(df['P7_1'], errors='coerce') == 1) &
                  (pd.to_numeric(df['P7_6_4'], errors='coerce') == 1)]

# Denominadores poblacionales base calculados
totales_universo = base_celular.groupby('SEXO')['FAC_PER'].sum()
total_hombres = totales_universo.get(1, 0)
total_mujeres = totales_universo.get(2, 0)

# Diccionario de actividades (Actividad : Columna en ENDUTIH)
diccionario_actividades = {
    'Mensajería instantánea': 'P7_16_9',       
    'Descargaron aplicaciones': 'P7_11_2',     
    'Acceder a redes sociales': 'P7_35_3',     
    'Contenidos de audio y video': 'P7_17_2',  
    'Jugar': 'P7_33',                          
    'Adquirir bienes o servicios': 'P7_34_2',  
    'Tránsito y navegación': 'P7_32_1',        
    'Acceder a Banca Móvil': 'P7_22_2',        
    'Editar fotos o videos': 'P7_36_3'         
}

# Cálculo dinámico de porcentajes
resultados = {}
for actividad, columna in diccionario_actividades.items():
    if columna in base_celular.columns:
        positivos = base_celular[pd.to_numeric(base_celular[columna], errors='coerce') == 1]
        sum_pos = positivos.groupby('SEXO')['FAC_PER'].sum()
        
        h_pct = round((sum_pos.get(1, 0) / total_hombres) * 100)
        m_pct = round((sum_pos.get(2, 0) / total_mujeres) * 100)
        resultados[actividad] = (m_pct, h_pct)

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
    
    # Título superior
    ax.text(x + w/2, y + h - 0.035, title, ha='center', va='top', 
            fontsize=8.5, color=TEXT_MAIN, fontweight='bold', linespacing=1.2)

    # Coordenadas X desplazadas al 65% del ancho de la tarjeta
    x_text = x + w * 0.65 

    # Coordenadas Y ajustadas (movidas hacia arriba respecto a la iteración anterior)
    y_f_label = y + h * 0.58
    y_f_pct   = y + h * 0.44
    y_m_label = y + h * 0.28
    y_m_pct   = y + h * 0.14

    # Bloque Mujeres (Arriba)
    ax.text(x_text, y_f_label, "Mujeres", ha='center', va='center', fontsize=8, color=TEXT_MAIN, fontweight='medium')
    ax.text(x_text, y_f_pct, f"{pct_f}%", ha='center', va='center', fontsize=16, color=COLOR_MUJERES, fontweight='bold')

    # Bloque Hombres (Abajo)
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
ax.text(0.12, 1.15, "Aplicaciones instaladas mediante Smartphone", fontweight='medium', fontsize=14, color=TEXT_MAIN, va='center')

# ─── PANELES SUPERIORES ─────────────────────────────────────────────────────
# 1. Panel Izquierdo
add_rounded_box(ax, 0.0, 0.74, 0.20, 0.28, bg_color=CARD_BG, r=0.02)
ax.text(0.10, 0.88, "Aplicaciones instaladas\nmediante Smartphone", ha='center', va='center', fontsize=12, color=TEXT_MAIN, fontweight='bold', linespacing=1.3)

# 2. Panel Central (Total Usuarios)
add_rounded_box(ax, 0.22, 0.74, 0.43, 0.28, bg_color=CARD_BG, r=0.02)
ax.text(0.435, 0.94, "Usuarios de Internet mediante Smartphone", ha='center', va='center', fontsize=11, color=TEXT_MAIN, fontweight='bold')

ax.text(0.33, 0.89, "Mujeres", ha='center', va='center', fontsize=9, color=TEXT_MAIN, fontweight='medium')
ax.text(0.33, 0.82, f"{int(total_mujeres):,}", ha='center', va='center', fontsize=18, color=COLOR_MUJERES, fontweight='bold')

ax.text(0.54, 0.89, "Hombres", ha='center', va='center', fontsize=9, color=TEXT_MAIN, fontweight='medium')
ax.text(0.54, 0.82, f"{int(total_hombres):,}", ha='center', va='center', fontsize=18, color=COLOR_HOMBRES, fontweight='bold')

# 3. Panel Derecho (Descargas)
add_rounded_box(ax, 0.67, 0.74, 0.33, 0.28, bg_color=CARD_BG, r=0.02)
ax.text(0.835, 0.94, "Descargaron aplicaciones", ha='center', va='center', fontsize=11, color=TEXT_MAIN, fontweight='bold', linespacing=1.2)

m_desc, h_desc = resultados.get('Descargaron aplicaciones', (0, 0))
ax.text(0.76, 0.85, "Mujeres", ha='center', va='center', fontsize=9, color=TEXT_MAIN, fontweight='medium')
ax.text(0.76, 0.80, f"{m_desc}%", ha='center', va='center', fontsize=18, color=COLOR_MUJERES, fontweight='bold')

ax.text(0.91, 0.85, "Hombres", ha='center', va='center', fontsize=9, color=TEXT_MAIN, fontweight='medium')
ax.text(0.91, 0.80, f"{h_desc}%", ha='center', va='center', fontsize=18, color=COLOR_HOMBRES, fontweight='bold')


# ─── CUADRÍCULA DE ACTIVIDADES ──────────────────────────────────────────────
actividades_grid = [
    ("Mensajería instantánea\n(WhatsApp, Messenger,\netcétera)", 'Mensajería instantánea'),
    ("Acceder a redes sociales\n(Facebook, Instagram,\netcétera)", 'Acceder a redes sociales'),
    ("Contenidos de audio y video\n(YouTube, Spotify,\netcétera)", 'Contenidos de audio y video'),
    ("Jugar\n(Pokémon go, Candy Crush)", 'Jugar'),
    ("Tránsito y navegación\n(Google Maps)", 'Tránsito y navegación'),
    ("Adquirir bienes o servicios\n(Uber, Rappi)", 'Adquirir bienes o servicios'),
    ("Acceder a Banca Móvil\n(BBVA, Banamex)", 'Acceder a Banca Móvil'),
    ("Editar fotos o videos", 'Editar fotos o videos')
]

ROW1_Y = 0.37
ROW1_H = 0.35
ROW2_Y = 0.00
ROW2_H = 0.35
GAP = 0.02

# Ancho para 4 tarjetas
w_total_grid = 1.0 - (GAP * 3)
w_card = w_total_grid / 4

for i in range(4):
    # Fila 1
    titulo1, clave1 = actividades_grid[i]
    pf1, pm1 = resultados.get(clave1, (0, 0))
    cx1 = i * (w_card + GAP)
    draw_activity_card(ax, cx1, ROW1_Y, w_card, ROW1_H, titulo1, pf1, pm1)

    # Fila 2
    titulo2, clave2 = actividades_grid[i + 4]
    pf2, pm2 = resultados.get(clave2, (0, 0))
    cx2 = i * (w_card + GAP)
    draw_activity_card(ax, cx2, ROW2_Y, w_card, ROW2_H, titulo2, pf2, pm2)


# ─── PIE DE PÁGINA ──────────────────────────────────────────────────────────
fig.text(0.08, 0.12, "Fuente:", fontweight='bold', fontsize=8, color=TEXT_MAIN)
fig.text(0.115, 0.12, "IFT con datos de la ENDUTIH 2023, del INEGI. Datos disponibles en https://www.inegi.org.mx/programas/endutih/2023/", fontweight='normal', fontsize=8, color=TEXT_MAIN)

fig.text(0.08, 0.09, "Notas:", fontweight='bold', fontsize=8, color=TEXT_MAIN)
fig.text(0.115, 0.09, "Todos los usuarios se refieren a personas de 6 años o más.", fontweight='normal', fontsize=8, color=TEXT_MAIN)


# ─── GUARDAR Y MOSTRAR ──────────────────────────────────────────────────────
output_dir = r"C:\Users\ivan-\Documents\GitHub\anuario\output"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "figura_f1.1.png")

plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=BG_FIG, edgecolor='none')
print(f"✅ Infografía de aplicaciones generada con diseño CRT en: {output_path}")

plt.show()