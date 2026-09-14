"""Figura C.12: teledensidad nacional del servicio móvil de acceso a Internet."""
from __future__ import annotations
import sys,zipfile
from pathlib import Path,PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
FIGURE_ID="C.12";SOURCE_ID="crt_bit_todo_2025_q2";TABLE="TD_TELEDENSIDAD_H_IMOVIL_ITE_VA.csv";TEXT="#4B4B83"
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        n=next((n for n in z.namelist() if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold()),None)
        if not n:raise ValueError(f"TODO.zip no contiene {TABLE}")
        with z.open(n) as f:return pd.read_csv(f,encoding="latin-1")
def _num(s):return pd.to_numeric(s.astype("string").str.replace(",","",regex=False),errors="coerce")
def build_metrics(raw):
    d=raw.copy();d["ANIO"]=_num(d.ANIO);d["MES"]=_num(d.MES);d["valor"]=_num(d.T_H_INTMOVIL_E);latest=int(d.loc[d.MES.eq(12),"ANIO"].max());d=d.loc[d.MES.eq(12)&d.ANIO.between(2010,latest)].groupby("ANIO",as_index=False).valor.mean().rename(columns={"ANIO":"anio","valor":"teledensidad"});d["anio"]=d.anio.astype(int);return d,{"anio":latest}
def _plot(d,m,out):
    fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc="#FBFBF7",transform=fig.transFigure,zorder=-1));fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#F58F82",ec="none"),zorder=20);fig.text(.061,.9,"Figura C.12.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21);fig.text(.153,.9,f"Líneas del servicio móvil de acceso a Internet por cada 100 habitantes (2010-{m['anio']})",fontsize=14,color=TEXT,va="center",zorder=21);ax=fig.add_axes([.08,.20,.84,.62]);ax.fill_between(d.anio,d.teledensidad,color="#ADDCDF",alpha=.35);ax.plot(d.anio,d.teledensidad,color="#4B4B83",lw=1.5,marker="o",ms=4)
    for r in d.itertuples(index=False):
        ax.vlines(r.anio,0,r.teledensidad,color="#4B4B83",lw=.7);ax.annotate(f"{r.teledensidad:.0f}",(r.anio,r.teledensidad),xytext=(0,8),textcoords="offset points",ha="center",fontweight="bold",color=TEXT,bbox=dict(boxstyle="round,pad=.25",fc="white",ec="none"))
    ax.set_xticks(d.anio);ax.set_ylim(0,d.teledensidad.max()*1.18);ax.spines[:].set_visible(False);ax.set_yticks([]);fig.text(.05,.07,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.07,f"CRT con datos de los operadores de telecomunicaciones a diciembre de cada año, hasta {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.05,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.05,"Líneas por cada 100 habitantes.",fontsize=8,color=TEXT);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200,facecolor="white");plt.close(fig)
def generate(context):
    print("  C.12 | Adquisición o reutilización de TODO.zip de BIT/CRT");src=context.acquire_source(SOURCE_ID);d,m=build_metrics(load_raw(src));period=f"{m['anio']}-12";context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.write_data_used(d);[context.record_calculation(f"teledensidad_internet_{r.anio}","T_H_INTMOVIL_E publicado por BIT",{"anio":r.anio},r.teledensidad,"líneas por cada 100 habitantes",0) for r in d.itertuples(index=False)];text=context.render_text("c_mobile.md.j2",{"resumen":f"En diciembre de {m['anio']} había {d.iloc[-1].teledensidad:.0f} líneas móviles de acceso a Internet por cada 100 habitantes."});print(d.to_string(index=False));_plot(d,m,context.expected_figure_path);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
