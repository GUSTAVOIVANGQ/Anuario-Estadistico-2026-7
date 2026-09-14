"""Figura C.13: teledensidad de Internet móvil por entidad federativa."""
from __future__ import annotations

import json, sys, unicodedata, zipfile
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
TEXT="#4B4B83"; COLORS=["#ADDCDF","#6CBFC4","#317DA3","#F58F82","#F2535A"]

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
def _plot(d,m,map_path,out):
    bounds=np.unique(np.quantile(d.valor,[0,.2,.4,.6,.8,1]));bounds=bounds if len(bounds)==6 else np.linspace(float(d.valor.min()),float(d.valor.max())+.01,6);shapes,colors=_shapes(map_path,dict(zip(d.ENTIDAD,d.valor)),bounds)
    fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc="#FBFBF7",transform=fig.transFigure,zorder=-1));fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#F58F82",ec="none"));fig.text(.061,.9,"Figura C.13.",fontsize=14,fontweight="bold",color=TEXT,va="center");fig.text(.153,.9,f"Líneas del servicio móvil de acceso a Internet por cada 100 habitantes ({m['anio']})",fontsize=14,color=TEXT,va="center")
    ax=fig.add_axes([.18,.18,.61,.65]);ax.add_collection(PatchCollection(shapes,facecolor=colors,edgecolor="white",linewidth=.7));ax.set_xlim(-119.5,-85);ax.set_ylim(14,33.5);ax.set_aspect(1/np.cos(np.deg2rad(23.5)));ax.axis("off")
    labels=[f"{bounds[i]:.0f} a {bounds[i+1]:.0f}" for i in range(5)];handles=[patches.Patch(facecolor=c,label=l) for c,l in zip(COLORS,labels)];leg=fig.legend(handles=handles,title="Líneas por cada 100 habitantes:",loc="lower left",bbox_to_anchor=(.06,.18),frameon=False,fontsize=9,title_fontsize=9);leg._legend_box.align="left";leg.get_title().set_fontweight("bold");leg.get_title().set_color(TEXT)
    fig.add_artist(patches.FancyBboxPatch((.76,.54),.18,.22,transform=fig.transFigure,boxstyle="round,pad=.015,rounding_size=.02",fc="white",ec="#E4E4E8"));fig.text(.85,.69,"Líneas por cada\n100 habitantes:",ha="center",fontsize=10,color=TEXT);fig.text(.85,.585,f"{m['nacional']:.0f}",ha="center",fontsize=43,fontweight="bold",color=TEXT);fig.text(.51,.18,f"Tasa de crecimiento\nanual de {m['crecimiento']:.1f}%",ha="center",va="center",fontsize=10,fontweight="bold",color="white",bbox=dict(boxstyle="round,pad=.8",fc=TEXT,ec="none"));fig.text(.05,.07,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.07,f"CRT con datos de los operadores de telecomunicaciones a diciembre de {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.05,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.05,"El valor nacional proviene de la serie nacional de líneas por cada 100 habitantes publicada por el CRT.",fontsize=8,color=TEXT);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200);plt.close(fig)
def generate(context):
    print("  C.13 | Adquisición o reutilización de TODO.zip y mapa estatal");source=context.acquire_source(SOURCE_ID);map_path=context.acquire_source(MAP_SOURCE_ID);states,national=load_tables(source);d,m=build_metrics(states,national);period=f"{m['anio']}-12";context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.record_source_period(MAP_SOURCE_ID,"geometría estatal","REFERENCIA");context.write_data_used(d)
    for r in d.itertuples(index=False):context.record_calculation(f"teledensidad_internet_{r.K_ENTIDAD:02d}","T_INTMOVIL_ITE_VA publicado por BIT",{"anio":m['anio'],"entidad":r.ENTIDAD},r.valor,"líneas por cada 100 habitantes",0)
    context.record_calculation("teledensidad_internet_nacional","T_H_INTMOVIL_E publicado por BIT",{"anio":m['anio']},m['nacional'],"líneas por cada 100 habitantes",0);high=d.loc[d.valor.idxmax()];low=d.loc[d.valor.idxmin()];text=context.render_text("c_mobile.md.j2",{"resumen":f"En {m['anio']}, {high.ENTIDAD} registró el valor estatal más alto ({high.valor:.0f}) y {low.ENTIDAD} el menor ({low.valor:.0f})."});print(d.to_string(index=False));_plot(d,m,map_path,context.expected_figure_path);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
