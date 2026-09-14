"""Figura C.5: líneas del servicio móvil de telefonía."""
from __future__ import annotations
import sys,zipfile
from pathlib import Path,PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
FIGURE_ID="C.5"; SOURCE_ID="crt_bit_todo_2025_q2"; TABLE="TD_LINEAS_HIST_TELMOVIL_ITE_VA.csv"; TEXT="#4B4B83"; CREAM="#FBFBF7"
COLS=["L_PREPAGO_E","L_POSPAGO_E","L_POSPAGOC_E","L_POSPAGOL_E","L_NO_ESPECIFICADO_E","L_TOTAL_E"]
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        member=next((n for n in z.namelist() if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold()),None)
        if not member: raise ValueError(f"TODO.zip no contiene {TABLE}")
        with z.open(member) as f:return pd.read_csv(f,encoding="latin-1",low_memory=False)
def _num(s):return pd.to_numeric(s.astype("string").str.replace(",","",regex=False),errors="coerce")
def build_metrics(raw):
    d=raw.copy();d["ANIO"]=_num(d.ANIO);d["MES"]=_num(d.MES)
    for c in COLS:d[c]=_num(d[c]).fillna(0)
    latest=int(d.loc[d.MES.eq(12),"ANIO"].max());d=d.loc[d.MES.eq(12)&d.ANIO.between(1990,latest)].groupby("ANIO",as_index=False)[COLS].sum().sort_values("ANIO");d[COLS]=d[COLS]/1_000_000;d=d.rename(columns={"ANIO":"anio"});d["anio"]=d.anio.astype(int);return d,{"anio":latest}
def _frame(title,root):
    fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc=CREAM,transform=fig.transFigure,zorder=-1));fig.text(.045,.90," ",bbox=dict(boxstyle="round,pad=1.5",fc="#F58F82",ec="none"),zorder=20);fig.text(.061,.90,"Figura C.5.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21);fig.text(.145,.90,title,fontsize=14,color=TEXT,va="center",zorder=21);return fig
def _plot(d,m,out,root):
    fig=_frame(f"Líneas del servicio móvil de telefonía (1990-{m['anio']}) [millones]",root);ax=fig.add_axes([.07,.20,.86,.62]);x=d.anio
    series=[d.L_PREPAGO_E,d.L_POSPAGO_E,d.L_POSPAGOC_E,d.L_POSPAGOL_E,d.L_NO_ESPECIFICADO_E];labels=["Prepago","Pospago","Pospago controlado","Pospago libre","Sin segmento especificado"];colors=["#ADDCDF","#65BED8","#4BA7C9","#317DA3","#4B4B83"]
    ax.stackplot(x,*series,labels=labels,colors=colors,alpha=.96);ax.plot(x,d.L_TOTAL_E,color="#4B4B83",lw=2.2,marker="o",ms=3,label="Líneas totales")
    for r in d.itertuples(index=False):ax.annotate(f"{r.L_TOTAL_E:.1f}",(r.anio,r.L_TOTAL_E),xytext=(0,6),textcoords="offset points",ha="center",fontsize=6.5,fontweight="bold",color=TEXT)
    ax.set_xlim(d.anio.min()-.5,d.anio.max()+.5);ax.set_ylim(bottom=0);ax.set_xticks(d.anio);ax.tick_params(axis="x",rotation=90,labelsize=7,colors=TEXT);ax.tick_params(axis="y",labelsize=8,colors=TEXT);ax.grid(axis="y",color="#E5E5E5",lw=.7);ax.spines[["top","right"]].set_visible(False);ax.legend(ncol=6,loc="lower center",bbox_to_anchor=(.5,-.25),frameon=False,fontsize=8)
    fig.text(.045,.075,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.086,.075,f"CRT con datos de los operadores de telecomunicaciones a diciembre de cada año, hasta {m['anio']}.",fontsize=8,color=TEXT);fig.text(.045,.054,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.077,.054,"Cifras expresadas en millones de líneas.",fontsize=8,color=TEXT);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200,facecolor="white");plt.close(fig)
def generate(context):
    print("  C.5 | Adquisición o reutilización de TODO.zip de BIT/CRT");src=context.acquire_source(SOURCE_ID);print("  C.5 | Lectura y cálculo de líneas por segmento");d,m=build_metrics(load_raw(src));period=f"{m['anio']}-12";context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.write_data_used(d)
    for r in d.itertuples(index=False):context.record_calculation(f"lineas_totales_{r.anio}","suma L_TOTAL_E / 1,000,000",{"anio":r.anio},r.L_TOTAL_E,"millones",1)
    last=d.iloc[-1];text=context.render_text("c_mobile.md.j2",{"resumen":f"En diciembre de {m['anio']} se registraron {last.L_TOTAL_E:,.1f} millones de líneas móviles."});print(d.to_string(index=False));_plot(d,m,context.expected_figure_path,context.project_root);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
