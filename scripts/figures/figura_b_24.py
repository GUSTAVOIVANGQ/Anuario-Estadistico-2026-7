"""Figura B.24: participación de mercado de televisión restringida."""
from __future__ import annotations
<<<<<<< HEAD
import math, sys, unicodedata, zipfile
=======
import sys, unicodedata, zipfile
>>>>>>> 93f2bf9f8ee9510be3d7cd1817e28eb1b7e51fc4
from pathlib import Path, PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd

FIGURE_ID="B.24"; SOURCE_ID="crt_bit_todo_2025_q2"; TABLE="TD_MARKET_SHARE_TVRES_ITE_VA.csv"
TEXT="#3c3c3b"; CREAM="#F8F8FA"
ORDER=["Grupo Televisa","Megacable-MCM","Dish-MVS","Grupo Salinas","Stargroup","Otros"]
COLORS=dict(zip(ORDER,["#1e6284","#ed8945","#5844a0","#99b554","#8e244d","#728781"]))

def _fonts(root):
    for p in (root/"assets"/"fonts"/"Noto_Sans").glob("*.ttf"): fm.fontManager.addfont(p)
    plt.rcParams["font.family"]="Noto Sans"
def _member(z):
    for n in z.namelist():
        if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold(): return n
    raise ValueError(f"TODO.zip no contiene {TABLE}")
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        with z.open(_member(z)) as f: return pd.read_csv(f,encoding="latin-1",low_memory=False)
def _num(s): return pd.to_numeric(s.astype("string").str.replace(",","",regex=False).str.replace("%","",regex=False),errors="coerce")
def _norm(v): return " ".join("".join(c for c in unicodedata.normalize("NFKD",str(v)) if not unicodedata.combining(c)).upper().split())
def _group(v):
    n=_norm(v)
    for key,val in (("GRUPO TELEVISA","Grupo Televisa"),("CABLEVISION RED","Grupo Televisa"),("MEGACABLE","Megacable-MCM"),("DISH","Dish-MVS"),("GRUPO SALINAS","Grupo Salinas"),("TOTALPLAY","Grupo Salinas"),("STARGROUP","Stargroup"),("STAR GROUP","Stargroup")):
        if key in n: return val
    return "Otros"
def build_metrics(raw):
    d=raw.copy(); d["ANIO"]=_num(d["ANIO"]); d["MES"]=_num(d["MES"]); d["MARKET_SHARE"]=_num(d["MARKET_SHARE"])
    if d["MARKET_SHARE"].dropna().max()<=1.5: d["MARKET_SHARE"]*=100
    years=sorted(d.loc[d["MES"].eq(12),"ANIO"].dropna().astype(int).unique()); latest=max(y for y in years if y>=2014)
    d=d.loc[d["MES"].eq(12)&d["ANIO"].between(2014,latest)].copy(); d["grupo"]=d["GRUPO"].map(_group)
    p=d.groupby(["ANIO","grupo"])["MARKET_SHARE"].sum().unstack(fill_value=0).reindex(columns=ORDER,fill_value=0).sort_index()
    sums=p.sum(axis=1)
    if ((sums<95)|(sums>105)).any(): raise ValueError("La suma anual de participaciones BIT no es plausible")
    out=p.reset_index().rename(columns={"ANIO":"anio"}); out["anio"]=out["anio"].astype(int); return out,{"anio":latest}
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


def _plot(data,meta,out,root):
    from anuario2026.ui_2024 import annotate_stacked_segments_outside
    _fonts(root); fig=plt.figure(figsize=(16,8.5),facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc=CREAM,transform=fig.transFigure,zorder=-1))
    fig.add_artist(patches.Rectangle((.045,.891),.009,.018,transform=fig.transFigure,fc="#4a7d75",ec="none")); fig.text(.061,.9,"Figura B.24.",fontsize=14,fontweight="bold",color=TEXT,va="center")
    fig.text(.154,.9,f"Participación de mercado del Servicio de Televisión Restringida (2014-{meta['anio']})",fontsize=14,color=TEXT,va="center")
<<<<<<< HEAD
    ax=fig.add_axes([.065,.20,.87,.62]); x=range(len(data)); bottoms=pd.Series(0.,index=data.index); width=.32; segments_by_year=[[] for _ in range(len(data))]
=======
    ax=fig.add_axes([.065,.20,.87,.62]); x=range(len(data)); bottoms=pd.Series(0.,index=data.index); width=.34; segments_by_year=[[] for _ in range(len(data))]
>>>>>>> 93f2bf9f8ee9510be3d7cd1817e28eb1b7e51fc4
    for category_index,g in enumerate(ORDER):
        bars=ax.bar(list(x),data[g],width,bottom=bottoms,color=COLORS[g],edgecolor="none",label=g,zorder=2)
        for year_index,(bar,val,base) in enumerate(zip(bars,data[g],bottoms)):
            if val>.005: segments_by_year[year_index].append({"index":category_index,"value":float(val),"center":float(base+val/2),"color":COLORS[g]})
        bottoms=bottoms+data[g]
<<<<<<< HEAD
    ax.set_xlim(-.7,len(data)-.3); ax.set_ylim(-8,108); ax.set_xticks(list(x),data["anio"].astype(str),fontsize=9,fontweight="bold",color=TEXT); ax.set_yticks([]); [s.set_visible(False) for s in ax.spines.values()]
    draw_stacked_chips(ax,list(x),segments_by_year,width,fontsize=6.4,line_pt=7.5)
=======
    for year_index,segments in enumerate(segments_by_year): annotate_stacked_segments_outside(ax,year_index,segments,bar_width=width,x_offset=.17,min_gap=6.3,fontsize=5.4,decimals=1)
    ax.set_xlim(-.7,len(data)-.3); ax.set_ylim(-8,108); ax.set_xticks(list(x),data["anio"].astype(str),fontsize=9,fontweight="bold",color=TEXT); ax.set_yticks([]); [s.set_visible(False) for s in ax.spines.values()]
>>>>>>> 93f2bf9f8ee9510be3d7cd1817e28eb1b7e51fc4
    ax.legend(ncol=6,loc="lower center",bbox_to_anchor=(.5,-.18),frameon=False,fontsize=8,labelcolor=TEXT,handlelength=1.5,columnspacing=1.5)
    fig.text(.045,.078,"Fuente:",fontsize=8,fontweight="bold",color=TEXT); fig.text(.086,.078,f"CRT con datos de los operadores de telecomunicaciones a diciembre de {meta['anio']}.",fontsize=8,color=TEXT)
    fig.text(.045,.057,"Nota:",fontsize=8,fontweight="bold",color=TEXT); fig.text(.077,.057,"La suma de los porcentajes puede no sumar 100% por cuestiones de redondeo.",fontsize=8,color=TEXT)
    out.parent.mkdir(parents=True,exist_ok=True); fig.savefig(out,dpi=200,bbox_inches="tight",facecolor="white"); plt.close(fig)
def generate(context):
    print("  B.24 | Adquisición o reutilización de TODO.zip de BIT/CRT"); source=context.acquire_source(SOURCE_ID)
    print("  B.24 | Lectura y agregación de participación por grupo"); data,meta=build_metrics(load_raw(source)); period=f"{meta['anio']}-12"; context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE"); context.write_data_used(data)
    for _, row in data.iterrows():
        for g in ORDER: context.record_calculation(f"participacion_{int(row['anio'])}_{g}","suma de MARKET_SHARE de los operadores del grupo",{"anio":int(row["anio"]),"grupo":g},float(row[g]),"%",1)
    last=data.iloc[-1]; leader=max(ORDER,key=lambda g:last[g]); text=context.render_text("b_24.md.j2",{"anio":meta["anio"],"lider":leader,"participacion_lider":last[leader]})
    print("  B.24 | Generación del PNG"); _plot(data,meta,context.expected_figure_path,context.project_root); return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(data)}
def main():
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline; run_pipeline(root,only=FIGURE_ID); return 0
if __name__=="__main__": raise SystemExit(main())