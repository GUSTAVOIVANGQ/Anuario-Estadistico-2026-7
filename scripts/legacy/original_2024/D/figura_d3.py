"""
Figura D.3 — Horas promedio de uso de internet por grupos de edad
Fuente: IFT con datos de la ENDUTIH 2023, del INEGI. Datos disponibles en https://www.inegi.org.mx/programas/endutih/2023/.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()

# ───────────────────────────────────────────────────────────────────────
# 1. LEER DATOS
# ───────────────────────────────────────────────────────────────────────
RUTA = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\D.3\tr_endutih_usuarios_anual_2023.csv"

df = pd.read_csv(RUTA, low_memory=False)

print("Columnas disponibles:", df.columns.tolist())
print(f"Total de registros: {len(df):,}")
print(f"\nDistribución de P7_4 (horas de uso):\n{df['P7_4'].value_counts().sort_index()}")
print(f"\nRango de edades: {df['EDAD'].min()} a {df['EDAD'].max()}")

# ───────────────────────────────────────────────────────────────────────
# 2. LIMPIAR Y PREPARAR
# ───────────────────────────────────────────────────────────────────────
df_valido = pd.DataFrame({
    'horas': pd.to_numeric(df['P7_4'], errors='coerce'),
    'edad': pd.to_numeric(df['EDAD'], errors='coerce'),
    'factor': pd.to_numeric(df['FAC_PER'], errors='coerce')
})

df_valido = df_valido.dropna(subset=['horas', 'edad', 'factor']).copy()
print(f"\nRegistros válidos para cálculo: {len(df_valido):,}")

# ───────────────────────────────────────────────────────────────────────
# 3. DEFINIR GRUPOS DE EDAD
# ───────────────────────────────────────────────────────────────────────
bins   = [5, 11, 17, 24, 34, 44, 54, 64, 999]
labels = ['6 a 11', '12 a 17', '18 a 24', '25 a 34',
          '35 a 44', '45 a 54', '55 a 64', '65 o más']

df_valido['grupo_edad'] = pd.cut(
    df_valido['edad'],
    bins=bins,
    labels=labels,
    right=True
)

# ───────────────────────────────────────────────────────────────────────
# 4. CALCULAR PROMEDIO PONDERADO POR GRUPO
# ───────────────────────────────────────────────────────────────────────
def promedio_ponderado(grupo):
    return np.average(grupo['horas'], weights=grupo['factor'])

resultado = (
    df_valido
    .dropna(subset=['grupo_edad'])
    .groupby('grupo_edad', observed=True)
    .apply(promedio_ponderado)
    .reset_index()
)
resultado.columns = ['grupo', 'horas_promedio']
resultado['horas_promedio'] = resultado['horas_promedio'].round(1)

print("\n=== RESULTADOS ===")
print(resultado.to_string(index=False))

# ───────────────────────────────────────────────────────────────────────
# 5. GRAFICAR CON ESTILO INSTITUCIONAL (Ref: Figura F.16 + Colores CRT)
# ───────────────────────────────────────────────────────────────────────
orden_anuario = ['18 a 24', '25 a 34', '12 a 17', '35 a 44',
                 '45 a 54', '55 a 64', '65 o más', '6 a 11']
res_ordenado = resultado.set_index('grupo').reindex(orden_anuario).reset_index()

plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

fig, ax = plt.subplots(figsize=(16, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8F8FA')

# Paleta de colores solicitada
COLORES_CRT = ['#86adae', '#64a0a1', '#5c9596', '#4c7d7e', '#3b6667', '#335a5c', '#234244', '#132b2d']
color_texto = '#3c3c3b'

x = np.arange(len(res_ordenado['grupo']))
width = 0.55

# Dibujar las barras con la paleta iterada de CRT
bars = ax.bar(x, res_ordenado['horas_promedio'], width, color=COLORES_CRT, edgecolor='none', zorder=2)

# Etiquetas de datos (Chips estilo F.16) con borde dinámico
for rect in bars:
    height = rect.get_height()
    bar_color = rect.get_facecolor() # Extrae el color individual de cada barra para el borde del chip
    ax.annotate(f'{height:.1f}',
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 6),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=8, color=color_texto, fontweight='bold', zorder=3,
                bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.8", facecolor='white', edgecolor=bar_color, linewidth=0.8))

# Diseño limpio de Ejes conforme a F.16
ax.set_xticks(x)
ax.set_xticklabels([])
ax.tick_params(axis='x', length=0, pad=8)

for idx, (group, color) in enumerate(zip(res_ordenado['grupo'], COLORES_CRT)):
    # Cuadrado de color
    ax.annotate('   ', xy=(idx - 0.20, -0.04), xycoords=ax.get_xaxis_transform(),
                bbox=dict(boxstyle="round,pad=0.2,rounding_size=0.4", facecolor=color, edgecolor='none'),
                ha='center', va='center')
    # Etiqueta de texto
    ax.annotate(group, xy=(idx - 0.10, -0.04), xycoords=ax.get_xaxis_transform(),
                fontsize=9, fontweight='bold', color=color_texto, ha='left', va='center')

ax.set_ylim(0, max(res_ordenado['horas_promedio']) * 1.25)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}'))
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

ax.annotate("Figura D.3.", xy=(0, 1), xycoords='axes fraction', 
            xytext=(15, 30), textcoords='offset points',
            fontsize=14, fontweight='bold', color=color_texto, ha='left', va='center')

ax.annotate(" Horas promedio de uso de internet por grupos de edad", 
            xy=(0, 1), xycoords='axes fraction', 
            xytext=(100, 30), textcoords='offset points',
            fontsize=14, fontweight='medium', color=color_texto, ha='left', va='center')

# Notas al pie
font_size_notes = 8
x_start = 0.08
y_fuente = 0.08

fig.text(x_start, y_fuente, "Fuente: ", fontsize=font_size_notes, fontweight='bold', color=color_texto, ha='left', va='top')
fuente_text = 'IFT con datos de la ENDUTIH 2023, del INEGI. Datos disponibles en https://www.inegi.org.mx/programas/endutih/2023/.'
fig.text(x_start + 0.032, y_fuente, fuente_text, fontsize=font_size_notes, fontweight='normal', color=color_texto, ha='left', va='top')

# Guardar
fig.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)
ruta_salida = Path(r'C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_D3.png')
ruta_salida.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(ruta_salida, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"¡Figura D.3 construida y validada con estilo institucional y colores CRT en {ruta_salida}!")