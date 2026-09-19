"""Figura C.13: teledensidad de Internet móvil por entidad federativa."""
from __future__ import annotations

<<<<<<< HEAD
import json, math, sys, unicodedata, zipfile
=======
import json, sys, unicodedata, zipfile
>>>>>>> 93f2bf9f8ee9510be3d7cd1817e28eb1b7e51fc4
from pathlib import Path, PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PatchCollection

FIGURE_ID="C.13"; SOURCE_ID="crt_bit_todo_2025_q2"; MAP_SOURCE_ID="mexico_geojson_legacy"
STATE_TABLE="TD_TELEDENSIDAD_INTMOVIL_ITE_VA.csv"; NATIONAL_TABLE="TD_TELEDENSIDAD_H_IMOVIL_ITE_VA.csv"
TEXT="#3c3c3b"; COLORS=["#afafaf","#737f7c","#63918b","#2d4f4b","#012f2a"]

def _member(z, table):
    found=[n for n in z.namelist() if PurePosixPath(n.replace("\\","/")).name.casefold()==table.casefold()]
    if len(found)!=1: raise ValueError(f"Se esperaba una tabla {table} y se encontraron {len(found)}")
    return found[0]
def load_tables(path):
    with zipfile.ZipFile(path) as z:
        with z.open(_member(z,STATE_TABLE)) as f: states=pd.read_csv(f,encoding="latin-1",low_memory=False)
        with z.open(_member(z,NATIONAL_TABLE)) as f: national=pd.read_csv(f,encoding="latin-1",low_memory=False)
    return states,national
def _num(s): return pd.to_numeric(s.astype("string").str.replace(",","",regex=False),errors="coerce")
def build_metrics(states,national):
    for c in ("ANIO","MES","K_ENTIDAD","T_INTMOVIL_ITE_VA"): states[c]=_num(states[c])
    for c in ("ANIO","MES","T_H_INTMOVIL_E"): national[c]=_num(national[c])
    latest=int(states.loc[states.MES.eq(12),"ANIO"].max())
    d=states.loc[states.ANIO.eq(latest)&states.MES.eq(12)&states.K_ENTIDAD.between(1,32),["K_ENTIDAD","ENTIDAD","T_INTMOVIL_ITE_VA"]].rename(columns={"T_INTMOVIL_ITE_VA":"valor"}).sort_values("K_ENTIDAD")
    if len(d)!=32: raise ValueError(f"C.13 requiere 32 entidades y encontró {len(d)}")
    d.K_ENTIDAD=d.K_ENTIDAD.astype(int)
    n=national.loc[national.MES.eq(12)&national.ANIO.le(latest)].sort_values("ANIO").dropna(subset=["T_H_INTMOVIL_E"])
    current=float(n.iloc[-1].T_H_INTMOVIL_E); year=int(n.iloc[-1].ANIO); previous=float(n.iloc[-2].T_H_INTMOVIL_E) if len(n)>1 else np.nan
    growth=(current/previous-1)*100 if previous else np.nan
    return d.reset_index(drop=True),{"anio":year,"nacional":current,"crecimiento":growth}
def _norm(v): return " ".join("".join(c for c in unicodedata.normalize("NFKD",str(v)) if not unicodedata.combining(c)).casefold().replace(".","").split())
def _shapes(path,values,bounds):
    lookup={_norm(k):(k,v) for k,v in values.items()}; aliases={"coahuila":"coahuila de zaragoza","michoacan":"michoacan de ocampo","veracruz":"veracruz de ignacio de la llave","distrito federal":"ciudad de mexico","estado de mexico":"mexico"}; shapes=[];colors=[];found=set()
    for f in json.loads(path.read_text(encoding="utf-8")).get("features",[]):
        key=_norm(f.get("properties",{}).get("name",""));key=aliases.get(key,key)
        if key not in lookup: continue
        original,value=lookup[key];found.add(original);idx=min(4,int(np.searchsorted(bounds[1:-1],value,side="right")));g=f.get("geometry",{});polys=[g.get("coordinates",[])] if g.get("type")=="Polygon" else g.get("coordinates",[])
        for p in polys:
            if p:shapes.append(patches.Polygon(np.asarray(p[0],dtype=float),closed=True));colors.append(COLORS[idx])
    if len(found)!=32:raise ValueError(f"No se empataron las 32 entidades: {sorted(set(values)-found)}")
    return shapes,colors
<<<<<<< HEAD
def _plot(d: pd.DataFrame, m: dict, map_path: Path, out: Path) -> None:
    values = dict(zip(d["ENTIDAD"], d["valor"]))
    bounds = np.unique(np.quantile(d["valor"], [0, .2, .4, .6, .8, 1]))
    if len(bounds) != 6:
        bounds = np.linspace(float(d.valor.min()), float(d.valor.max()) + .01, 6)
    shape_list, facecolors = _shapes(map_path, values, bounds)

    fig, ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")
    ax.add_collection(PatchCollection(shape_list, facecolor=facecolors, edgecolor="white", linewidth=.5))
    ax.set_xlim(-120.5, -79.0)
    ax.set_ylim(13.5, 34.0)
    ax.set_aspect(1 / np.cos(np.deg2rad(23.5)))

    bx, by, bw, bh = 0.735, 0.56, 0.215, 0.275
    bubble_face, bubble_edge = "#f7f7f7", "#c0c0c0"
    fig.add_artist(patches.FancyBboxPatch(
        (bx, by), bw, bh, boxstyle="round,pad=0.015,rounding_size=0.015",
        linewidth=1.0, edgecolor=bubble_edge, facecolor=bubble_face,
        transform=fig.transFigure, zorder=6, clip_on=False,
    ))
    fig.text(
        bx + bw / 2, by + bh * 0.80, "Líneas por cada\n100 habitantes:",
        transform=fig.transFigure, fontsize=9.5, color=TEXT,
        ha="center", va="center", zorder=7, multialignment="center", clip_on=False,
    )
    fig.text(
        bx + bw / 2, by + bh * 0.37, f"{m['nacional']:.0f}",
        transform=fig.transFigure, fontsize=60, fontweight="bold", color=TEXT,
        ha="center", va="center", zorder=7, clip_on=False,
    )
    line_y = by + bh * 0.60
    fig.add_artist(plt.Line2D(
        [bx + 0.02, bx + bw - 0.02], [line_y, line_y], transform=fig.transFigure,
        color="#d0d0d0", linewidth=0.8, zorder=7, clip_on=False,
    ))

    growth = float(m["crecimiento"])
    if not math.isnan(growth):
        tx, ty, tw, th = 0.28, 0.155, 0.225, 0.095
        fig.add_artist(patches.FancyBboxPatch(
            (tx, ty), tw, th, boxstyle="round,pad=0.012,rounding_size=0.012",
            linewidth=0, facecolor="#2d4f4b", transform=fig.transFigure, zorder=6, clip_on=False,
        ))
        fig.add_artist(patches.FancyBboxPatch(
            (tx + 0.008, ty + 0.012), 0.038, th - 0.024,
            boxstyle="round,pad=0.005,rounding_size=0.008", linewidth=0, facecolor="#012f2a",
            transform=fig.transFigure, zorder=7, clip_on=False,
        ))
        icon_cx, icon_cy = tx + 0.027, ty + th / 2
        icon_hw, icon_hh = 0.010, 0.020
        xs = [icon_cx - icon_hw, icon_cx - icon_hw * 0.3, icon_cx + icon_hw * 0.3, icon_cx + icon_hw]
        ys = [icon_cy - icon_hh * 0.4, icon_cy + icon_hh * 0.1, icon_cy - icon_hh * 0.15, icon_cy + icon_hh * 0.55]
        fig.add_artist(plt.Line2D(xs, ys, transform=fig.transFigure, color="white", linewidth=2.0,
                                 solid_capstyle="round", solid_joinstyle="round", zorder=8, clip_on=False))
        fig.add_artist(plt.Line2D([icon_cx + icon_hw * 0.65, icon_cx + icon_hw],
                                 [icon_cy + icon_hh * 0.20, icon_cy + icon_hh * 0.55],
                                 transform=fig.transFigure, color="white", linewidth=2.0,
                                 solid_capstyle="round", zorder=8, clip_on=False))
        text_cx = tx + 0.008 + 0.038 + (tw - 0.008 - 0.038) / 2 + 0.008
        fig.text(text_cx, ty + th * 0.65, "Tasa de crecimiento", transform=fig.transFigure,
                 fontsize=9.5, fontweight="bold", color="white", ha="center", va="center", zorder=7)
        fig.text(text_cx, ty + th * 0.28, f"anual de {growth:.1f}%", transform=fig.transFigure,
                 fontsize=9.5, fontweight="bold", color="white", ha="center", va="center", zorder=7)

    fig.text(0.08, 0.94, " ", bbox=dict(boxstyle="round,pad=1.6,rounding_size=0.2",
             facecolor="#4a7d75", edgecolor="none"), va="center", fontsize=2)
    fig.text(0.093, 0.94, "Figura C.13.", fontsize=14, fontweight="bold", color=TEXT, va="center")
    fig.text(0.180, 0.94, f"Líneas del servicio móvil de acceso a Internet por cada 100 habitantes ({m['anio']})",
             fontsize=14, fontweight="medium", color=TEXT, va="center")

    labels = [f"{bounds[i]:.0f} a {bounds[i+1]:.0f}" for i in range(5)]
    handles = [patches.Patch(facecolor=color, edgecolor="none", label=label) for color, label in zip(COLORS, labels)]
    legend = ax.legend(
        handles=handles, title="Líneas por cada 100 habitantes:",
        loc="lower left", bbox_to_anchor=(0.08, 0.12), bbox_transform=fig.transFigure,
        prop={"weight": "normal", "size": 10}, title_fontproperties={"weight": "bold", "size": 10},
        facecolor="white", labelcolor=TEXT, edgecolor="none", framealpha=0.0,
        handletextpad=0.5, labelspacing=0.3, handlelength=1.2, borderpad=0.0, borderaxespad=0.0,
    )
    legend._legend_box.align = "left"
    legend.get_title().set_multialignment("left")
    legend.get_title().set_color(TEXT)

    fig.text(0.08, 0.07, "Fuente:", fontsize=8, fontweight="bold", color=TEXT, ha="left", va="center")
    fig.text(0.11, 0.07, f"CRT con datos de los operadores de telecomunicaciones a diciembre de {m['anio']}.",
             fontsize=8, color=TEXT, ha="left", va="center")
    fig.text(0.08, 0.045, "Nota:", fontsize=8, fontweight="bold", color=TEXT, ha="left", va="center")
    fig.text(0.105, 0.045, "El valor nacional proviene de la serie nacional de líneas por cada 100 habitantes publicada por el CRT.",
             fontsize=8, color=TEXT, ha="left", va="center")

    plt.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.15)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)


=======
def _plot(d,m,map_path,out):
    bounds=np.unique(np.quantile(d.valor,[0,.2,.4,.6,.8,1]));bounds=bounds if len(bounds)==6 else np.linspace(float(d.valor.min()),float(d.valor.max())+.01,6);shapes,colors=_shapes(map_path,dict(zip(d.ENTIDAD,d.valor)),bounds)
    fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc="#F8F8FA",transform=fig.transFigure,zorder=-1));fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#4a7d75",ec="none"));fig.text(.061,.9,"Figura C.13.",fontsize=14,fontweight="bold",color=TEXT,va="center");fig.text(.153,.9,f"Líneas del servicio móvil de acceso a Internet por cada 100 habitantes ({m['anio']})",fontsize=14,color=TEXT,va="center")
    ax=fig.add_axes([.18,.18,.61,.65]);ax.add_collection(PatchCollection(shapes,facecolor=colors,edgecolor="white",linewidth=.7));ax.set_xlim(-119.5,-85);ax.set_ylim(14,33.5);ax.set_aspect(1/np.cos(np.deg2rad(23.5)));ax.axis("off")
    labels=[f"{bounds[i]:.0f} a {bounds[i+1]:.0f}" for i in range(5)];handles=[patches.Patch(facecolor=c,label=l) for c,l in zip(COLORS,labels)];leg=fig.legend(handles=handles,title="Líneas por cada 100 habitantes:",loc="lower left",bbox_to_anchor=(.06,.18),frameon=False,fontsize=9,title_fontsize=9);leg._legend_box.align="left";leg.get_title().set_fontweight("bold");leg.get_title().set_color(TEXT)
    fig.add_artist(patches.FancyBboxPatch((.76,.54),.18,.22,transform=fig.transFigure,boxstyle="round,pad=.015,rounding_size=.02",fc="white",ec="#E4E4E8"));fig.text(.85,.69,"Líneas por cada\n100 habitantes:",ha="center",fontsize=10,color=TEXT);fig.text(.85,.585,f"{m['nacional']:.0f}",ha="center",fontsize=43,fontweight="bold",color=TEXT);fig.text(.51,.18,f"Tasa de crecimiento\nanual de {m['crecimiento']:.1f}%",ha="center",va="center",fontsize=10,fontweight="bold",color="white",bbox=dict(boxstyle="round,pad=.8",fc=TEXT,ec="none"));fig.text(.05,.07,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.07,f"CRT con datos de los operadores de telecomunicaciones a diciembre de {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.05,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.05,"El valor nacional proviene de la serie nacional de líneas por cada 100 habitantes publicada por el CRT.",fontsize=8,color=TEXT);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200);plt.close(fig)
>>>>>>> 93f2bf9f8ee9510be3d7cd1817e28eb1b7e51fc4
def generate(context):
    print("  C.13 | Adquisición o reutilización de TODO.zip y mapa estatal");source=context.acquire_source(SOURCE_ID);map_path=context.acquire_source(MAP_SOURCE_ID);states,national=load_tables(source);d,m=build_metrics(states,national);period=f"{m['anio']}-12";context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.record_source_period(MAP_SOURCE_ID,"geometría estatal","REFERENCIA");context.write_data_used(d)
    for r in d.itertuples(index=False):context.record_calculation(f"teledensidad_internet_{r.K_ENTIDAD:02d}","T_INTMOVIL_ITE_VA publicado por BIT",{"anio":m['anio'],"entidad":r.ENTIDAD},r.valor,"líneas por cada 100 habitantes",0)
    context.record_calculation("teledensidad_internet_nacional","T_H_INTMOVIL_E publicado por BIT",{"anio":m['anio']},m['nacional'],"líneas por cada 100 habitantes",0);high=d.loc[d.valor.idxmax()];low=d.loc[d.valor.idxmin()];text=context.render_text("c_mobile.md.j2",{"resumen":f"En {m['anio']}, {high.ENTIDAD} registró el valor estatal más alto ({high.valor:.0f}) y {low.ENTIDAD} el menor ({low.valor:.0f})."});print(d.to_string(index=False));_plot(d,m,map_path,context.expected_figure_path);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
