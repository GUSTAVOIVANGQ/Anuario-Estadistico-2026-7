"""Figura C.14: tráfico del servicio móvil de acceso a Internet por tecnología."""
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
import numpy as np
FIGURE_ID="C.14";SOURCE_ID="crt_bit_todo_2025_q2";TABLE="TD_TRAF_INTMOVIL_ITE_VA.csv";TEXT="#4B4B83";COLS=["TRAF_TB_2G_E","TRAF_TB_3G_E","TRAF_TB_4G_E","TRAF_TB_NO_ESPECIFICADO_E","TOTAL_TB_E"]
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        n=next((n for n in z.namelist() if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold()),None)
        if not n:raise ValueError(f"TODO.zip no contiene {TABLE}")
        with z.open(n) as f:return pd.read_csv(f,encoding="latin-1",low_memory=False)
def _num(s):return pd.to_numeric(s.astype("string").str.replace(",","",regex=False),errors="coerce")
def build_metrics(raw):
    d=raw.copy();d["ANIO"]=_num(d.ANIO);d["MES"]=_num(d.MES)
    for c in COLS:d[c]=_num(d[c]).fillna(0)
    latest=int(d.loc[d.MES.eq(12),"ANIO"].max())
    # El tabulado es mensual. La cifra anual del referente se reproduce sumando
    # los doce meses, no tomando sólo diciembre ni convirtiendo columnas de forma desigual.
    g=d.loc[d.ANIO.between(2015,latest)].groupby("ANIO")[COLS].sum().sort_index()
    for pct,c in (("pct_2g","TRAF_TB_2G_E"),("pct_3g","TRAF_TB_3G_E"),("pct_4g","TRAF_TB_4G_E")):g[pct]=np.where(g.TOTAL_TB_E>0,g[c]/g.TOTAL_TB_E*100,0)
    out=g.reset_index().rename(columns={"ANIO":"anio"});out["anio"]=out.anio.astype(int);return out,{"anio":latest}
def _plot(d,m,out):
    fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc="#FBFBF7",transform=fig.transFigure,zorder=-1));fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#F58F82",ec="none"),zorder=20);fig.text(.061,.9,"Figura C.14.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21);fig.text(.153,.9,f"Tráfico del servicio móvil de acceso a Internet (2015-{m['anio']})",fontsize=14,color=TEXT,va="center",zorder=21);ax=fig.add_axes([.07,.20,.86,.62]);bottom=np.zeros(len(d));colors=["#F2535A","#F58F82","#4B4B83"]
    for col,label,c in zip(["pct_2g","pct_3g","pct_4g"],["Tráfico 2G","Tráfico 3G","Tráfico 4G"],colors):
        bars=ax.bar(d.anio,d[col],bottom=bottom,width=.42,color=c,label=label)
        for b,v,base in zip(bars,d[col],bottom):
            if v>=.1:ax.text(b.get_x()+b.get_width()/2,base+v/2,f"{v:.1f}%",ha="center",va="center",fontsize=8,fontweight="bold",color="white" if c=="#4B4B83" else TEXT)
        bottom+=d[col].to_numpy()
    for x,t in zip(d.anio,d.TOTAL_TB_E):ax.text(x,102,f"{t:,.0f}",ha="center",fontweight="bold",fontsize=8,color=TEXT)
    ax.set_ylim(0,108);ax.set_xticks(d.anio);ax.set_yticks([]);ax.spines[:].set_visible(False);ax.legend(ncol=3,loc="lower center",bbox_to_anchor=(.5,-.14),frameon=False);fig.text(.05,.07,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.091,.07,f"CRT con datos de los operadores; acumulado a diciembre de cada año, hasta {m['anio']}.",fontsize=8,color=TEXT);fig.text(.05,.05,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.082,.05,"Los porcentajes se calculan respecto del tráfico total; el tráfico sin tecnología especificada no se representa.",fontsize=8,color=TEXT);out.parent.mkdir(parents=True,exist_ok=True);apply_reference_ui(fig, FIGURE_ID); fig.savefig(out,dpi=200);plt.close(fig)
def generate(context):
    print("  C.14 | Adquisición o reutilización de TODO.zip de BIT/CRT");src=context.acquire_source(SOURCE_ID);d,m=build_metrics(load_raw(src));period=f"{m['anio']}-12";context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE");context.write_data_used(d)
    for r in d.itertuples(index=False):
        for tech in ("2g","3g","4g"):context.record_calculation(f"participacion_{tech}_{r.anio}",f"tráfico {tech.upper()} / TOTAL_TB_E * 100",{"anio":r.anio},getattr(r,f"pct_{tech}"),"%",1)
    last=d.iloc[-1];text=context.render_text("c_mobile.md.j2",{"resumen":f"En {m['anio']}, el tráfico móvil de Internet fue {last.TOTAL_TB_E:,.0f}; la red 4G representó {last.pct_4g:.1f}%."});print(d.to_string(index=False));_plot(d,m,context.expected_figure_path);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
