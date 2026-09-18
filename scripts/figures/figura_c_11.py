"""Figura C.11: líneas del servicio móvil de acceso a Internet."""
from __future__ import annotations
import sys,zipfile
from pathlib import Path,PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
FIGURE_ID="C.11";SOURCE_ID="crt_bit_todo_2025_q2";TABLE="TD_LINEAS_HIST_INTMOVIL_ITE_VA.csv";TEXT="#3c3c3b";COLS=["L_PREPAGO_E","L_POSPAGO_E","L_POSPAGOC_E","L_POSPAGOL_E","L_NO_ESPECIFICADO_E","L_TOTAL_E"]
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        n=next((n for n in z.namelist() if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold()),None)
        if not n:raise ValueError(f"TODO.zip no contiene {TABLE}")
        with z.open(n) as f:return pd.read_csv(f,encoding="latin-1",low_memory=False)
def _num(s):return pd.to_numeric(s.astype("string").str.replace(",","",regex=False),errors="coerce")
def build_metrics(raw):
    d=raw.copy();d["ANIO"]=_num(d.ANIO);d["MES"]=_num(d.MES)
    for c in COLS:d[c]=_num(d[c]).fillna(0)
    latest=int(d.loc[d.MES.eq(12),"ANIO"].max());d=d.loc[d.MES.eq(12)&d.ANIO.between(2010,latest)].groupby("ANIO",as_index=False)[COLS].sum().sort_values("ANIO");d[COLS]/=1_000_000;d=d.rename(columns={"ANIO":"anio"});d["anio"]=d.anio.astype(int);return d,{"anio":latest}
def _plot(d,m,out):
    fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc="#F8F8FA",transform=fig.transFigure,zorder=-1));fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#4a7d75",ec="none"),zorder=20);fig.text(.061,.9,"Figura C.11.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21);fig.text(.153,.9,f"Líneas del servicio móvil de acceso a Internet (2010-{m['anio']}) [millones]",fontsize=14,color=TEXT,va="center",zorder=21)
    ax=fig.add_axes([.07,.20,.86,.62]);series=[d.L_PREPAGO_E,d.L_POSPAGO_E,d.L_POSPAGOC_E,d.L_POSPAGOL_E,d.L_NO_ESPECIFICADO_E];ax.stackplot(d.anio,*series,colors=["#86adae","#64a0a1","#5c9596","#4c7d7e","#3b6667"],labels=["Prepago","Pospago","Pospago controlado","Pospago libre","Sin especificar"]);ax.plot(d.anio,d.L_TOTAL_E,color="#132b2d",lw=2,marker="o",label="Total")
    for r in d.itertuples(index=False):
        ax.annotate(f"{r.L_TOTAL_E:.1f}",(r.anio,r.L_TOTAL_E),xytext=(0,6),textcoords="offset points",ha="center",fontsize=7,fontweight="bold",color=TEXT,bbox=dict(boxstyle="round,pad=.3,rounding_size=.8",fc="white",ec="#132b2d",lw=.8))
    ax.set_xticks(d.anio);ax.tick_params(colors=TEXT);ax.grid(axis="y",color="#E5E5E5");ax.spines[["top","right"]].set_visible(False);ax.legend(ncol=6,loc="lower center",bbox_to_anchor=(.5,-.18),frameon=False,fontsize=8);fig.text(.05,.07,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.07,f"CRT con datos de los operadores a diciembre de cada año, hasta {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.05,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.05,"Cifras en millones de líneas.",fontsize=8,color=TEXT);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200,facecolor="white");plt.close(fig)
def generate(context):
    print("  C.11 | Adquisición o reutilización de TODO.zip de BIT/CRT");src=context.acquire_source(SOURCE_ID);d,m=build_metrics(load_raw(src));period=f"{m['anio']}-12";context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.write_data_used(d);[context.record_calculation(f"lineas_internet_{r.anio}","suma L_TOTAL_E / 1,000,000",{"anio":r.anio},r.L_TOTAL_E,"millones",1) for r in d.itertuples(index=False)];text=context.render_text("c_mobile.md.j2",{"resumen":f"En diciembre de {m['anio']} se registraron {d.iloc[-1].L_TOTAL_E:,.1f} millones de líneas móviles de acceso a Internet."});print(d.to_string(index=False));_plot(d,m,context.expected_figure_path);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
