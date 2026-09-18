"""Figura B.24: participación de mercado de televisión restringida."""
from __future__ import annotations
import sys, unicodedata, zipfile
from pathlib import Path, PurePosixPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd

FIGURE_ID="B.24"; SOURCE_ID="crt_bit_todo_2025_q2"; TABLE="TD_MARKET_SHARE_TVRES_ITE_VA.csv"
TEXT="#3c3c3b"; CREAM="#F8F8FA"
ORDER=["Grupo Televisa","Megacable-MCM","Dish-MVS","Grupo Salinas","Stargroup","Otros"]
COLORS=dict(zip(ORDER,["#1e6284","#ed8945","#5844a0","#99b554","#8e244d","#728781"]))

def _fonts(root):
    for p in (root/"assets"/"fonts"/"Noto_Sans").glob("*.ttf"): fm.fontManager.addfont(p)
    plt.rcParams["font.family"]="Noto Sans"
def _member(z):
    for n in z.namelist():
        if PurePosixPath(n.replace("\\","/")).name.casefold()==TABLE.casefold(): return n
    raise ValueError(f"TODO.zip no contiene {TABLE}")
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        with z.open(_member(z)) as f: return pd.read_csv(f,encoding="latin-1",low_memory=False)
def _num(s): return pd.to_numeric(s.astype("string").str.replace(",","",regex=False).str.replace("%","",regex=False),errors="coerce")
def _norm(v): return " ".join("".join(c for c in unicodedata.normalize("NFKD",str(v)) if not unicodedata.combining(c)).upper().split())
def _group(v):
    n=_norm(v)
    for key,val in (("GRUPO TELEVISA","Grupo Televisa"),("CABLEVISION RED","Grupo Televisa"),("MEGACABLE","Megacable-MCM"),("DISH","Dish-MVS"),("GRUPO SALINAS","Grupo Salinas"),("TOTALPLAY","Grupo Salinas"),("STARGROUP","Stargroup"),("STAR GROUP","Stargroup")):
        if key in n: return val
    return "Otros"
def build_metrics(raw):
    d=raw.copy(); d["ANIO"]=_num(d["ANIO"]); d["MES"]=_num(d["MES"]); d["MARKET_SHARE"]=_num(d["MARKET_SHARE"])
    if d["MARKET_SHARE"].dropna().max()<=1.5: d["MARKET_SHARE"]*=100
    years=sorted(d.loc[d["MES"].eq(12),"ANIO"].dropna().astype(int).unique()); latest=max(y for y in years if y>=2014)
    d=d.loc[d["MES"].eq(12)&d["ANIO"].between(2014,latest)].copy(); d["grupo"]=d["GRUPO"].map(_group)
    p=d.groupby(["ANIO","grupo"])["MARKET_SHARE"].sum().unstack(fill_value=0).reindex(columns=ORDER,fill_value=0).sort_index()
    sums=p.sum(axis=1)
    if ((sums<95)|(sums>105)).any(): raise ValueError("La suma anual de participaciones BIT no es plausible")
    out=p.reset_index().rename(columns={"ANIO":"anio"}); out["anio"]=out["anio"].astype(int); return out,{"anio":latest}
def _plot(data,meta,out,root):
    from anuario2026.ui_2024 import annotate_stacked_segments_outside
    _fonts(root); fig=plt.figure(figsize=(16,8.5),facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc=CREAM,transform=fig.transFigure,zorder=-1))
    fig.add_artist(patches.Rectangle((.045,.891),.009,.018,transform=fig.transFigure,fc="#4a7d75",ec="none")); fig.text(.061,.9,"Figura B.24.",fontsize=14,fontweight="bold",color=TEXT,va="center")
    fig.text(.154,.9,f"Participación de mercado del Servicio de Televisión Restringida (2014-{meta['anio']})",fontsize=14,color=TEXT,va="center")
    ax=fig.add_axes([.065,.20,.87,.62]); x=range(len(data)); bottoms=pd.Series(0.,index=data.index); width=.34; segments_by_year=[[] for _ in range(len(data))]
    for category_index,g in enumerate(ORDER):
        bars=ax.bar(list(x),data[g],width,bottom=bottoms,color=COLORS[g],edgecolor="none",label=g,zorder=2)
        for year_index,(bar,val,base) in enumerate(zip(bars,data[g],bottoms)):
            if val>.005: segments_by_year[year_index].append({"index":category_index,"value":float(val),"center":float(base+val/2),"color":COLORS[g]})
        bottoms=bottoms+data[g]
    for year_index,segments in enumerate(segments_by_year): annotate_stacked_segments_outside(ax,year_index,segments,bar_width=width,x_offset=.17,min_gap=6.3,fontsize=5.4,decimals=1)
    ax.set_xlim(-.7,len(data)-.3); ax.set_ylim(-8,108); ax.set_xticks(list(x),data["anio"].astype(str),fontsize=9,fontweight="bold",color=TEXT); ax.set_yticks([]); [s.set_visible(False) for s in ax.spines.values()]
    ax.legend(ncol=6,loc="lower center",bbox_to_anchor=(.5,-.18),frameon=False,fontsize=8,labelcolor=TEXT,handlelength=1.5,columnspacing=1.5)
    fig.text(.045,.078,"Fuente:",fontsize=8,fontweight="bold",color=TEXT); fig.text(.086,.078,f"CRT con datos de los operadores de telecomunicaciones a diciembre de {meta['anio']}.",fontsize=8,color=TEXT)
    fig.text(.045,.057,"Nota:",fontsize=8,fontweight="bold",color=TEXT); fig.text(.077,.057,"La suma de los porcentajes puede no sumar 100% por cuestiones de redondeo.",fontsize=8,color=TEXT)
    out.parent.mkdir(parents=True,exist_ok=True); fig.savefig(out,dpi=200,bbox_inches="tight",facecolor="white"); plt.close(fig)
def generate(context):
    print("  B.24 | Adquisición o reutilización de TODO.zip de BIT/CRT"); source=context.acquire_source(SOURCE_ID)
    print("  B.24 | Lectura y agregación de participación por grupo"); data,meta=build_metrics(load_raw(source)); period=f"{meta['anio']}-12"; context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE"); context.write_data_used(data)
    for _, row in data.iterrows():
        for g in ORDER: context.record_calculation(f"participacion_{int(row['anio'])}_{g}","suma de MARKET_SHARE de los operadores del grupo",{"anio":int(row["anio"]),"grupo":g},float(row[g]),"%",1)
    last=data.iloc[-1]; leader=max(ORDER,key=lambda g:last[g]); text=context.render_text("b_24.md.j2",{"anio":meta["anio"],"lider":leader,"participacion_lider":last[leader]})
    print("  B.24 | Generación del PNG"); _plot(data,meta,context.expected_figure_path,context.project_root); return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(data)}
def main():
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline; run_pipeline(root,only=FIGURE_ID); return 0
if __name__=="__main__": raise SystemExit(main())
