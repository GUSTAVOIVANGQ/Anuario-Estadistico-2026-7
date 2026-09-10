import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from _plot_data_logger import enable_plot_data_logging
enable_plot_data_logging()
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# ─── Rutas ────────────────────────────────────────────────────────────────────────
INPUT  = r"C:\Users\ivan-\Documents\GitHub\anuario\datos\b.16\TD_ACC_BAF_XT_XC_VA.csv"
OUTPUT = r"C:\Users\ivan-\Documents\GitHub\anuario\output\Figura_B16.png"
Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)

# ─── Lectura ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT, encoding="cp1252")

# Normalizar nombre duplicado
df["TECNO_ACCESO_INTERNET"] = df["TECNO_ACCESO_INTERNET"].str.strip()
df["TECNO_ACCESO_INTERNET"] = df["TECNO_ACCESO_INTERNET"].replace(
    {"TecnologÃ­a MÃ³vil": "TecnologÃ­a mÃ³vil"}
)

# ─── Filtros ──────────────────────────────────────────────────────────────────────
TECNO_PRINCIPALES = ["Fibra óptica", "Cable coaxial", "DSL",
                     "Tecnología móvil", "Satelital"]

def get_totals(year, mes=12):
    d = df[(df["ANIO"] == year) & (df["MES"] == mes)]
    d = d[d["TECNO_ACCESO_INTERNET"].isin(TECNO_PRINCIPALES)]
    res   = d.groupby("TECNO_ACCESO_INTERNET")["A_RESIDENCIAL_E"].sum()
    nores = d.groupby("TECNO_ACCESO_INTERNET")["A_NO_RESIDENCIAL_E"].sum()
    return res.reindex(TECNO_PRINCIPALES, fill_value=0), \
           nores.reindex(TECNO_PRINCIPALES, fill_value=0)

res23,  nores23  = get_totals(2023)
res22,  nores22  = get_totals(2022)

# ─── Tasas de crecimiento ─────────────────────────────────────────────────────────
def tasa(v23, v22):
    return {t: ((v23[t] - v22[t]) / v22[t] * 100) if v22[t] > 0 else 0
            for t in TECNO_PRINCIPALES}

tc_res  = tasa(res23,  res22)
tc_nores = tasa(nores23, nores22)

total_res  = res23.sum()
total_nores = nores23.sum()
tc_total_res  = (total_res  - res22.sum())  / res22.sum()  * 100
tc_total_nores = (total_nores - nores22.sum()) / nores22.sum() * 100

# ─── Estilos y Colores Institucionales ────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
C_TEXT = '#3c3c3b'
color_borde_caja = '#D1D1DF'
color_lineas = '#A0A0B0'

COLORS = {
    "Fibra óptica":     "#132b2d",
    "Cable coaxial":    "#3b6667",
    "DSL":              "#64a0a1",
    "Tecnología móvil": "#86adae",
    "Satelital":        "#afafaf",
}
BAR_POS = "#3b6667"
BAR_NEG = "#86adae"

chip_style = dict(boxstyle="round,pad=0.4", fc="white", ec="#D1D1DF", lw=1.2)

# Coordenadas retraídas en X para "Cable coaxial" y "DSL" para evitar colisión con la gráfica de barras
PIE_LBL_POS = {
    "Residencial": {
        "Fibra óptica":     (-1.0, -1.0),
        "Tecnología móvil": ( 0.5,  1.2),
        "DSL":              ( 1.0,  0.8),  # Retraído hacia el centro
        "Cable coaxial":    ( 1.05, 0.2),  # Retraído fuertemente hacia el centro
        "Satelital":        (-0.8,  1.0)
    },
    "No Residencial": {
        "Fibra óptica":     (-1.0, -1.0),
        "DSL":              ( 0.9,  0.9),
        "Cable coaxial":    ( 1.05, 0.1),  # Retraído fuertemente hacia el centro
        "Satelital":        (-0.8,  1.0)
    }
}

# ─── Layout General y Eje de Fondo ────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 10), facecolor='white')

# Eje de fondo para cajas UI
bg_ax = fig.add_axes([0, 0, 1, 1], zorder=0)
bg_ax.axis('off')
bg_ax.set_xlim(0, 1)
bg_ax.set_ylim(0, 1)

# ─── Funciones de Dibujo UI ───────────────────────────────────────────────────────
def draw_pie_with_labels(ax, totals, panel_type):
    sizes = [totals[t] for t in TECNO_PRINCIPALES]
    colors = [COLORS[t] for t in TECNO_PRINCIPALES]
    
    wedges, _ = ax.pie(sizes, colors=colors, startangle=90, counterclock=True,
                       wedgeprops=dict(edgecolor="white", linewidth=1.5))
    ax.set_aspect("equal")
    ax.patch.set_alpha(0)
    
    total = sum(sizes)
    for i, p in enumerate(wedges):
        pct = sizes[i] / total * 100
        if pct < 0.05: continue
        
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y_edge = np.sin(np.deg2rad(ang))
        x_edge = np.cos(np.deg2rad(ang))
        
        t_name = TECNO_PRINCIPALES[i]
        x_text, y_text = PIE_LBL_POS[panel_type].get(t_name, (x_edge*1.2, y_edge*1.2))
        
        ha = "left" if x_text > 0 else "right"
        
        chip_text = f"{pct:.1f}%"
        ax.annotate(chip_text, xy=(x_edge, y_edge), xytext=(x_text, y_text),
                    ha=ha, va="center",
                    arrowprops=dict(arrowstyle="-", color=color_lineas, lw=1.2),
                    bbox=chip_style, color=COLORS[t_name], fontweight='bold', fontsize=11,
                    annotation_clip=False)
        
        # Posicionamiento inteligente del nombre
        y_label_offset = 0.22 if y_text > 0 else -0.22
        va_label = "bottom" if y_text > 0 else "top"
        
        ax.text(x_text, y_text + y_label_offset, t_name.replace(" ", "\n"), ha=ha, va=va_label,
                fontsize=9, fontweight='bold', color='#6C6C85', clip_on=False)

def draw_bar_chart(ax, data_tc, totals):
    tecno_bar = [t for t in TECNO_PRINCIPALES if abs(data_tc[t]) > 0.05 and totals[t] > 0 and t != "Satelital"]
    vals = [data_tc[t] for t in tecno_bar]
    cols = [BAR_POS if v >= 0 else BAR_NEG for v in vals]
    
    x_pos = np.arange(len(tecno_bar))
    ax.bar(x_pos, vals, color=cols, width=0.45, zorder=3)
    ax.axhline(0, color='#A0A0B0', linewidth=1, zorder=2)
    ax.axis('off')
    
    y_min, y_max = min(vals + [0]), max(vals + [0])
    ax.set_ylim(y_min - abs(y_min)*0.4 - 10, y_max + abs(y_max)*0.4 + 10)
    
    for i, v in enumerate(vals):
        offset = 5 if v >= 0 else -18
        ax.text(i, v + offset, f"{v:.1f}%", ha='center', va='center', 
                fontweight='bold', fontsize=9, color=C_TEXT, clip_on=False)
        
        y_name = -8 if v >= 0 else 8
        ax.text(i, y_name, tecno_bar[i].replace(" ", "\n"), 
                ha='center', va='top' if v >= 0 else 'bottom', 
                fontsize=8, color='#6C6C85', clip_on=False)

def draw_section(offset_x, type_title, totals, tc, tc_total, is_res=True):
    # Caja principal del panel
    box_main = patches.FancyBboxPatch((0.02 + offset_x, 0.08), 0.45, 0.78, 
                                      boxstyle="round,pad=0.02", ec=color_borde_caja, fc="white", lw=1.5)
    bg_ax.add_patch(box_main)
    
    # Chip título
    w_title = 0.14 if is_res else 0.16
    t_box = patches.FancyBboxPatch((0.175 + offset_x, 0.85), w_title, 0.05, 
                                   boxstyle="round,pad=0.02", ec="#EEEEEE", fc="white", lw=1)
    bg_ax.add_patch(t_box)
    bg_ax.text(0.175 + w_title/2 + offset_x, 0.875, type_title, 
               fontsize=16, fontweight='bold', color=C_TEXT, ha='center', va='center')

    # Burbuja de Totales
    bubble = patches.FancyBboxPatch((0.28 + offset_x, 0.62), 0.15, 0.08, 
                                    boxstyle="round,pad=0.01", ec="#EEEEEE", fc="white", lw=1)
    bg_ax.add_patch(bubble)
    bg_ax.text(0.355 + offset_x, 0.675, f"Accesos {'residenciales' if is_res else 'no residenciales'}\na nivel nacional:", 
               fontsize=8, color='#6C6C85', ha='center', va='center')
    bg_ax.text(0.355 + offset_x, 0.64, f"{int(sum(totals)):,}", 
               fontsize=18, fontweight='bold', color=C_TEXT, ha='center', va='center')

    # Caja pequeña (Tasa total)
    box_bot = patches.FancyBboxPatch((0.05 + offset_x, 0.10), 0.14, 0.06, 
                                     boxstyle="round,pad=0.01", ec="#EEEEEE", fc="white", lw=1)
    bg_ax.add_patch(box_bot)
    bg_ax.text(0.12 + offset_x, 0.13, f"Tasa de crecimiento\nanual de {tc_total:.1f}%", 
               fontsize=9, ha='center', va='center', color='#6C6C85')

    # Caja fondo de gráfica de barras
    box_bar = patches.FancyBboxPatch((0.27 + offset_x, 0.10), 0.17, 0.40, 
                                     boxstyle="round,pad=0.01", ec=color_borde_caja, fc="white", lw=1)
    bg_ax.add_patch(box_bar)
    bg_ax.text(0.355 + offset_x, 0.47, "Tasa de crecimiento anual,\ndic 2022 - dic 2023", 
               fontsize=10, color='#6C6C85', ha='center', va='center')

    # Gráfica de Pastel
    ax_pie = fig.add_axes([0.02 + offset_x, 0.20, 0.22, 0.45], zorder=5)
    draw_pie_with_labels(ax_pie, totals, type_title)

    # Gráfica de barras
    ax_bar = fig.add_axes([0.28 + offset_x, 0.16, 0.15, 0.28], zorder=5)
    draw_bar_chart(ax_bar, tc, totals)

# Renderizar ambos paneles
draw_section(0.00, "Residencial", res23, tc_res, tc_total_res, is_res=True)
draw_section(0.49, "No Residencial", nores23, tc_nores, tc_total_nores, is_res=False)

# ─── Encabezado y Pie Institucional (dibujado en el fondo) ────────────────────────
bg_ax.text(0.028, 0.952, '   ', fontsize=2, va='center',
         bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))
bg_ax.text(0.046, 0.952, 'Figura B.16.', fontsize=13, fontweight='bold', color=C_TEXT, va='center')
bg_ax.text(0.125, 0.952, 'Distribución de los accesos al servicio fijo de Internet por tecnología de conexión y por segmento', 
           fontsize=13, color=C_TEXT, va='center')

bg_ax.text(0.040, 0.045, "Fuente:", fontweight='bold', fontsize=8, color=C_TEXT)
bg_ax.text(0.075, 0.045, "IFT con datos de los operadores de telecomunicaciones a diciembre de 2023.", fontsize=8, color=C_TEXT)
bg_ax.text(0.040, 0.025, "Nota:", fontweight='bold', fontsize=8, color=C_TEXT)
bg_ax.text(0.070, 0.025, "Los porcentajes pueden no sumar 100% debido al redondeo.", fontsize=8, color=C_TEXT)

# ─── Guardado ─────────────────────────────────────────────────────────────────────
plt.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor="white", edgecolor='none')
plt.close()
print(f"Figura guardada exitosamente en: {OUTPUT}")