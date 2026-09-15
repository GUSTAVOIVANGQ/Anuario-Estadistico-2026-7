"""Figura C.2: distribución del espectro por operador y banda."""
from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui
import sys,unicodedata,re
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd
FIGURE_ID="C.2"; OP_SOURCE="crt_bit_espectro_banda_actual"; DIST_SOURCE="crt_bit_dist_espectro_actual"; TEXT="#4B4B83"; CREAM="#FBFBF7"
BANDS={"B_700_MHZ":"700 MHz","B_800_MHZ":"800 MHz","B_850_MHZ":"850 MHz","B_PCS":"1900 MHz","B_AWS":"AWS","B_2_5_GHZ":"2500 MHz","B_3_3_GHZ":"3300 MHz","B_3_5_GHZ":"3500 MHz"}; OPS=["TELCEL","AT&T","ALTÁN"]; COLORS={"TELCEL":"#317DA3","AT&T":"#ADDCDF","ALTÁN":"#4B4B83"}
def load_raw(path):
    try:return pd.read_csv(path,encoding="utf-8-sig")
    except UnicodeDecodeError:return pd.read_csv(path,encoding="latin-1")
MONTHS={"ene":1,"feb":2,"mar":3,"abr":4,"may":5,"jun":6,"jul":7,"ago":8,"sep":9,"oct":10,"nov":11,"dic":12}
def latest_period(raw):
    if "ESTADO" not in raw.columns: raise ValueError("La tabla de distribución no contiene ESTADO")
    periods=[]
    for value in raw["ESTADO"]:
        match=re.search(r"([A-Za-záéíóú]{3})[- /](\d{2,4})",str(value).lower())
        if match:
            year=int(match.group(2)); periods.append((year+2000 if year<100 else year,MONTHS.get(match.group(1)[:3],0)))
    if not periods: raise ValueError("No se pudo identificar la fecha de espectro")
    year,month=max(periods); return {"anio":year,"mes":month}
def _norm(v):return " ".join("".join(c for c in unicodedata.normalize("NFKD",str(v)) if not unicodedata.combining(c)).upper().split())
def _op(v):
    n=_norm(v)
    if "TELCEL" in n or "AMERICA MOVIL" in n:return "TELCEL"
    if n in ("ATT","AT&T") or "AT AND T" in n:return "AT&T"
    if "ALTAN" in n:return "ALTÁN"
    return str(v).strip()
def build_metrics(raw):
    missing=[c for c in ["OPERADOR",*BANDS] if c not in raw.columns]
    if missing:raise ValueError("Tabla por operador no contiene: "+", ".join(missing))
    d=raw.copy()
    for c in BANDS:d[c]=pd.to_numeric(d[c],errors="coerce").fillna(0)
    if d[list(BANDS)].max().max()>1.5:d[list(BANDS)]/=100
    d["operador"]=d["OPERADOR"].map(_op); unknown=d.loc[~d.operador.isin(OPS)]
    if not unknown.empty and unknown[list(BANDS)].sum().sum()>.005:raise ValueError("Operador material no contemplado")
    p=d.groupby("operador")[list(BANDS)].sum().reindex(OPS,fill_value=0)
    sums=p.sum(); bad=sums[(sums>0)&~sums.between(.98,1.02)]
    if not bad.empty:raise ValueError("Las participaciones por banda no suman aproximadamente 100%")
    rows=[]
    for op in OPS:
        for c,label in BANDS.items():rows.append({"operador":op,"banda":label,"participacion":float(p.loc[op,c]*100)})
    return pd.DataFrame(rows)
def _plot(d,m,out,root):
    for p in (root/"assets"/"fonts"/"Noto_Sans").glob("*.ttf"):fm.fontManager.addfont(p)
    plt.rcParams["font.family"]="Noto Sans"; fig=plt.figure(figsize=(16,8.5),facecolor="white"); fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc=CREAM,transform=fig.transFigure,zorder=-1)); fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#F58F82",ec="none"),zorder=20); fig.text(.061,.9,"Figura C.2.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21); fig.text(.143,.9,"Distribución del espectro radioeléctrico por operador y banda",fontsize=14,color=TEXT,va="center",zorder=21)
    ax=fig.add_axes([.07,.20,.86,.62]); labels=list(BANDS.values()); x=list(range(len(labels))); bottoms=[0.]*len(labels); clips=[]
    for i in x:
        cp=patches.FancyBboxPatch((i-.2,0),.4,100,boxstyle="round,pad=0,rounding_size=.2",transform=ax.transData,fc="none",ec="none");ax.add_patch(cp);clips.append(cp)
    for op in OPS:
        vals=[float(d.loc[(d.operador.eq(op))&(d.banda.eq(b)),"participacion"].iloc[0]) for b in labels]; bars=ax.bar(x,vals,.4,bottom=bottoms,color=COLORS[op],edgecolor="none",label=op)
        for i,(bar,v,base) in enumerate(zip(bars,vals,bottoms)):
            bar.set_clip_path(clips[i]);
            if v>=.5:ax.annotate(f"{v:.0f}%",xy=(i,base+v/2),xytext=(i+.34,base+v/2),ha="center",va="center",fontsize=9,fontweight="bold",color=TEXT,bbox=dict(boxstyle="round,pad=.3",fc="white",ec="none"),arrowprops=dict(arrowstyle="-",color=COLORS[op],lw=.8))
        bottoms=[a+b for a,b in zip(bottoms,vals)]
    ax.set_xlim(-.6,len(labels)-.35);ax.set_ylim(-5,103);ax.set_xticks(x,labels,fontsize=10,fontweight="bold",color=TEXT);ax.set_yticks([]);[s.set_visible(False) for s in ax.spines.values()];ax.legend(ncol=3,loc="lower center",bbox_to_anchor=(.5,-.17),frameon=False,fontsize=10,labelcolor=TEXT)
    months={1:"enero",2:"febrero",3:"marzo",4:"abril",5:"mayo",6:"junio",7:"julio",8:"agosto",9:"septiembre",10:"octubre",11:"noviembre",12:"diciembre"};fig.text(.045,.075,"Fuente:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.086,.075,f"CRT, distribución del espectro radioeléctrico a {months[m['mes']]} de {m['anio']}.",fontsize=8,color=TEXT);fig.text(.045,.054,"Nota:",fontsize=8,fontweight="bold",color=TEXT);fig.text(.077,.054,"Participación respecto del total asignado en cada banda.",fontsize=8,color=TEXT)
    out.parent.mkdir(parents=True,exist_ok=True);apply_reference_ui(fig, FIGURE_ID); fig.savefig(out,dpi=200,bbox_inches="tight",facecolor="white");plt.close(fig)
def generate(context):
    print("  C.2 | Adquisición o reutilización de los CSV directos actualizados de BIT/CRT");op=context.acquire_source(OP_SOURCE);dist=context.acquire_source(DIST_SOURCE);m=latest_period(load_raw(dist));d=build_metrics(load_raw(op));period=f"{m['anio']}-{m['mes']:02d}";context.record_source_period(OP_SOURCE,period,"ULTIMO_DISPONIBLE");context.record_source_period(DIST_SOURCE,period,"ULTIMO_DISPONIBLE");context.write_data_used(d)
    for r in d.itertuples(index=False):context.record_calculation(f"participacion_{r.operador}_{r.banda}","fracción BIT del operador en la banda * 100",{"periodo":period,"operador":r.operador,"banda":r.banda},r.participacion,"%",0)
    text=context.render_text("c_2.md.j2",{"anio":m["anio"],"mes":m["mes"]});print("  C.2 | Generación del PNG");_plot(d,m,context.expected_figure_path,context.project_root);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
