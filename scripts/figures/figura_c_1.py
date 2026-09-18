"""Figura C.1: espectro asignado por banda con fuente directa BIT/CRT."""
from __future__ import annotations
import sys,re
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd
FIGURE_ID="C.1"; SOURCE_ID="crt_bit_dist_espectro_actual"; TEXT="#3c3c3b"; CREAM="#F8F8FA"
BANDS={"B_700_MHZ":"Banda de 700 MHz","B_800_MHZ":"Banda de 800 MHz","B_850_MHZ":"Banda de 850 MHz","B_PCS":"Banda PCS","B_AWS":"Banda AWS","B_2_5_GHZ":"Banda de 2500 MHz","B_3_3_GHZ":"Banda de 3300 MHz","B_3_5_GHZ":"Banda de 3500 MHz"}
COLORS=["#132b2d","#234244","#335a5c","#3b6667","#4c7d7e","#5c9596","#64a0a1","#86adae"]
MONTHS={"ene":1,"feb":2,"mar":3,"abr":4,"may":5,"jun":6,"jul":7,"ago":8,"sep":9,"oct":10,"nov":11,"dic":12}
def load_raw(path):
    try:return pd.read_csv(path,encoding="utf-8-sig")
    except UnicodeDecodeError:return pd.read_csv(path,encoding="latin-1")
def _period(v):
    m=re.search(r"([A-Za-záéíóú]{3})[- /](\d{2,4})",str(v).lower());
    if not m:return (0,0)
    y=int(m.group(2)); y=y+2000 if y<100 else y; return y,MONTHS.get(m.group(1)[:3],0)
def build_metrics(raw):
    missing=[c for c in ["ESTADO",*BANDS] if c not in raw.columns]
    if missing: raise ValueError("Tabla de espectro no contiene: "+", ".join(missing))
    d=raw.copy(); d[["anio","mes"]]=pd.DataFrame(d["ESTADO"].map(_period).tolist(),index=d.index); d=d.sort_values(["anio","mes"]); row=d.iloc[-1]
    if int(row["anio"])==0: raise ValueError("No se pudo identificar la fecha de espectro")
    items=[]
    for c,label in BANDS.items():
        v=float(pd.to_numeric(str(row[c]).replace(",",""),errors="coerce"));
        if v<0 or pd.isna(v): raise ValueError(f"Valor inválido en {c}")
        items.append({"banda":label,"mhz":v,"anio":int(row.anio),"mes":int(row.mes)})
    out=pd.DataFrame(items); return out,{"anio":int(row.anio),"mes":int(row.mes),"total":float(out.mhz.sum())}
def _layout(items,x,y,w,h):
    if len(items)==1:return [(items[0],x,y,w,h)]
    total=sum(v for _,v in items); acc=0; cut=1
    for i,(_,v) in enumerate(items[:-1],1):
        acc+=v
        if acc>=total/2: cut=i; break
    a,b=items[:cut],items[cut:]; sa=sum(v for _,v in a)
    if w>=h:
        wa=w*sa/total; return _layout(a,x,y,wa,h)+_layout(b,x+wa,y,w-wa,h)
    ha=h*sa/total; return _layout(a,x,y,w,ha)+_layout(b,x,y+ha,w,h-ha)
def _plot(d,m,out,root):
    for p in (root/"assets"/"fonts"/"Noto_Sans").glob("*.ttf"): fm.fontManager.addfont(p)
    plt.rcParams["font.family"]="Noto Sans"; fig=plt.figure(figsize=(16,8.5),facecolor="white"); fig.add_artist(patches.FancyBboxPatch((.025,.045),.95,.89,boxstyle="round,pad=.01,rounding_size=.018",lw=0,fc=CREAM,transform=fig.transFigure,zorder=-1)); fig.text(.045,.9," ",bbox=dict(boxstyle="round,pad=1.5",fc="#4a7d75",ec="none"),zorder=20); fig.text(.061,.9,"Figura C.1.",fontsize=14,fontweight="bold",color=TEXT,va="center",zorder=21); fig.text(.143,.9,"Espectro radioeléctrico asignado por banda de frecuencia",fontsize=14,color=TEXT,va="center",zorder=21)
    ax=fig.add_axes([.055,.15,.89,.68]); items=sorted([(r.banda,r.mhz) for r in d.itertuples(index=False)],key=lambda q:q[1],reverse=True)
    for i,(item,x,y,w,h) in enumerate(_layout(items,0,0,100,100)):
        label,val=item; ax.add_patch(patches.Rectangle((x,y),w,h,fc=COLORS[i%len(COLORS)],ec="white",lw=3)); fs=max(7,min(16,7+min(w,h)/3)); shown=label
        if w<9: shown=label.replace("Banda de ","Banda de\n").replace(" MHz"," MHz",1)
        ax.text(x+w/2,y+h/2,f"{shown}\n{val:,.0f} MHz",ha="center",va="center",fontsize=fs,fontweight="bold",color="white",wrap=True,clip_on=True)
    ax.set_xlim(0,100); ax.set_ylim(0,100); ax.axis("off"); fig.text(.055,.105,f"Total: {m['total']:,.0f} MHz",fontsize=15,fontweight="bold",color=TEXT)
    months={1:"enero",2:"febrero",3:"marzo",4:"abril",5:"mayo",6:"junio",7:"julio",8:"agosto",9:"septiembre",10:"octubre",11:"noviembre",12:"diciembre"}; fig.text(.045,.068,"Fuente:",fontsize=8,fontweight="bold",color=TEXT); fig.text(.086,.068,f"CRT, distribución de espectro radioeléctrico a {months[m['mes']]} de {m['anio']}.",fontsize=8,color=TEXT); fig.text(.045,.048,"Nota:",fontsize=8,fontweight="bold",color=TEXT); fig.text(.077,.048,"Las superficies son proporcionales a los MHz asignados.",fontsize=8,color=TEXT)
    out.parent.mkdir(parents=True,exist_ok=True); fig.savefig(out,dpi=200,bbox_inches="tight",facecolor="white"); plt.close(fig)
def generate(context):
    print("  C.1 | Adquisición o reutilización del CSV directo actualizado de BIT/CRT"); src=context.acquire_source(SOURCE_ID); print("  C.1 | Selección de la fecha más reciente y cálculo de MHz por banda"); d,m=build_metrics(load_raw(src)); period=f"{m['anio']}-{m['mes']:02d}"; context.record_source_period(SOURCE_ID,period,"ULTIMO_DISPONIBLE"); context.write_data_used(d)
    for r in d.itertuples(index=False): context.record_calculation("mhz_"+r.banda.lower().replace(" ","_"),"valor de MHz publicado por banda en la fila más reciente",{"periodo":period,"banda":r.banda},r.mhz,"MHz",0)
    leader=d.sort_values("mhz",ascending=False).iloc[0]; text=context.render_text("c_1.md.j2",{"anio":m["anio"],"mes":m["mes"],"total":m["total"],"banda_mayor":leader.banda,"mhz_mayor":leader.mhz}); print("  C.1 | Generación del PNG"); _plot(d,m,context.expected_figure_path,context.project_root); return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":period,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline; run_pipeline(root,only=FIGURE_ID); return 0
if __name__=="__main__": raise SystemExit(main())
