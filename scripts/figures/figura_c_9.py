"""Figura C.9: participación de mercado del servicio móvil de telefonía."""
from __future__ import annotations
import sys,zipfile,unicodedata
from pathlib import Path,PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
FIGURE_ID="C.9";SOURCE_ID="crt_bit_todo_2025_q2";TABLE="TD_MARKET_SHARE_TELMOVIL_ITE_VA.csv";TEXT="#4B4B83";ORDER=["América Móvil","Telefónica","AT&T","Otros"];COLORS=["#317DA3","#ADDCDF","#4B4B83","#F58F82"]
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
    fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc="#FBFBF7",transform=fig.transFigure,zorder=-1));fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#F58F82",ec="none"),zorder=20);fig.text(.061,.9,"Figura C.9.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21);fig.text(.145,.9,f"Participación de mercado del servicio móvil de telefonía (2013-{m['anio']})",fontsize=14,color=TEXT,va="center",zorder=21);ax=fig.add_axes([.06,.20,.88,.62]);bottom=pd.Series(0.,index=d.index)
    for g,c in zip(ORDER,COLORS):
        bars=ax.bar(d.anio,d[g],bottom=bottom,width=.55,color=c,label=g)
        for b,v,base in zip(bars,d[g],bottom):
            if v>=3:ax.text(b.get_x()+b.get_width()/2,base+v/2,f"{v:.1f}%",ha="center",va="center",fontsize=7,fontweight="bold",color="white" if c in ("#317DA3","#4B4B83") else TEXT)
        bottom+=d[g]
    ax.set_ylim(0,103);ax.set_xticks(d.anio);ax.tick_params(colors=TEXT);ax.set_yticks([]);ax.spines[:].set_visible(False);ax.legend(ncol=4,loc="lower center",bbox_to_anchor=(.5,-.16),frameon=False);fig.text(.05,.07,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.07,f"CRT con datos de los operadores de telecomunicaciones a diciembre de cada año, hasta {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.05,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.05,"La suma puede no ser 100% por redondeo.",fontsize=8,color=TEXT);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200);plt.close(fig)
def generate(context):
    print("  C.9 | Adquisición o reutilización de TODO.zip de BIT/CRT");src=context.acquire_source(SOURCE_ID);d,m=build_metrics(load_raw(src));period=f"{m['anio']}-12";context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.write_data_used(d);last=d.iloc[-1]
    for _,r in d.iterrows():
        for g in ORDER:context.record_calculation(f"participacion_{int(r.anio)}_{g}","suma de MARKET_SHARE del grupo",{"anio":int(r.anio),"grupo":g},float(r[g]),"%",1)
    lead=max(ORDER,key=lambda g:last[g]);text=context.render_text("c_mobile.md.j2",{"resumen":f"En diciembre de {m['anio']}, {lead} encabezó el mercado móvil con {last[lead]:.1f}%."});print(d.to_string(index=False));_plot(d,m,context.expected_figure_path);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
