"""Figura C.14: tráfico del servicio móvil de acceso a Internet por tecnología."""
from __future__ import annotations
<<<<<<< HEAD
import math,sys,zipfile
=======
import sys,zipfile
>>>>>>> 93f2bf9f8ee9510be3d7cd1817e28eb1b7e51fc4
from pathlib import Path,PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np
FIGURE_ID="C.14";SOURCE_ID="crt_bit_todo_2025_q2";TABLE="TD_TRAF_INTMOVIL_ITE_VA.csv";TEXT="#3c3c3b";COLS=["TRAF_TB_2G_E","TRAF_TB_3G_E","TRAF_TB_4G_E","TRAF_TB_NO_ESPECIFICADO_E","TOTAL_TB_E"]
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        n=next((n for n in z.namelist() if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold()),None)
        if not n:raise ValueError(f"TODO.zip no contiene {TABLE}")
        with z.open(n) as f:return pd.read_csv(f,encoding="latin-1",low_memory=False)
def _num(s):return pd.to_numeric(s.astype("string").str.replace(",","",regex=False),errors="coerce")
def build_metrics(raw):
    d=raw.copy();d["ANIO"]=_num(d.ANIO);d["MES"]=_num(d.MES)
    for c in COLS:d[c]=_num(d[c]).fillna(0)
    latest=int(d.loc[d.MES.eq(12),"ANIO"].max())
    # El tabulado es mensual. La cifra anual del referente se reproduce sumando
    # los doce meses, no tomando sólo diciembre ni convirtiendo columnas de forma desigual.
    g=d.loc[d.ANIO.between(2015,latest)].groupby("ANIO")[COLS].sum().sort_index()
    for pct,c in (("pct_2g","TRAF_TB_2G_E"),("pct_3g","TRAF_TB_3G_E"),("pct_4g","TRAF_TB_4G_E")):g[pct]=np.where(g.TOTAL_TB_E>0,g[c]/g.TOTAL_TB_E*100,0)
    out=g.reset_index().rename(columns={"ANIO":"anio"});out["anio"]=out.anio.astype(int);return out,{"anio":latest}
# ---------------------------------------------------------------------------
# Etiquetas tipo "chip" (mismo estilo que la Figura C.9): recuadro blanco con
# borde y conector recto hacia la barra. Los conectores son siempre horizontales;
# si un chip debe desplazarse en vertical para no encimarse con otro, el
# conector hace un quiebre a 90° (nunca una diagonal).
# ---------------------------------------------------------------------------
CHIP_LINE = "#A0A0B0"
CHIP_EDGE = "#D1D1DF"
CHIP_PAD = 0.28
CHIP_LW = 0.8


def _chip_text(value: float) -> str:
    if value < 0.1:
        text = f"{value:.2f}"
        return "<0.01%" if text == "0.00" else f"{text}%"
    return f"{value:.1f}%"


def _chip_color(color: str):
    """Color del texto: el de la serie; se oscurece si es muy claro para que se lea."""
    r, g, b = matplotlib.colors.to_rgb(color)
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    k = 1.0 if lum < 0.30 else 0.72
    return (r * k, g * k, b * k)


def _chip_spread(desired, gap, lo, hi):
    """Separa posiciones ascendentes al menos `gap`, con el menor desplazamiento total."""
    n = len(desired)
    if n == 0:
        return []
    shifted = [d - i * gap for i, d in enumerate(desired)]
    blocks = []
    for value in shifted:
        blocks.append([value, 1])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]:
            total, count = blocks.pop()
            blocks[-1][0] += total
            blocks[-1][1] += count
    fitted = []
    for total, count in blocks:
        fitted += [total / count] * count
    top = max(lo, hi - (n - 1) * gap)
    return [min(max(v, lo), top) + i * gap for i, v in enumerate(fitted)]


def draw_stacked_chips(ax, xs, segments_by_bar, bar_width, *, fontsize=6.4, line_pt=7.0):
    """Dibuja chips con conector para barras apiladas.

    xs: posición x de cada barra. segments_by_bar: por barra, lista de dicts con
    index (categoría), value, center y color. Llamar cuando xlim, ylim y la
    posición del eje ya son definitivos. Las categorías pares van a la izquierda
    de la barra y las impares a la derecha.
    """
    fig = ax.figure
    renderer = fig.canvas.get_renderer()
    pos = ax.get_position()
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    pt_x = pos.width * fig.get_figwidth() * 72 / (x1 - x0)   # puntos por unidad de x
    pt_y = pos.height * fig.get_figheight() * 72 / (y1 - y0)  # puntos por unidad de y
    text_kw = dict(fontsize=fontsize, fontweight="bold")
    pad_pt = CHIP_PAD * fontsize

    def measure(label):
        probe = ax.text(0, 0, label, **text_kw)
        extent = probe.get_window_extent(renderer)
        probe.remove()
        return extent.width * 72 / fig.dpi, extent.height * 72 / fig.dpi

    chip_h = measure("0.0%")[1] + 2 * pad_pt + CHIP_LW
    gap_y = (chip_h + 1.2) / pt_y
    lo = y0 + (chip_h / 2 + 1.0) / pt_y
    hi = y1 - (chip_h / 2 + 1.0) / pt_y

    # 1) Elementos por hueco entre barras (cada chip pertenece a un solo hueco).
    gaps = {}
    for bar_i, segments in enumerate(segments_by_bar):
        for seg in segments:
            side = "left" if seg["index"] % 2 == 0 else "right"
            label = _chip_text(seg["value"])
            item = {"bar": bar_i, "side": side, "c": seg["center"], "k": seg["index"],
                    "label": label, "color": seg["color"],
                    "w": measure(label)[0] + 2 * pad_pt + CHIP_LW}
            gaps.setdefault(bar_i - 1 if side == "left" else bar_i, []).append(item)

    # 2) Posición vertical de cada chip.
    for gap_i, items in gaps.items():
        rights = sorted((i for i in items if i["side"] == "right"), key=lambda i: (i["c"], i["k"]))
        lefts = sorted((i for i in items if i["side"] == "left"), key=lambda i: (i["c"], i["k"]))
        avail = (xs[gap_i + 1] - xs[gap_i] - bar_width) * pt_x if 0 <= gap_i < len(xs) - 1 else math.inf
        need = max([i["w"] for i in rights], default=0) + max([i["w"] for i in lefts], default=0) + 2 * line_pt
        groups = [rights, lefts] if (need <= avail or not rights or not lefts) else [sorted(items, key=lambda i: (i["c"], i["k"]))]
        for group in groups:
            for item, y in zip(group, _chip_spread([i["c"] for i in group], gap_y, lo, hi)):
                item["y"] = y

    # 3) Quiebres: los chips desplazados hacia arriba (o abajo) escalonan su quiebre
    #    para que los conectores no se crucen.
    tol = 0.6 / pt_y
    e_far, e_near = line_pt - 1.5, 1.5
    per_side = {}
    for items in gaps.values():
        for item in items:
            per_side.setdefault((item["bar"], item["side"]), []).append(item)
    for items in per_side.values():
        items.sort(key=lambda i: (i["c"], i["k"]))
        ups = [i for i in items if i["y"] - i["c"] > tol]
        downs = [i for i in items if i["c"] - i["y"] > tol]
        step = min(1.5, (e_far - e_near) / max(len(items) - 1, 1))
        for n, item in enumerate(ups):
            item["elbow"] = e_far - n * step
        for n, item in enumerate(downs):
            item["elbow"] = e_near + n * step

    # 4) Dibujo.
    for items in per_side.values():
        for item in items:
            sign = -1 if item["side"] == "left" else 1
            x_edge = xs[item["bar"]] + sign * bar_width / 2
            x_chip = x_edge + sign * (line_pt + pad_pt) / pt_x
            c, y = item["c"], item["y"]
            if "elbow" in item:
                x_elbow = x_edge + sign * item["elbow"] / pt_x
                path = ([x_edge, x_elbow, x_elbow, x_chip], [c, c, y, y])
            else:
                path = ([x_edge, x_chip], [c, c])
            ax.plot(*path, color=CHIP_LINE, lw=CHIP_LW, solid_capstyle="butt", zorder=5, clip_on=False)
            ax.text(x_chip, y, item["label"], ha="right" if sign < 0 else "left", va="center",
                    color=_chip_color(item["color"]), zorder=6, clip_on=False,
                    bbox=dict(boxstyle=f"round,pad={CHIP_PAD},rounding_size=.6", fc="white",
                              ec=CHIP_EDGE, lw=CHIP_LW),
                    **text_kw)


def _plot(d,m,out):
<<<<<<< HEAD
    fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc="#F8F8FA",transform=fig.transFigure,zorder=-1));fig.add_artist(patches.Rectangle((.045,.891),.009,.018,transform=fig.transFigure,fc="#4a7d75",ec="none",zorder=20));fig.text(.061,.9,"Figura C.14.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21);fig.text(.153,.9,f"Tráfico del servicio móvil de acceso a Internet (2015-{m['anio']})",fontsize=14,color=TEXT,va="center",zorder=21);ax=fig.add_axes([.07,.20,.86,.62]);bottom=np.zeros(len(d));colors=["#1e6284","#ed8945","#5844a0"];segments_by_year=[[] for _ in range(len(d))];width=.30
=======
    from anuario2026.ui_2024 import annotate_stacked_segments_outside
    fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc="#F8F8FA",transform=fig.transFigure,zorder=-1));fig.add_artist(patches.Rectangle((.045,.891),.009,.018,transform=fig.transFigure,fc="#4a7d75",ec="none",zorder=20));fig.text(.061,.9,"Figura C.14.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21);fig.text(.153,.9,f"Tráfico del servicio móvil de acceso a Internet (2015-{m['anio']})",fontsize=14,color=TEXT,va="center",zorder=21);ax=fig.add_axes([.07,.20,.86,.62]);bottom=np.zeros(len(d));colors=["#1e6284","#ed8945","#5844a0"];segments_by_year=[[] for _ in range(len(d))];width=.34
>>>>>>> 93f2bf9f8ee9510be3d7cd1817e28eb1b7e51fc4
    for category_index,(col,label,c) in enumerate(zip(["pct_2g","pct_3g","pct_4g"],["Tráfico 2G","Tráfico 3G","Tráfico 4G"],colors)):
        bars=ax.bar(d.anio,d[col],bottom=bottom,width=width,color=c,edgecolor="white",linewidth=.5,label=label,zorder=3)
        for year_index,(b,v,base) in enumerate(zip(bars,d[col],bottom)):
            if v>.005:segments_by_year[year_index].append({"index":category_index,"value":float(v),"center":float(base+v/2),"color":c})
        bottom+=d[col].to_numpy()
    for year,segments in zip(d.anio,segments_by_year):annotate_stacked_segments_outside(ax,float(year),segments,bar_width=width,x_offset=.18,min_gap=6.2,fontsize=5.8,decimals=1)
    for x,t in zip(d.anio,d.TOTAL_TB_E):ax.text(x,102,f"{t:,.0f}",ha="center",fontweight="bold",fontsize=8,color=TEXT)
<<<<<<< HEAD
    ax.set_xlim(d.anio.min()-.8,d.anio.max()+.8);ax.set_ylim(-4,108);ax.set_xticks(d.anio);ax.set_yticks([]);ax.spines[:].set_visible(False);draw_stacked_chips(ax,[float(y) for y in d.anio],segments_by_year,width,fontsize=6.8,line_pt=8);ax.legend(ncol=3,loc="lower center",bbox_to_anchor=(.5,-.14),frameon=False);fig.text(.05,.07,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.07,f"CRT con datos de los operadores; acumulado a diciembre de cada año, hasta {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.05,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.05,"Los porcentajes se calculan respecto del tráfico total; el tráfico sin tecnología especificada no se representa.",fontsize=8,color=TEXT);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200);plt.close(fig)
=======
    ax.set_ylim(0,108);ax.set_xticks(d.anio);ax.set_yticks([]);ax.spines[:].set_visible(False);ax.legend(ncol=3,loc="lower center",bbox_to_anchor=(.5,-.14),frameon=False);fig.text(.05,.07,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.07,f"CRT con datos de los operadores; acumulado a diciembre de cada año, hasta {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.05,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.05,"Los porcentajes se calculan respecto del tráfico total; el tráfico sin tecnología especificada no se representa.",fontsize=8,color=TEXT);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200);plt.close(fig)
>>>>>>> 93f2bf9f8ee9510be3d7cd1817e28eb1b7e51fc4
def generate(context):
    print("  C.14 | Adquisición o reutilización de TODO.zip de BIT/CRT");src=context.acquire_source(SOURCE_ID);d,m=build_metrics(load_raw(src));period=f"{m['anio']}-12";context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.write_data_used(d)
    for r in d.itertuples(index=False):
        for tech in ("2g","3g","4g"):context.record_calculation(f"participacion_{tech}_{r.anio}",f"tráfico {tech.upper()} / TOTAL_TB_E * 100",{"anio":r.anio},getattr(r,f"pct_{tech}"),"%",1)
    last=d.iloc[-1];text=context.render_text("c_mobile.md.j2",{"resumen":f"En {m['anio']}, el tráfico móvil de Internet fue {last.TOTAL_TB_E:,.0f}; la red 4G representó {last.pct_4g:.1f}%."});print(d.to_string(index=False));_plot(d,m,context.expected_figure_path);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())