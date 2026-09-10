import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import numpy as np

# ── 1. Cargar los datos ───────────────────────────────────────────────────────
file_movil = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\E.1\Tercera Encuesta 2023_Tel Móvil.xlsx"
file_fija = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\E.1\Tercera Encuesta 2023_Tel Fija.xlsx"
file_int_tv = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\E.1\Tercera Encuesta 2023_Int&TV.xlsx"

df_movil = pd.read_excel(file_movil)
df_fija = pd.read_excel(file_fija)
df_int_tv = pd.read_excel(file_int_tv)

# ── 2. Columnas base ──────────────────────────────────────────────────────────
col_movil = 'En términos generales, ¿qué tan satisfecho se encuentra con el servicio de telefonía móvil que ha recibido en los últimos 12 meses? Recodificada'
col_fija = 'En términos generales, ¿qué tan satisfecho se encuentra con el servicio de telefonía fija que ha recibido en los últimos 12 meses? Recodificada'
col_tv = 'En términos generales, ¿qué tan satisfecho se encuentra con el servicio de televisión de paga que ha recibido en los últimos 12 meses? Recodificada '
col_int = 'En términos generales, ¿qué tan satisfecho se encuentra con el servicio de Internet que ha recibido en los últimos 12 meses? Recodificada '

# ── 3. Cálculo ────────────────────────────────────────────────────────────────
val_movil = df_movil[col_movil].dropna().mean()
val_fija = df_fija[col_fija].dropna().mean()
val_tv = df_int_tv[col_tv].dropna().mean()
val_int = df_int_tv[col_int].dropna().mean()

data_calc = {
    'Servicio': ['Internet fijo', 'Televisión de paga', 'Telefonía móvil', 'Telefonía fija'],
    'Calculado': [val_int, val_tv, val_movil, val_fija]
}
df_calc = pd.DataFrame(data_calc)
df_calc = df_calc.sort_values(by='Calculado', ascending=True)

# ── 4. Configuración Gráfica (Estilo F.16 exacto) ─────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')
color_texto = '#3c3c3b'

# Colores institucionales de la Paleta Teal usados en el proyecto
colors = ['#86adae', '#64a0a1', '#4c7d7e', '#335a5c'] 

# ── 5. Dibujar Barras Horizontales ────────────────────────────────────────────
bars = ax.barh(df_calc['Servicio'], df_calc['Calculado'], color=colors, edgecolor='none', height=0.55, zorder=2)

# ── 6. Etiquetas de datos (Chips idénticos a F.16 adaptados a horizontal) ─────
for bar in bars:
    width_val = bar.get_width()
    bar_color = bar.get_facecolor()
    ax.annotate(f'{width_val:.1f}', 
                xy=(width_val, bar.get_y() + bar.get_height() / 2),
                xytext=(15, 0), 
                textcoords="offset points",
                ha='left', va='center', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

# ── 7. Diseño limpio de Ejes (Estilo F.16) ────────────────────────────────────
ax.set_xlim(0, max(df_calc['Calculado']) * 1.15)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}'))

ax.tick_params(axis='y', length=0, labelsize=9, colors=color_texto)
ax.tick_params(axis='x', labelsize=9, colors=color_texto)

# Cuadrícula en X estilo F.16
ax.grid(axis='x', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0) 
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# ── 8. Títulos (Cuadrado decorativo y tipografía exacta a F.16) ───────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura E.1.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Índice General de Satisfacción por tipo de servicio a nivel nacional", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# ── 9. Notas al pie (Posiciones de F.16) ──────────────────────────────────────
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = 'IFT con información de la Tercera Encuesta 2023, Usuarios de Servicios de Telecomunicaciones.'
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# ── 10. Guardar ───────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.20, right=0.92, top=0.85, bottom=0.22)
ruta_salida = r"C:\Users\ivan-\Documents\GitHub\anuario\output\figura_E1.png"
os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
plt.savefig(ruta_salida, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"¡Figura E.1 construida con estilo idéntico a F.16 en: {ruta_salida}!")