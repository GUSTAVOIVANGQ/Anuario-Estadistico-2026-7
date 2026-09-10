import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import numpy as np

print("Iniciando el procesamiento de datos...")

# ==========================================
# FASE 1: EXTRACCIÓN Y LIMPIEZA DE DATOS
# ==========================================
archivo_excel = r'C:\Users\ivan-\Documents\GitHub\anuario\datos\F.4\mociba2023_tabulados.xlsx'

df_1_17 = pd.read_excel(archivo_excel, sheet_name='1.17', skiprows=14)
df_1_18 = pd.read_excel(archivo_excel, sheet_name='1.18', skiprows=14)

hombres = df_1_17.iloc[:1000, [0, 3]].dropna().copy()
mujeres = df_1_18.iloc[:1000, [0, 3]].dropna().copy()

hombres.columns = ['Entidad', 'Hombres_Ciberacoso']
mujeres.columns = ['Entidad', 'Mujeres_Ciberacoso']

hombres['Entidad'] = hombres['Entidad'].astype(str).str.strip()
mujeres['Entidad'] = mujeres['Entidad'].astype(str).str.strip()

hombres['Hombres_Ciberacoso'] = pd.to_numeric(hombres['Hombres_Ciberacoso'].astype(str).str.replace(',', ''), errors='coerce')
mujeres['Mujeres_Ciberacoso'] = pd.to_numeric(mujeres['Mujeres_Ciberacoso'].astype(str).str.replace(',', ''), errors='coerce')

total_hombres = hombres[hombres['Entidad'] == 'Estados Unidos Mexicanos']['Hombres_Ciberacoso'].values[0]
total_mujeres = mujeres[mujeres['Entidad'] == 'Estados Unidos Mexicanos']['Mujeres_Ciberacoso'].values[0]

patron_filtro = '^(De |Estados Unidos Mexicanos|Entidad|Absolutos|Estimaciones)'
hombres_estados = hombres[~hombres['Entidad'].str.match(patron_filtro, case=False)].drop_duplicates(subset=['Entidad'])
mujeres_estados = mujeres[~mujeres['Entidad'].str.match(patron_filtro, case=False)].drop_duplicates(subset=['Entidad'])

df_final = pd.merge(hombres_estados, mujeres_estados, on='Entidad', how='inner').head(32)
df_final['Hombres (%)'] = (df_final['Hombres_Ciberacoso'] / total_hombres * 100).round(1)
df_final['Mujeres (%)'] = (df_final['Mujeres_Ciberacoso'] / total_mujeres * 100).round(1)

df_final = df_final.sort_values('Entidad').reset_index(drop=True)

print("Datos calculados con éxito. Generando gráfica...")


# ==========================================
# FASE 2: DIBUJO Y DISEÑO DE LA GRÁFICA
# ==========================================

plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

COLOR_MUJERES = '#86adae'  
COLOR_HOMBRES = '#335a5c'  
color_texto = '#3c3c3b'

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

x = np.arange(len(df_final['Entidad']))
width = 0.35  

rects1 = ax.bar(x - width/2, df_final['Hombres (%)'], width, label='Hombres', color=COLOR_HOMBRES, edgecolor='none', zorder=2)
rects2 = ax.bar(x + width/2, df_final['Mujeres (%)'], width, label='Mujeres', color=COLOR_MUJERES, edgecolor='none', zorder=2)

# Lógica "anti-colisión" para mantener los chips en horizontal
for r1, r2 in zip(rects1, rects2):
    h1 = r1.get_height()
    h2 = r2.get_height()
    
    # Offsets verticales base
    off1, off2 = 4, 4
    
    # Si las barras están muy parejas (diferencia < 1.2%), se escalonan para que los chips horizontales no choquen
    if abs(h1 - h2) < 1.2:
        if h1 >= h2:
            off1 = 12  # Sube el chip de Hombres
        else:
            off2 = 12  # Sube el chip de Mujeres

    # Chip Hombres
    if h1 > 0:
        ax.annotate(f'{h1:.1f}%',
                    xy=(r1.get_x() + r1.get_width() / 2, h1),
                    xytext=(0, off1),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=5.5, color=color_texto, fontweight='bold', zorder=3,
                    bbox=dict(boxstyle="round,pad=0.15,rounding_size=0.4", facecolor='white', edgecolor=r1.get_facecolor(), linewidth=0.6))
    
    # Chip Mujeres
    if h2 > 0:
        ax.annotate(f'{h2:.1f}%',
                    xy=(r2.get_x() + r2.get_width() / 2, h2),
                    xytext=(0, off2),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=5.5, color=color_texto, fontweight='bold', zorder=3,
                    bbox=dict(boxstyle="round,pad=0.15,rounding_size=0.4", facecolor='white', edgecolor=r2.get_facecolor(), linewidth=0.6))

# Diseño de Ejes
ax.set_xticks(x)
ax.set_xticklabels(df_final['Entidad'], rotation=90, fontsize=8.5, fontweight='normal', color=color_texto)

ax.set_ylim(0, 16)  
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.tick_params(axis='y', labelsize=9, colors=color_texto)

ax.grid(axis='y', alpha=1.0, color='#d1d1d1', linewidth=1, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#7c7c7c')
ax.spines['bottom'].set_color('#7c7c7c')

# Títulos
ax.annotate('   ', xy=(0, 1), xycoords='axes fraction', 
            xytext=(0, 30), textcoords='offset points',
            va='center', ha='left', fontsize=2,
            bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))

ax.annotate("Figura F.4.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Prevalencia de ciberacoso por entidad federativa y sexo", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(95, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Leyenda (bajada a 0.10 para no estorbar con las etiquetas largas)
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.10), ncol=2, fontsize=10, frameon=False, handlelength=2.5)

# Notas al pie (bajadas a 0.06 y 0.03 para no estorbar)
font_size_notes = 8
x_start = 0.08
y_fuente = 0.06

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = 'INEGI. Módulo sobre Ciberacoso (MOCIBA) 2023.'
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

y_nota = 0.03
fig.text(x_start, y_nota, "Nota: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
nota_text = 'Datos expresados como porcentaje del total nacional por sexo.'
fig.text(x_start + 0.025, y_nota, nota_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# Ajuste de layout con margen inferior amplio para los nombres de los estados
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.32)
nombre_salida = r'C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_F4.png'
plt.savefig(nombre_salida, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')

print(f"¡Terminado! Gráfica guardada exitosamente como '{nombre_salida}'.")