"""Figura B.25: índice Herfindahl-Hirschman de televisión restringida."""
from __future__ import annotations
import sys,zipfile
from pathlib import Path,PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd
FIGURE_ID="B.25"; SOURCE_ID="crt_bit_todo_2025_q2"; TABLE="TD_IHH_TVRES_ITE_VA.csv"; TEXT="#3c3c3b"; TEAL="#335a5c"; CREAM="#F8F8FA"
def _member(z):
    for n in z.namelist():
        if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold(): return n
    raise ValueError(f"TODO.zip no contiene {TABLE}")
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        with z.open(_member(z)) as f: return pd.read_csv(f,encoding="latin-1",low_memory=False)
def _num(s): return pd.to_numeric(s.astype("string").str.replace(",","",regex=False),errors="coerce")
def build_metrics(raw):
    d=raw.copy()
    for c in ("ANIO","MES","IHH_TVRES_E"): d[c]=_num(d[c])
    latest=int(d.loc[d["MES"].eq(12)&d["ANIO"].ge(2015),"ANIO"].max()); d=d.loc[d["MES"].eq(12)&d["ANIO"].between(2015,latest),["ANIO","IHH_TVRES_E"]].dropna().sort_values("ANIO")
    if d.groupby("ANIO").size().max()>1: raise ValueError("Más de un IHH para un mismo diciembre")
    return d.rename(columns={"ANIO":"anio","IHH_TVRES_E":"ihh"}).astype({"anio":int}),{"anio":latest}
def _plot(d,m,out,root):
    for p in (root/"assets"/"fonts"/"Noto_Sans").glob("*.ttf"): fm.fontManager.addfont(p)
    plt.rcParams["font.family"]="Noto Sans"; fig=plt.figure(figsize=(16,8.5),facecolor="white"); fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc=CREAM,transform=fig.transFigure,zorder=-1))
    fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#4a7d75",ec="none"),zorder=20); fig.text(.061,.9,"Figura B.25.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21); fig.text(.151,.9,f"Índice de concentración del Servicio de Televisión Restringida (2015-{m['anio']})",fontsize=14,color=TEXT,va="center",zorder=21)
    ax=fig.add_axes([.10,.17,.82,.67]); ymax=len(d); xmax=d["ihh"].max()*1.16
    positions=range(ymax); bars=ax.barh(positions,d["ihh"],height=.55,color=TEAL,edgecolor="none",zorder=2)
    for bar,row in zip(bars,d.itertuples(index=False)):
        ax.text(row.ihh+xmax*.012,bar.get_y()+bar.get_height()/2,f"{row.ihh:,.0f}",va="center",fontsize=11,color=TEXT)
    ax.set_xlim(0,xmax); ax.set_ylim(-.7,ymax-.3); ax.invert_yaxis(); ax.set_yticks(range(ymax),d["anio"].astype(str),fontsize=11,fontweight="bold",color=TEXT); ax.set_xticks([]); [s.set_visible(False) for s in ax.spines.values()]
    fig.text(.045,.078,"Fuente:",fontsize=8,fontweight="bold",color=TEXT); fig.text(.086,.078,f"CRT con datos de los operadores de telecomunicaciones a diciembre de {m['anio']}.",fontsize=8,color=TEXT); fig.text(.045,.057,"Nota:",fontsize=8,fontweight="bold",color=TEXT); fig.text(.077,.057,"El índice se calcula con las participaciones de mercado del servicio.",fontsize=8,color=TEXT)
    out.parent.mkdir(parents=True,exist_ok=True); fig.savefig(out,dpi=200,bbox_inches="tight",facecolor="white"); plt.close(fig)
def generate(context):
    print("  B.25 | Adquisición o reutilización de TODO.zip de BIT/CRT"); src=context.acquire_source(SOURCE_ID); print("  B.25 | Lectura y validación de la serie IHH"); d,m=build_metrics(load_raw(src)); period=f"{m['anio']}-12"; context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE"); context.write_data_used(d)
    for r in d.itertuples(index=False): context.record_calculation(f"ihh_{r.anio}","IHH_TVRES_E publicado por BIT",{"anio":r.anio,"mes":12},r.ihh,"puntos IHH",0)
    text=context.render_text("b_25.md.j2",{"anio":m["anio"],"ihh":float(d.iloc[-1]["ihh"]),"anio_inicial":int(d.iloc[0]["anio"]),"ihh_inicial":float(d.iloc[0]["ihh"])}); print("  B.25 | Generación del PNG"); _plot(d,m,context.expected_figure_path,context.project_root); return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline; run_pipeline(root,only=FIGURE_ID); return 0
if __name__=="__main__": raise SystemExit(main())
