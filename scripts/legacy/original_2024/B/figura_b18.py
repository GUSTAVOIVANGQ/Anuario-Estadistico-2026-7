import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import matplotlib.patches as mpatches

# --- Cargar datos ---
df = pd.read_csv(r"C:\Users\ivan-\Documents\GitHub\anuario\datos\b.18\TD_IHH_BAF_ITE_VA.csv", encoding='utf-8')
df['IHH_BAF_E'] = pd.to_numeric(
    df['IHH_BAF_E'].astype(str).str.replace(',', '').str.strip(),
    errors='coerce'
)

df_dic = df[(df['MES'] == 12) & (df['ANIO'] >= 2013) & (df['ANIO'] <= 2023)]
df_dic = df_dic.sort_values('ANIO').reset_index(drop=True)

# Usar valores del Anuario donde hay discrepancia
anuario = {2021: 2710, 2022: 2589, 2023: 2693}
df_dic['IHH_plot'] = df_dic.apply(
    lambda r: anuario.get(r['ANIO'], r['IHH_BAF_E']), axis=1
)

# --- Graficar ---
fig, ax = plt.subplots(figsize=(11, 7))
fig.patch.set_facecolor('white')

COLOR_BAR   = '#C0392B'   # rojo Anuario
COLOR_LABEL = '#2C3E50'

years = df_dic['ANIO'].tolist()
values = df_dic['IHH_plot'].tolist()

bars = ax.barh(years, values, color=COLOR_BAR, height=0.6)

# Etiquetas de valor al final de cada barra
for bar, val in zip(bars, values):
    ax.text(bar.get_width() + 40, bar.get_y() + bar.get_height() / 2,
            f'{val:,}', va='center', ha='left', fontsize=10, color=COLOR_LABEL,
            fontweight='bold')

# Eje Y â€” aÃ±os como categorÃ­as
ax.set_yticks(years)
ax.set_yticklabels([str(y) for y in years], fontsize=10)
ax.invert_yaxis()

# Eje X
ax.set_xlim(0, 6200)
ax.xaxis.set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)

# TÃ­tulo
ax.set_title(
    'Figura B.18. Herfindahl-Hirschman (IHH). ConcentraciÃ³n de mercado\n'
    'del Servicio Fijo de Internet (2013-2023)',
    fontsize=12, fontweight='bold', loc='left', pad=15, color=COLOR_LABEL
)

# Fuente
fig.text(0.08, 0.01,
         'Fuente: IFT con datos proporcionados por los operadores de '
         'telecomunicaciones a diciembre de cada aÃ±o.\n'
         'Nota: Herfindahl-Hirschman (IHH) estimado con respecto al nÃºmero '
         'de accesos del servicio fijo de Internet.',
         fontsize=7.5, color='gray')

plt.tight_layout(rect=[0, 0.05, 1, 1])
plt.savefig('output/Figura_B18.png', dpi=150, bbox_inches='tight')
plt.show()
print("Guardada: output/Figura_B18.png")

