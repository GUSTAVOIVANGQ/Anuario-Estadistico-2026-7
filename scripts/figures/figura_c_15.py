"""Figura C.15: participación de mercado del Internet móvil."""
from __future__ import annotations
import sys,unicodedata,zipfile
from pathlib import Path,PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
FIGURE_ID="C.15";SOURCE_ID="crt_bit_todo_2025_q2";TABLE="TD_MARKET_SHARE_INTMOVIL_ITE_VA.csv";TEXT="#4B4B83"
ORDER=["América Móvil","AT&T","Grupo Walmart","Telefónica","Otros"];COLORS=["#F58F82","#4B4B83","#317DA3","#ADDCDF","#F2535A"]
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        n=next((n for n in z.namelist() if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold()),None)
        if not n:raise ValueError(f"TODO.zip no contiene {TABLE}")
        with z.open(n) as f:return pd.read_csv(f,encoding="latin-1",low_memory=False)
def _num(s):return pd.to_numeric(s.astype("string").str.replace("%","",regex=False).str.replace(",","",regex=False),errors="coerce")
def _norm(v):return " ".join("".join(c for c in unicodedata.normalize("NFKD",str(v)) if not unicodedata.combining(c)).upper().split())
def _group(r):
    name=_norm(r.get("GRUPO",""));code=str(r.get("K_GRUPO","")).upper()
    if "AMERICA MOVIL" in name or code=="G006":return "América Móvil"
    if name=="AT&T" or code=="G007":return "AT&T"
    if "WALMART" in name or code=="C804":return "Grupo Walmart"
    if "TELEFONICA" in name or code=="G003":return "Telefónica"
    return "Otros"
def build_metrics(raw):
    d=raw.copy();d["ANIO"]=_num(d.ANIO);d["MES"]=_num(d.MES);d["valor"]=_num(d.MARKET_SHARE).fillna(0);latest=int(d.loc[d.MES.eq(12),"ANIO"].max());d=d.loc[d.MES.eq(12)&d.ANIO.between(2013,latest)].copy();d["grupo"]=d.apply(_group,axis=1);p=d.groupby(["ANIO","grupo"]).valor.sum().unstack(fill_value=0).reindex(columns=ORDER,fill_value=0).reset_index().rename(columns={"ANIO":"anio"});p.anio=p.anio.astype(int);return p,{"anio":latest}
def _plot(d,m,out):
    fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc="#FBFBF7",transform=fig.transFigure,zorder=-1));fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#F58F82",ec="none"));fig.text(.061,.9,"Figura C.15.",fontsize=14,fontweight="bold",color=TEXT,va="center");fig.text(.153,.9,f"Participación de mercado del servicio móvil de acceso a Internet (2013-{m['anio']})",fontsize=14,color=TEXT,va="center");ax=fig.add_axes([.06,.20,.88,.62]);bottom=np.zeros(len(d))
    for group,color in zip(ORDER,COLORS):
        values=d[group].to_numpy(float);bars=ax.bar(d.anio,values,bottom=bottom,width=.48,color=color,label=group)
        for bar,value,base in zip(bars,values,bottom):
            if value>=2:ax.text(bar.get_x()+bar.get_width()/2,base+value/2,f"{value:.1f}%",ha="center",va="center",fontsize=7,fontweight="bold",color="white" if color in ("#4B4B83","#317DA3","#F2535A") else TEXT)
        bottom+=values
    ax.set_ylim(0,102);ax.set_xticks(d.anio);ax.set_yticks([]);ax.tick_params(colors=TEXT);ax.spines[:].set_visible(False);ax.legend(ncol=5,loc="lower center",bbox_to_anchor=(.5,-.15),frameon=False);fig.text(.05,.07,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.07,f"CRT con datos de los operadores de telecomunicaciones a diciembre de cada año, hasta {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.05,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.05,"La suma puede no ser 100% por redondeo.",fontsize=8,color=TEXT);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200);plt.close(fig)
def generate(context):
    print("  C.15 | Adquisición o reutilización de TODO.zip de BIT/CRT");src=context.acquire_source(SOURCE_ID);d,m=build_metrics(load_raw(src));period=f"{m['anio']}-12";context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.write_data_used(d)
    for _,r in d.iterrows():
        for group in ORDER:context.record_calculation(f"participacion_{int(r.anio)}_{group}","suma de MARKET_SHARE del grupo",{"anio":int(r.anio),"grupo":group},float(r[group]),"%",1)
    last=d.iloc[-1];leader=max(ORDER,key=lambda g:last[g]);text=context.render_text("c_mobile.md.j2",{"resumen":f"En diciembre de {m['anio']}, {leader} encabezó el mercado de Internet móvil con {last[leader]:.1f}%."});print(d.to_string(index=False));_plot(d,m,context.expected_figure_path);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
