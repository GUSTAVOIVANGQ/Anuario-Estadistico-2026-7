"""Figura C.6: teledensidad nacional del servicio móvil de telefonía."""
from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui
import sys,zipfile
from pathlib import Path,PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
FIGURE_ID="C.6";SOURCE_ID="crt_bit_todo_2025_q2";TABLE="TD_TELEDENSIDAD_H_TMOVIL_ITE_VA.csv";TEXT="#4B4B83";CREAM="#FBFBF7"
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        n=next((n for n in z.namelist() if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold()),None)
        if not n:raise ValueError(f"TODO.zip no contiene {TABLE}")
        with z.open(n) as f:return pd.read_csv(f,encoding="latin-1",low_memory=False)
def _num(s):return pd.to_numeric(s.astype("string").str.replace(",","",regex=False),errors="coerce")
def build_metrics(raw):
    d=raw.copy();d["ANIO"]=_num(d.ANIO);d["MES"]=_num(d.MES);d["T_H_TELMOVIL_E"]=_num(d.T_H_TELMOVIL_E);latest=int(d.loc[d.MES.eq(12),"ANIO"].max());d=d.loc[d.MES.eq(12)&d.ANIO.between(1990,latest),["ANIO","T_H_TELMOVIL_E"]].dropna().drop_duplicates("ANIO",keep="last").rename(columns={"ANIO":"anio","T_H_TELMOVIL_E":"teledensidad"});d["anio"]=d.anio.astype(int);return d,{"anio":latest}
def _plot(d,m,out):
    fig=plt.figure(figsize=(16,9),facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc=CREAM,transform=fig.transFigure,zorder=-1))
    fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#F58F82",ec="none"),zorder=20)
    fig.text(.061,.9,"Figura C.6.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21)
    fig.text(.145,.9,"Teledensidad del servicio móvil de telefonía",fontsize=14,color=TEXT,va="center",zorder=21)
    ax=fig.add_axes([.10,.20,.80,.60]);ax.plot(d.anio,d.teledensidad,color="#317DA3",lw=2.5,marker="o",ms=7);ax.fill_between(d.anio,d.teledensidad,color="#ADDCDF",alpha=.35)
    for r in d.itertuples(index=False):
        ax.annotate(f"{r.teledensidad:.0f}",(r.anio,r.teledensidad),xytext=(0,8),textcoords="offset points",ha="center",fontsize=7,fontweight="bold",color=TEXT,bbox=dict(boxstyle="round,pad=.2",fc="white",ec="none"))
    ax.set_xticks(d.anio);ax.tick_params(axis="x",rotation=90,labelsize=7,colors=TEXT);ax.set_ylim(0,max(d.teledensidad.max()*1.25,10));ax.grid(axis="y",color="#E5E5E5");ax.spines[["top","right"]].set_visible(False)
    fig.text(.05,.075,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.075,f"CRT con datos de los operadores de telecomunicaciones a diciembre de cada año, hasta {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.054,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.054,"Líneas por cada 100 habitantes.",fontsize=8,color=TEXT)
    out.parent.mkdir(parents=True,exist_ok=True);apply_reference_ui(fig, FIGURE_ID); fig.savefig(out,dpi=200,facecolor="white");plt.close(fig)
def generate(context):
    print("  C.6 | Adquisición o reutilización de TODO.zip de BIT/CRT");src=context.acquire_source(SOURCE_ID);d,m=build_metrics(load_raw(src));period=f"{m['anio']}-12";context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.write_data_used(d);[context.record_calculation(f"teledensidad_{r.anio}","T_H_TELMOVIL_E nacional publicado por BIT",{"anio":r.anio},r.teledensidad,"líneas por cada 100 habitantes",0) for r in d.itertuples(index=False)];text=context.render_text("c_mobile.md.j2",{"resumen":f"La teledensidad móvil publicada para {m['anio']} fue {d.iloc[-1].teledensidad:.0f} líneas por cada 100 habitantes."});print(d.to_string(index=False));_plot(d,m,context.expected_figure_path);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
