"""
Figura B.24 â€” ParticipaciÃ³n de mercado del Servicio de TelevisiÃ³n Restringida (2014-2023)
Fuente: IFT con datos de los operadores de telecomunicaciones a diciembre de cada aÃ±o.
Archivo: TD_MARKET_SHARE_TVRES_ITE_VA.CSV
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import matplotlib.patches as mpatches
import numpy as np
import os

# â”€â”€ Rutas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
INPUT  = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\B.24\TD_MARKET_SHARE_TVRES_ITE_VA.CSV"
OUTPUT = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_B24.png"
os.makedirs("output", exist_ok=True)

# â”€â”€ Lectura â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
df = pd.read_csv(INPUT, encoding="cp1252", low_memory=False)
df["MARKET_SHARE"] = pd.to_numeric(
    df["MARKET_SHARE"].astype(str).str.replace("%", "").str.strip(),
    errors="coerce"
).fillna(0)

# â”€â”€ Filtro: diciembre, 2014-2023 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
df = df[(df["MES"] == 12) & (df["ANIO"].between(2014, 2023))]

# â”€â”€ Mapeo a 6 grupos del Anuario â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# IMPORTANTE: imprime los grupos sin mapear para verificar
MAPEO = {
    "GRUPO TELEVISA"   : "Grupo Televisa",
    "CABLEVISION RED"  : "Grupo Televisa",   # filial de Televisa
    "MEGACABLE-MCM"    : "Megacable-MCM",
    "DISH-MVS"         : "Dish-MVS",
    "GRUPO SALINAS"    : "Grupo Salinas",
    "TOTALPLAY"        : "Grupo Salinas",    # filial de Salinas
    "STARGROUP"        : "Stargroup",
    "STAR GROUP"       : "Stargroup",        # variante de nombre
}

def asignar_grupo(nombre):
    n = nombre.strip().upper()
    for k, v in MAPEO.items():
        if k in n:
            return v
    return "Otros"

df["GRUPO_FIGURA"] = df["GRUPO"].apply(asignar_grupo)

# â”€â”€ VerificaciÃ³n: grupos sin mapear con share relevante â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
otros = df[df["GRUPO_FIGURA"] == "Otros"].groupby("GRUPO")["MARKET_SHARE"].sum()
print("=== Grupos clasificados como 'Otros' (total 2014-2023) ===")
print(otros.sort_values(ascending=False).head(20))

# â”€â”€ AgrupaciÃ³n final â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
pivot = (df.groupby(["ANIO", "GRUPO_FIGURA"])["MARKET_SHARE"]
           .sum()
           .unstack(fill_value=0))

# Orden de apilado (de abajo hacia arriba, igual al Anuario)
ORDEN  = ["Grupo Televisa", "Megacable-MCM", "Dish-MVS",
          "Grupo Salinas",  "Stargroup",     "Otros"]
COLORS = {
    "Grupo Televisa" : "#a8d8ea",   # azul claro
    "Megacable-MCM"  : "#1a5276",   # azul oscuro
    "Dish-MVS"       : "#2e4057",   # azul marino
    "Grupo Salinas"  : "#5dade2",   # azul medio
    "Stargroup"      : "#f0a500",   # naranja/Ã¡mbar
    "Otros"          : "#e74c3c",   # rojo
}

# Asegurar que todas las columnas existan
for g in ORDEN:
    if g not in pivot.columns:
        pivot[g] = 0.0
pivot = pivot[ORDEN]

anos  = pivot.index.tolist()
x     = np.arange(len(anos))
width = 0.55

# â”€â”€ VerificaciÃ³n de valores clave vs Anuario â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n=== VerificaciÃ³n vs Anuario (Grupo Televisa) ===")
for a, v in pivot["Grupo Televisa"].items():
    print(f"  {a}: {v:.1f}%")

# â”€â”€ Figura â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
fig, ax = plt.subplots(figsize=(14, 7))
fig.patch.set_facecolor("white")

bottoms = np.zeros(len(anos))
bars_by_group = {}

for grupo in ORDEN:
    vals = pivot[grupo].values
    bars = ax.bar(x, vals, width, bottom=bottoms,
                  color=COLORS[grupo], label=grupo, zorder=2)
    bars_by_group[grupo] = (bars, vals, bottoms.copy())
    # Etiquetas dentro de la barra (solo si >= 0.5%)
    for i, (v, b) in enumerate(zip(vals, bottoms)):
        if v >= 0.5:
            ax.text(x[i], b + v / 2, f"{v:.1f}%",
                    ha="center", va="center",
                    fontsize=7, fontweight="bold", color="white")
    bottoms += vals

# â”€â”€ EstÃ©tica â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
ax.set_xticks(x)
ax.set_xticklabels(anos, fontsize=10)
ax.set_ylim(0, 108)
ax.set_yticks([])
ax.spines[["top", "right", "left"]].set_visible(False)
ax.yaxis.set_visible(False)
ax.set_title(
    "Figura B.24. ParticipaciÃ³n de mercado del Servicio de\nTelevisiÃ³n Restringida (2014-2023)",
    fontsize=13, fontweight="bold", loc="left", pad=12
)

# Leyenda
handles = [mpatches.Patch(color=COLORS[g], label=g) for g in ORDEN]
ax.legend(handles=handles, loc="lower center",
          bbox_to_anchor=(0.5, -0.12), ncol=6, fontsize=9,
          frameon=False)

note = ("Fuente: IFT con datos proporcionados por los operadores de telecomunicaciones a diciembre de cada aÃ±o.\n"
        "Nota: ParticipaciÃ³n de mercado calculada con respecto al nÃºmero de accesos del servicio televisiÃ³n restringida.")
fig.text(0.01, -0.04, note, fontsize=7.5, color="#555555")

plt.tight_layout()
plt.savefig(OUTPUT, dpi=150, bbox_inches="tight")
print(f"\nGuardado en {OUTPUT}")
plt.show()

