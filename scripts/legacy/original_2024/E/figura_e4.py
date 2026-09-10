import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()

# 1. Cargar bases de datos histÃ³ricas
df22 = pd.read_excel(r"C:\Users\ivan-\Documents\GitHub\anuario\datos\E.4\Base de datos_Cuarta Encuesta 2022_MiPymes.xlsx")
df23 = pd.read_excel(r"C:\Users\ivan-\Documents\GitHub\anuario\datos\E.4\Base de datos_Cuarta Encuesta 2023_MiPymes.xlsx")

# 2. Definir las preguntas (columnas) exactas de los servicios contratados
cols = {
    'Internet Fijo': 'Hablando exclusivamente de la empresa o negocio Â¿cuÃ¡les de los siguientes servicios se tienen contratados para poder llevar a cabo las actividades laborales? ConexiÃ³n a Internet fijo (incluye conexiÃ³n Wi-Fi)',
    'TelefonÃ­a Fija': 'Hablando exclusivamente de la empresa o negocio Â¿cuÃ¡les de los siguientes servicios se tienen contratados para poder llevar a cabo las actividades laborales? TelefonÃ­a fija',
    'TelefonÃ­a MÃ³vil': 'Hablando exclusivamente de la empresa o negocio Â¿cuÃ¡les de los siguientes servicios se tienen contratados para poder llevar a cabo las actividades laborales? TelefonÃ­a mÃ³vil',
    'Datos MÃ³viles': 'Hablando exclusivamente de la empresa o negocio Â¿cuÃ¡les de los siguientes servicios se tienen contratados para poder llevar a cabo las actividades laborales? ConexiÃ³n a Internet por datos mÃ³viles (por red de telefonÃ­a mÃ³vil)',
    'TelevisiÃ³n de Paga': 'Hablando exclusivamente de la empresa o negocio Â¿cuÃ¡les de los siguientes servicios se tienen contratados para poder llevar a cabo las actividades laborales? TelevisiÃ³n de paga'
}

sizes = ['General', 'Micro', 'PequeÃ±a', 'Mediana']
results = []

# 3. FunciÃ³n matemÃ¡tica para calcular porcentajes usando el Factor de ExpansiÃ³n
def calc_percentages(df, year):
    peso = 'Factor de ExpansiÃ³n Final'
    if peso not in df.columns:
         peso = 'Factor de ExpansiÃ³n Final Normalizado' # Fallback por si cambia el nombre
         
    for svc_name, col_name in cols.items():
        if col_name in df.columns:
            # Filtrar valores nulos
            df_filtered = df[[col_name, peso, 'ClasificaciÃ³n de la empresa por su tamaÃ±o']].dropna(subset=[col_name, peso])
            
            # Calcular para el rubro "General"
            total_weight = df_filtered[peso].sum()
            yes_weight = df_filtered[df_filtered[col_name] == 'SÃ­'][peso].sum()
            results.append({'Service': svc_name, 'Year': year, 'Size': 'General', 'Percentage': (yes_weight/total_weight)*100})
            
            # Calcular segmentado por tamaÃ±o (Micro, PequeÃ±a, Mediana)
            for size in ['Micro', 'PequeÃ±a', 'Mediana']:
                df_size = df_filtered[df_filtered['ClasificaciÃ³n de la empresa por su tamaÃ±o'] == size]
                size_total = df_size[peso].sum()
                size_yes = df_size[df_size[col_name] == 'SÃ­'][peso].sum()
                if size_total > 0:
                    results.append({'Service': svc_name, 'Year': year, 'Size': size, 'Percentage': (size_yes/size_total)*100})

# Ejecutar cÃ¡lculos para ambos aÃ±os
calc_percentages(df22, 2022)
calc_percentages(df23, 2023)
df_results = pd.DataFrame(results)

# 4. Construir la interfaz de la tabla tipo infografÃ­a (Reemplazando los grÃ¡ficos de barras)
fig, ax = plt.subplots(figsize=(15, 8))
plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.15)
ax.set_xlim(0, 11.5)
ax.set_ylim(-1.5, 7.5) # Expandir para acomodar tÃ­tulo y notas
ax.axis('off')

# TÃ­tulo de la figura
ax.text(0, 7.3, "â– ", color='#EA746A', fontsize=12, ha='left', va='center')
ax.text(0.2, 7.3, "Figura E.4.", fontweight='bold', color='#636E7B', fontsize=14, ha='left', va='center')
ax.text(1.3, 7.3, "Servicios de telecomunicaciones que contratan las MiPymes (2022-2023)", color='#636E7B', fontsize=14, ha='left', va='center')

import matplotlib.patches as patches

# Definir colores de celdas segÃºn el aÃ±o y tipo de empresa
colors = {
    'Header_2022': '#D8E8E2',
    'Header_2023': '#F0F5F8',
    ('General', 2022): '#D8E8E2',
    ('General', 2023): '#F0F5F8',
    ('Micro', 2022): '#F9DFD6',
    ('Micro', 2023): '#F4AE9D',
    ('PequeÃ±a', 2022): '#F4BCAD',
    ('PequeÃ±a', 2023): '#EC7C6F',
    ('Mediana', 2022): '#C0D5E0',
    ('Mediana', 2023): '#80A8BA'
}

# FunciÃ³n para dibujar celdas (fondo y texto)
def draw_cell(x, y, w, h, bg_color, text='', font_weight='normal', font_size=11, text_color='#5B6770', align='center'):
    if bg_color:
        rect = patches.Rectangle((x, y), w, h, facecolor=bg_color, edgecolor='none', zorder=1)
        ax.add_patch(rect)
    if text:
        if align == 'center':
            ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=font_size, fontweight=font_weight, color=text_color, zorder=3)
        elif align == 'top-center':
            ax.text(x + w/2, y + h - 0.2, text, ha='center', va='top', fontsize=font_size, fontweight=font_weight, color=text_color, zorder=3)

# Dibujar cabeceras
draw_cell(0, 4.6, 1.5, 2.1, 'white', 'Tipo de\nempresa', 'bold', 11, '#636E7B')

services_keys = ['Internet Fijo', 'TelefonÃ­a Fija', 'TelefonÃ­a MÃ³vil', 'Datos MÃ³viles', 'TelevisiÃ³n de Paga']
services_display = [
    'Internet fijo',
    'TelefonÃ­a fija',
    'TelefonÃ­a mÃ³vil',
    'ConexiÃ³n a Internet\npor datos mÃ³viles\n(por red de telefonÃ­a mÃ³vil)',
    'TelevisiÃ³n de paga'
]

# Dibujar fila de encabezados de Servicios (Row 0) y fila de AÃ±os (Row 1)
for i, (s_key, s_disp) in enumerate(zip(services_keys, services_display)):
    x_start = 1.5 + i * 2.0
    # Fondo blanco e iconos se dibujarÃ¡n arriba
    draw_cell(x_start, 5.2, 2.0, 1.5, 'white')
    # Texto un poco mÃ¡s abajo
    ty = 5.6 if i != 3 else 5.7
    ax.text(x_start + 1.0, ty - 0.2, s_disp, ha='center', va='center', fontsize=10, fontweight='bold', color='#636E7B', zorder=3)
    
    # AÃ±os
    draw_cell(x_start, 4.6, 1.0, 0.6, colors['Header_2022'], '2022', 'bold', 10, '#636E7B')
    draw_cell(x_start + 1.0, 4.6, 1.0, 0.6, colors['Header_2023'], '2023', 'bold', 10, '#636E7B')

# Filas de datos
row_labels = ['General', 'Micro', 'PequeÃ±a', 'Mediana']
y_starts = [3.6, 2.4, 1.2, 0]
heights = [1.0, 1.2, 1.2, 1.2]

for r_idx, (r_label, y_pos, h) in enumerate(zip(row_labels, y_starts, heights)):
    draw_cell(0, y_pos, 1.5, h, 'white', r_label if r_label == 'General' else '', 'bold' if r_label == 'General' else 'normal', 11, '#636E7B', align='top-center' if r_label != 'General' else 'center')
    if r_label != 'General':
        ax.text(0.75, y_pos + h - 0.2, r_label, ha='center', va='top', fontsize=11, fontweight='bold', color='#636E7B', zorder=3)
        
    for c_idx, svc in enumerate(services_keys):
        x_base = 1.5 + c_idx * 2.0
        
        # 2022
        val22 = df_results[(df_results['Service'] == svc) & (df_results['Year'] == 2022) & (df_results['Size'] == r_label)]['Percentage'].values
        val22_str = f"{val22[0]:.1f}%" if len(val22) > 0 else "-"
        draw_cell(x_base, y_pos, 1.0, h, colors[(r_label, 2022)], val22_str, 'bold', 11, '#333333')
        
        # 2023
        val23 = df_results[(df_results['Service'] == svc) & (df_results['Year'] == 2023) & (df_results['Size'] == r_label)]['Percentage'].values
        val23_str = f"{val23[0]:.1f}%" if len(val23) > 0 else "-"
        draw_cell(x_base + 1.0, y_pos, 1.0, h, colors[(r_label, 2023)], val23_str, 'bold', 11, '#333333')

# DIBUJO DE ICONOS #
# Iconos de Tipos de Empresa
def draw_building(ax, x, y, tipo):
    if tipo == 'Micro': cols, rows, w, h, color = 2, 2, 0.4, 0.5, '#F19584'
    elif tipo == 'PequeÃ±a': cols, rows, w, h, color = 2, 3, 0.4, 0.65, '#EA7C6B'
    else: cols, rows, w, h, color = 4, 3, 0.8, 0.65, '#EE9886'
    bx, by = x - w/2, y - h/2 - 0.1
    ax.add_patch(patches.Rectangle((bx, by), w, h, facecolor=color, zorder=5))
    door_w, door_h = 0.12, 0.15
    ax.add_patch(patches.Rectangle((x - door_w/2, by), door_w, door_h, facecolor='#C1D7E3', zorder=6))
    win_w, win_h = 0.08, 0.08
    margin_x = (w - (cols * win_w)) / (cols + 1)
    for r in range(rows):
        wy = by + h - (r + 1) * (win_h + 0.05) - 0.03
        for c in range(cols):
            wx = bx + margin_x + c * (win_w + margin_x)
            if wy < by + door_h and x - door_w/2 - 0.02 < wx < x + door_w/2 + 0.02: continue
            ax.add_patch(patches.Rectangle((wx, wy), win_w, win_h, facecolor='#C1D7E3', zorder=6))

draw_building(ax, 0.75, 2.4 + 0.5, 'Micro')
draw_building(ax, 0.75, 1.2 + 0.5, 'PequeÃ±a')
draw_building(ax, 0.75, 0 + 0.5, 'Mediana')

# Dibujar sÃ­mbolos simples para los Servicios
def draw_router(ax, x, y):
    ax.add_patch(patches.Rectangle((x-0.2, y-0.1), 0.4, 0.15, facecolor='#F39B8B', zorder=5))
    ax.add_patch(patches.Rectangle((x-0.08, y-0.03), 0.16, 0.02, facecolor='white', zorder=6)) # luces
    ax.plot([x-0.15, x-0.15], [y, y+0.15], color='#F39B8B', lw=2, zorder=4)
    ax.plot([x+0.15, x+0.15], [y, y+0.15], color='#F39B8B', lw=2, zorder=4)
    for i, r in enumerate([0.1, 0.18, 0.26]):
        ax.add_patch(patches.Arc((x, y+0.05), r, r, theta1=45, theta2=135, color='#78A1B5', lw=2, zorder=5))

def draw_phone(ax, x, y):
    ax.add_patch(patches.Rectangle((x-0.15, y-0.15), 0.3, 0.2, facecolor='#5B6B8A', zorder=5))
    ax.add_patch(patches.Rectangle((x-0.1, y-0.1), 0.2, 0.1, facecolor='#FFFFFF', zorder=6))
    ax.plot([x-0.12, x-0.05], [y-0.05, y-0.05], color='#5B6B8A', lw=1, zorder=7)
    ax.plot([x-0.15, x+0.15], [y+0.1, y+0.1], color='#5B6B8A', lw=3, solid_capstyle='round', zorder=5) # auricular
    ax.plot([x-0.1, x-0.1], [y+0.05, y+0.1], color='#5B6B8A', lw=2, zorder=5) # left hook
    ax.plot([x+0.1, x+0.1], [y+0.05, y+0.1], color='#5B6B8A', lw=2, zorder=5) # right hook

def draw_mobile(ax, x, y):
    ax.add_patch(patches.FancyBboxPatch((x-0.11, y-0.2), 0.22, 0.4, boxstyle="round,pad=0.03", facecolor='#5B6B8A', edgecolor='none', zorder=5))
    ax.add_patch(patches.Rectangle((x-0.09, y-0.15), 0.18, 0.3, facecolor='#FFFFFF', zorder=6))
    ax.add_patch(patches.Circle((x, y-0.17), 0.015, facecolor='#FFFFFF', zorder=6))

def draw_mobile_data(ax, x, y):
    ax.add_patch(patches.Circle((x-0.15, y+0.05), 0.12, facecolor='#5B6B8A', zorder=5)) # deco
    ax.add_patch(patches.Circle((x+0.05, y-0.1), 0.1, facecolor='#EA746A', zorder=5)) # play deco
    for i, r in enumerate([0.15, 0.25, 0.35]):
        ax.add_patch(patches.Arc((x+0.05, y+0.05), r, r, theta1=45, theta2=135, color='#5B6B8A', lw=3, zorder=5))
    for i, r in enumerate([0.2, 0.3, 0.4]):
        ax.add_patch(patches.Arc((x-0.1, y-0.1), r, r, theta1=225, theta2=315, color='#78A1B5', lw=3, zorder=5))

def draw_tv(ax, x, y):
    ax.add_patch(patches.FancyBboxPatch((x-0.2, y-0.12), 0.4, 0.24, boxstyle="round,pad=0.02", facecolor='#78A1B5', edgecolor='none', zorder=5))
    ax.add_patch(patches.Rectangle((x-0.18, y-0.1), 0.36, 0.2, facecolor='#FFFFFF', zorder=6))
    ax.plot([x, x], [y-0.14, y-0.24], color='#5B6B8A', lw=4, zorder=5)
    ax.plot([x-0.08, x+0.08], [y-0.24, y-0.24], color='#5B6B8A', lw=2, zorder=5)

draw_router(ax, 2.5, 6.2)
draw_phone(ax, 4.5, 6.2)
draw_mobile(ax, 6.5, 6.2)
draw_mobile_data(ax, 8.5, 6.1)
draw_tv(ax, 10.5, 6.2)

# LÃNEAS DIVISORIAS (CuadrÃ­cula interactiva y bordes) #
line_color = '#C9CED3'
line_width = 1.0

# LÃ­neas horizontales
ax.plot([0, 11.5], [6.7, 6.7], color=line_color, lw=line_width, zorder=4) # Top general
ax.plot([1.5, 11.5], [5.2, 5.2], color=line_color, lw=line_width, zorder=4) # Debajo de iconos
ax.plot([0, 11.5], [4.6, 4.6], color=line_color, lw=line_width, zorder=4) # Debajo de aÃ±os
ax.plot([0, 11.5], [3.6, 3.6], color=line_color, lw=line_width, zorder=4) # Debajo de General
ax.plot([0, 11.5], [2.4, 2.4], color=line_color, lw=line_width, zorder=4) # Debajo de Micro
ax.plot([0, 11.5], [1.2, 1.2], color=line_color, lw=line_width, zorder=4) # Debajo de PequeÃ±a
ax.plot([0, 11.5], [0, 0], color=line_color, lw=line_width, zorder=4)     # Bottom

# LÃ­neas verticales
ax.plot([0, 0], [0, 6.7], color=line_color, lw=line_width, zorder=4) # Borde izquierdo
ax.plot([1.5, 1.5], [0, 6.7], color=line_color, lw=line_width, zorder=4) # Post Tipo empresa
ax.plot([11.5, 11.5], [0, 6.7], color=line_color, lw=line_width, zorder=4) # Borde derecho

# Separadores de Servicios
for x_sep in [3.5, 5.5, 7.5, 9.5]:
    ax.plot([x_sep, x_sep], [0, 6.7], color=line_color, lw=line_width, zorder=4)

# Separadores de AÃ±os (solo dentro de datos de servicio, hasta la cabecera)
for x_sep in [2.5, 4.5, 6.5, 8.5, 10.5]:
    ax.plot([x_sep, x_sep], [0, 5.2], color=line_color, lw=line_width, zorder=4)

# Borde exterior redondeado para mejorar el estilo
outer_rect = patches.FancyBboxPatch((0, 0), 11.5, 6.7, boxstyle="round,pad=0.02,rounding_size=0.2", 
                                    edgecolor=line_color, facecolor='none', lw=line_width, zorder=5)
ax.add_patch(outer_rect)

# PIE DE PÃGINA #
footer_y = -0.5
ax.text(0, footer_y, "Fuente:", fontweight='bold', color='#4A5C6A', fontsize=9, ha='left', va='top')
ax.text(0.65, footer_y, "IFT con informaciÃ³n de la Cuarta Encuesta 2023, Usuarios de Servicios de Telecomunicaciones (micro, pequeÃ±as y medianas empresas).", color='#4A5C6A', fontsize=9, ha='left', va='top')
ax.text(0, footer_y - 0.25, "Para mÃ¡s informaciÃ³n consultar: https://www.ift.org.mx/usuarios-y-audiencias/encuestas-trimestrales.", color='#4A5C6A', fontsize=9, ha='left', va='top')
ax.text(0, footer_y - 0.5, "Nota:", fontweight='bold', color='#4A5C6A', fontsize=9, ha='left', va='top')
ax.text(0.45, footer_y - 0.5, "Respuesta mÃºltiple, por lo que la suma no da 100%. Es importante seÃ±alar que los resultados pueden presentar variaciones que pueden ser explicadas por el error teÃ³rico de cada encuesta.", color='#4A5C6A', fontsize=9, ha='left', va='top')

# Guardar la grÃ¡fica en el output
plt.savefig(r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_E4.png", dpi=300, bbox_inches='tight')

