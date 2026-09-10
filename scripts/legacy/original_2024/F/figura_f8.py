import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import numpy as np
import textwrap
import re

# ── 1. RUTA AL ARCHIVO EXCEL ──────────────────────────────────────────────────
ruta_archivo = r'C:\Users\ivan-\Documents\GitHub\anuario\datos\F.8\mociba2023_tabulados.xlsx'

# ── 2. LEER LA TABLA ──────────────────────────────────────────────────────────
df = pd.read_excel(ruta_archivo, sheet_name='1.42')

# Listas para guardar los datos extraídos
plataformas = []
porcentajes = []

# ── 3. EXTRACCIÓN DINÁMICA DE DATOS ───────────────────────────────────────────
# Recorremos todas las columnas buscando la palabra 'Relativos' en la fila 15
for col in range(len(df.columns)):
    if str(df.iloc[15, col]).strip() == 'Relativos':
        # El nombre de la red social está en la fila 14, una columna a la izquierda
        nombre = str(df.iloc[14, col-1]).strip()
        
        # Por si la celda combinada desfasó el nombre una columna más
        if nombre.lower() == 'nan':
            nombre = str(df.iloc[14, col-2]).strip()
            
        # Limpiar el nombre (quitarle numeritos al final si los tiene)
        nombre = re.sub(r'\d+$', '', nombre).strip()
        
        # El valor porcentual está en la fila 17
        valor = df.iloc[17, col]
        
        # Guardar solo si el valor es un número válido (Ignorar "NS" - No sabe)
        if pd.notna(valor) and str(valor).strip() != 'NS':
            # Ajustar nombres largos para que quepan en la gráfica
            nombre_wrap = textwrap.fill(nombre, width=15)
            plataformas.append(nombre_wrap)
            porcentajes.append(float(valor))

# ── 4. PREPARAR DATOS (Ordenar de mayor a menor) ──────────────────────────────
df_res = pd.DataFrame({'Medio': plataformas, 'Porcentaje': porcentajes})
df_res = df_res.sort_values(by='Porcentaje', ascending=False).reset_index(drop=True)

# ── 5. CONFIGURACIÓN DE GRÁFICA (Estilo F.16) ─────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Color Teal institucional de la guía
COLOR_BARRA = '#86adae'
color_texto = '#3c3c3b'

x = np.arange(len(df_res))
width = 0.6 

# Dibujar las barras
bars = ax.bar(x, df_res['Porcentaje'], width, color=COLOR_BARRA, edgecolor='none', zorder=2)

# ── 6. CHIPS DE DATOS REDONDEADOS ─────────────────────────────────────────────
for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height:.1f}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 6),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=COLOR_BARRA, linewidth=0.8))

# ── 7. DISEÑO LIMPIO DE EJES ──────────────────────────────────────────────────
ax.set_xticks(x)
ax.set_xticklabels(df_res['Medio'], fontsize=9, fontweight='normal', color=color_texto)

ax.set_ylim(0, df_res['Porcentaje'].max() * 1.25)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

# Cuadrícula y espinas
ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# ── 8. TÍTULOS ────────────────────────────────────────────────────────────────
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura F.8.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Porcentaje de población de 12 años y más que vivió ciberacoso por medios digitales", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(105, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# ── 9. NOTAS AL PIE ───────────────────────────────────────────────────────────
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = ('INEGI. Módulo sobre Ciberacoso (MOCIBA) 2023.')
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# ── 10. GUARDAR ───────────────────────────────────────────────────────────────
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
plt.savefig(r'C:\Users\ivan-\Documents\GitHub\anuario\output\figura_f8.png', dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')

# Mostrar los datos extraídos en consola para validación
print("\n--- DATOS CALCULADOS ---")
for index, row in df_res.iterrows():
    print(f"{row['Medio'].replace(chr(10), ' ')}: {row['Porcentaje']:.1f}%")

print("\n¡Gráfica F.8 generada con éxito con el estilo F.16!")
plt.show()