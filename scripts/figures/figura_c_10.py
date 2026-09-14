"""Figura C.10: IHH del servicio móvil de telefonía."""
from __future__ import annotations
import sys,zipfile
from pathlib import Path,PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
FIGURE_ID="C.10";SOURCE_ID="crt_bit_todo_2025_q2";TABLE="TD_IHH_TELMOVIL_ITE_VA.csv";TEXT="#4B4B83"
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        n=next((n for n in z.namelist() if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold()),None)
        if not n:raise ValueError(f"TODO.zip no contiene {TABLE}")
        with z.open(n) as f:return pd.read_csv(f,encoding="latin-1")
def _num(s):return pd.to_numeric(s.astype("string").str.replace(",","",regex=False),errors="coerce")
def build_metrics(raw):
    d=raw.copy();d["ANIO"]=_num(d.ANIO);d["MES"]=_num(d.MES);d["ihh"]=_num(d.IHH_TELMOVIL_E);latest=int(d.loc[d.MES.eq(12),"ANIO"].max());d=d.loc[d.MES.eq(12)&d.ANIO.between(2013,latest)].groupby("ANIO",as_index=False).ihh.mean().rename(columns={"ANIO":"anio"});d["anio"]=d.anio.astype(int);return d,{"anio":latest}
def _plot(d,m,out):
    fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc="#FBFBF7",transform=fig.transFigure,zorder=-1));fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#F58F82",ec="none"),zorder=20);fig.text(.061,.9,"Figura C.10.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21);fig.text(.153,.9,f"Índice de concentración del servicio móvil de telefonía (2013-{m['anio']})",fontsize=14,color=TEXT,va="center",zorder=21)
    ax=fig.add_axes([.11,.17,.80,.68]);rev=d.iloc[::-1].reset_index(drop=True);bars=ax.barh(range(len(rev)),rev.ihh,color="#317DA3",height=.58);ax.set_yticks(range(len(rev)),rev.anio.astype(str),color=TEXT);ax.set_xticks([]);ax.spines[:].set_visible(False);xmax=rev.ihh.max()
    for b,v in zip(bars,rev.ihh):
        ax.text(v+xmax*.01,b.get_y()+b.get_height()/2,f"{v:,.0f}",va="center",fontweight="bold",color=TEXT)
    fig.text(.05,.07,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.07,f"CRT con datos de los operadores a diciembre de cada año, hasta {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.05,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.05,"IHH estimado respecto del número de líneas móviles.",fontsize=8,color=TEXT);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200,facecolor="white");plt.close(fig)
def generate(context):
    print("  C.10 | Adquisición o reutilización de TODO.zip de BIT/CRT");src=context.acquire_source(SOURCE_ID);d,m=build_metrics(load_raw(src));period=f"{m['anio']}-12";context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.write_data_used(d);[context.record_calculation(f"ihh_{r.anio}","IHH_TELMOVIL_E publicado por BIT",{"anio":r.anio},r.ihh,"puntos IHH",0) for r in d.itertuples(index=False)];text=context.render_text("c_mobile.md.j2",{"resumen":f"En diciembre de {m['anio']}, el IHH móvil fue de {d.iloc[-1].ihh:,.0f} puntos."});print(d.to_string(index=False));_plot(d,m,context.expected_figure_path);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
