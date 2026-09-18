"""Figura C.9: participación de mercado del servicio móvil de telefonía."""
from __future__ import annotations
import sys,zipfile,unicodedata
from pathlib import Path,PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
FIGURE_ID="C.9";SOURCE_ID="crt_bit_todo_2025_q2";TABLE="TD_MARKET_SHARE_TELMOVIL_ITE_VA.csv";TEXT="#3c3c3b";ORDER=["América Móvil","Telefónica","AT&T","Otros"];COLORS=["#1e6284","#368491","#667489","#728781"]
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        n=next((n for n in z.namelist() if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold()),None)
        if not n:raise ValueError(f"TODO.zip no contiene {TABLE}")
        with z.open(n) as f:return pd.read_csv(f,encoding="latin-1",low_memory=False)
def _num(s):return pd.to_numeric(s.astype("string").str.replace("%","",regex=False).str.replace(",","",regex=False),errors="coerce")
def _norm(v):return " ".join("".join(c for c in unicodedata.normalize("NFKD",str(v)) if not unicodedata.combining(c)).upper().split())
def _group(r):
    n=_norm(r.get("GRUPO",""));c=str(r.get("K_GRUPO","")).upper()
    if "AMERICA" in n or c=="G006":return "América Móvil"
    if "TELEFONICA" in n or c=="G003":return "Telefónica"
    if n in ("AT&T","IUSACELL-UNEFON","NEXTEL") or c=="G007":return "AT&T"
    return "Otros"
def build_metrics(raw):
    d=raw.copy();d["ANIO"]=_num(d.ANIO);d["MES"]=_num(d.MES);d["valor"]=_num(d.MARKET_SHARE).fillna(0);latest=int(d.loc[d.MES.eq(12),"ANIO"].max());d=d.loc[d.MES.eq(12)&d.ANIO.between(2013,latest)].copy();d["grupo"]=d.apply(_group,axis=1);p=d.groupby(["ANIO","grupo"]).valor.sum().unstack(fill_value=0).reindex(columns=ORDER,fill_value=0).reset_index().rename(columns={"ANIO":"anio"});p["anio"]=p.anio.astype(int);return p,{"anio":latest}
def _plot(d,m,out):
    fig=plt.figure(figsize=(16,9),facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc="#F8F8FA",transform=fig.transFigure,zorder=-1))
    fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#4a7d75",ec="none"),zorder=20);fig.text(.061,.9,"Figura C.9.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21);fig.text(.145,.9,f"Participación de mercado del servicio móvil de telefonía (2013-{m['anio']})",fontsize=14,color=TEXT,va="center",zorder=21)
    ax=fig.add_axes([.06,.20,.88,.62]);years=d.anio.to_numpy(float);width=.45;bottom=pd.Series(0.,index=d.index);segments=[[] for _ in range(len(d))]
    for group_index,(group,color) in enumerate(zip(ORDER,COLORS)):
        values=d[group].to_numpy(float);bars=ax.bar(years,values,bottom=bottom,width=width,color=color,edgecolor="white",linewidth=.5,label=group,zorder=3)
        for year_index,(value,base) in enumerate(zip(values,bottom)):segments[year_index].append((group_index,float(value),float(base),color))
        bottom+=values
    for year_index,year in enumerate(years):
        last_y=-10.
        for group_index,value,base,color in segments[year_index]:
            if value<.1:continue
            center=base+value/2;y_text=max(center,last_y+4.);last_y=y_text;x_text=year-width/2-.12;x_elbow=x_text+.02+group_index*.008;x_target=year-width/2
            ax.plot([x_text,x_elbow,x_elbow,x_target],[y_text,y_text,center,center],color="#A0A0B0",lw=1.0,zorder=3)
            ax.annotate(f"{value:.2f}%",(x_text,y_text),ha="right",va="center",fontsize=7,fontweight="bold",color=color,bbox=dict(boxstyle="round,pad=.3,rounding_size=.6",fc="white",ec="#D1D1DF",lw=1.0),zorder=4)
    ax.set_ylim(0,105);ax.set_xticks(years,d.anio.astype(str),fontsize=9,fontweight="bold",color=TEXT);ax.tick_params(colors=TEXT,length=0);ax.set_yticks([]);ax.spines[:].set_visible(False);ax.legend(ncol=4,loc="lower center",bbox_to_anchor=(.5,-.16),frameon=False)
    fig.text(.05,.07,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.07,f"CRT con datos de los operadores de telecomunicaciones a diciembre de cada año, hasta {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.05,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.05,"La suma puede no ser 100% por redondeo.",fontsize=8,color=TEXT);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200);plt.close(fig)
def generate(context):
    print("  C.9 | Adquisición o reutilización de TODO.zip de BIT/CRT");src=context.acquire_source(SOURCE_ID);d,m=build_metrics(load_raw(src));period=f"{m['anio']}-12";context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.write_data_used(d);last=d.iloc[-1]
    for _,r in d.iterrows():
        for g in ORDER:context.record_calculation(f"participacion_{int(r.anio)}_{g}","suma de MARKET_SHARE del grupo",{"anio":int(r.anio),"grupo":g},float(r[g]),"%",1)
    lead=max(ORDER,key=lambda g:last[g]);text=context.render_text("c_mobile.md.j2",{"resumen":f"En diciembre de {m['anio']}, {lead} encabezó el mercado móvil con {last[lead]:.1f}%."});print(d.to_string(index=False));_plot(d,m,context.expected_figure_path);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
