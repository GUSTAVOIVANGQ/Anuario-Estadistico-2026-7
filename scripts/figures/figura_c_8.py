"""Figura C.8: tráfico de salida del servicio móvil de telefonía."""
from __future__ import annotations
import sys,zipfile
from pathlib import Path,PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
FIGURE_ID="C.8";SOURCE_ID="crt_bit_todo_2025_q2";TABLE="TD_TRAF_HIST_TELMOVIL_ITE_VA.csv";TEXT="#3c3c3b";CREAM="#F8F8FA"
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        n=next((n for n in z.namelist() if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold()),None)
        if not n:raise ValueError(f"TODO.zip no contiene {TABLE}")
        with z.open(n) as f:return pd.read_csv(f,encoding="latin-1",low_memory=False)
def _num(s):return pd.to_numeric(s.astype("string").str.replace(",","",regex=False),errors="coerce")
def build_metrics(raw):
    d=raw.copy();d["ANIO"]=_num(d.ANIO);d["TRAF_SALIDA"]=_num(d.TRAF_SALIDA).fillna(0);latest=int(d.ANIO.max());d=d.loc[d.ANIO.between(1997,latest)].groupby("ANIO",as_index=False).TRAF_SALIDA.sum();d.TRAF_SALIDA/=1_000_000;d=d.rename(columns={"ANIO":"anio","TRAF_SALIDA":"trafico_millones_minutos"});d["anio"]=d.anio.astype(int);return d,{"anio":latest}
def _plot(d,m,out):
    fig=plt.figure(figsize=(16,9),facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc=CREAM,transform=fig.transFigure,zorder=-1))
    fig.add_artist(patches.Rectangle((.045,.891),.009,.018,transform=fig.transFigure,fc="#4a7d75",ec="none",zorder=20))
    fig.text(.061,.9,"Figura C.8.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21)
    fig.text(.145,.9,f"Tráfico de salida del servicio móvil de telefonía (1997-{m['anio']})",fontsize=14,color=TEXT,va="center",zorder=21)
    ax=fig.add_axes([.08,.20,.84,.62])
    line_color="#006157"
    ax.fill_between(d.anio,d.trafico_millones_minutos,color=line_color,alpha=.15)
    ax.plot(d.anio,d.trafico_millones_minutos,color=line_color,lw=2.5,marker="o",ms=5,label="Millones de minutos")
    for row in d.iloc[[0,-1]].itertuples(index=False):
        ax.annotate(f"{row.trafico_millones_minutos:,.0f}",(row.anio,row.trafico_millones_minutos),xytext=(0,10),textcoords="offset points",ha="center",fontweight="bold",fontsize=7,color=TEXT,bbox=dict(boxstyle="round,pad=.3,rounding_size=.8",fc="white",ec=line_color,lw=.8))
    ax.set_xticks(d.anio);ax.tick_params(axis="x",rotation=90,labelsize=7,colors=TEXT);ax.tick_params(axis="y",labelsize=8,colors=TEXT);ax.set_ylabel("Millones de minutos",fontsize=9,color=TEXT);ax.grid(axis="y",color="#d1d1d1");ax.spines[["top","right"]].set_visible(False);ax.legend(loc="lower center",bbox_to_anchor=(.5,-.20),frameon=False,fontsize=9,labelcolor=TEXT)
    fig.text(.05,.075,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.075,f"CRT con datos de los operadores de telecomunicaciones hasta {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.054,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.054,"Suma anual del tráfico de salida, en millones de minutos.",fontsize=8,color=TEXT)
    out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200);plt.close(fig)
def generate(context):
    print("  C.8 | Adquisición o reutilización de TODO.zip de BIT/CRT");src=context.acquire_source(SOURCE_ID);d,m=build_metrics(load_raw(src));period=str(m["anio"]);context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.write_data_used(d);[context.record_calculation(f"trafico_{r.anio}","suma anual TRAF_SALIDA / 1,000,000",{"anio":r.anio},r.trafico_millones_minutos,"millones de minutos",1) for r in d.itertuples(index=False)];last=d.iloc[-1];text=context.render_text("c_mobile.md.j2",{"resumen":f"En {m['anio']}, el tráfico móvil de salida fue {last.trafico_millones_minutos:,.1f} millones de minutos."});print(d.to_string(index=False));_plot(d,m,context.expected_figure_path);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
