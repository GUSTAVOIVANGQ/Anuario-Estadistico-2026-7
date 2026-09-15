"""Figura C.16: índice de concentración del mercado de Internet móvil."""
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
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
FIGURE_ID="C.16";SOURCE_ID="crt_bit_todo_2025_q2";TABLE="TD_IHH_INTMOVIL_ITE_VA.csv";TEXT="#4B4B83"
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        n=next((n for n in z.namelist() if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold()),None)
        if not n:raise ValueError(f"TODO.zip no contiene {TABLE}")
        with z.open(n) as f:return pd.read_csv(f,encoding="latin-1",low_memory=False)
def _num(s):return pd.to_numeric(s.astype("string").str.replace(",","",regex=False),errors="coerce")
def build_metrics(raw):
    d=raw.copy();column=next((c for c in d.columns if c.upper().startswith("IHH_")),None)
    if not column:raise ValueError("La tabla no contiene una columna IHH")
    d["ANIO"]=_num(d.ANIO);d["MES"]=_num(d.MES);d["ihh"]=_num(d[column]);latest=int(d.loc[d.MES.eq(12),"ANIO"].max());out=d.loc[d.MES.eq(12)&d.ANIO.between(2013,latest),["ANIO","ihh"]].dropna().sort_values("ANIO").drop_duplicates("ANIO",keep="last").rename(columns={"ANIO":"anio"});out.anio=out.anio.astype(int);return out.reset_index(drop=True),{"anio":latest,"columna":column}
def _plot(d,m,out):
    fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc="#FBFBF7",transform=fig.transFigure,zorder=-1));fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#F58F82",ec="none"));fig.text(.061,.9,"Figura C.16.",fontsize=14,fontweight="bold",color=TEXT,va="center");fig.text(.153,.9,f"Herfindahl-Hirschman (IHH). Concentración del mercado de Internet móvil (2013-{m['anio']})",fontsize=14,color=TEXT,va="center");ax=fig.add_axes([.16,.17,.75,.66]);ordered=d.sort_values("anio",ascending=False);bars=ax.barh(np.arange(len(ordered)),ordered.ihh,color="#317DA3",height=.58)
    ax.set_yticks(np.arange(len(ordered)),ordered.anio.astype(str),fontsize=9,fontweight="bold");ax.set_xticks([]);ax.set_xlim(0,ordered.ihh.max()*1.15);ax.spines[:].set_visible(False)
    for bar,value in zip(bars,ordered.ihh):ax.text(value+ordered.ihh.max()*.012,bar.get_y()+bar.get_height()/2,f"{value:,.0f}",va="center",fontsize=9,fontweight="bold",color=TEXT)
    fig.text(.05,.07,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.07,f"CRT con datos de los operadores de telecomunicaciones a diciembre de cada año, hasta {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.05,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.05,"IHH estimado con respecto al número de líneas del servicio móvil de acceso a Internet.",fontsize=8,color=TEXT);out.parent.mkdir(parents=True,exist_ok=True);apply_reference_ui(fig, FIGURE_ID); fig.savefig(out,dpi=200);plt.close(fig)
def generate(context):
    print("  C.16 | Adquisición o reutilización de TODO.zip de BIT/CRT");src=context.acquire_source(SOURCE_ID);d,m=build_metrics(load_raw(src));period=f"{m['anio']}-12";context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.write_data_used(d)
    for r in d.itertuples(index=False):context.record_calculation(f"ihh_internet_movil_{r.anio}",f"{m['columna']} publicado por BIT",{"anio":r.anio},r.ihh,"puntos IHH",0)
    first=d.iloc[0];last=d.iloc[-1];text=context.render_text("c_mobile.md.j2",{"resumen":f"El IHH del mercado de Internet móvil pasó de {first.ihh:,.0f} puntos en {first.anio:.0f} a {last.ihh:,.0f} en {last.anio:.0f}."});print(d.to_string(index=False));_plot(d,m,context.expected_figure_path);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
