"""Figura F.4: distribución estatal de víctimas de ciberacoso por sexo."""
from __future__ import annotations
import sys, textwrap, zipfile
from io import BytesIO
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIGURE_ID="F.4"; CURRENT_SOURCE_ID="inegi_mociba_2025"; REFERENCE_SOURCE_ID="inegi_mociba_2024_reference"; PERIOD="2025"
LANDING_PAGE="https://www.inegi.org.mx/programas/mociba/2025/"
TEXT="#3c3c3b"; MEN="#335a5c"; WOMEN="#86adae"; BG="#F8F8FA"

def _fonts(root:Path)->None:
    d=root/"assets"/"fonts"/"Noto_Sans"
    for n in ("NotoSans-Regular.ttf","NotoSans-Medium.ttf","NotoSans-Bold.ttf"):
        if (d/n).is_file(): fm.fontManager.addfont(d/n)
    plt.rcParams["font.family"]="Noto Sans" if "Noto Sans" in {x.name for x in fm.fontManager.ttflist} else "DejaVu Sans"

def _csv(raw:bytes)->pd.DataFrame:
    last=None
    for enc in ("utf-8-sig","latin1","cp1252"):
        for sep in (",","|",";"):
            try:
                df=pd.read_csv(BytesIO(raw),encoding=enc,sep=sep,low_memory=False); df.columns=[str(c).strip().upper() for c in df.columns]
                if {"P4_01","FACTOR","CVE_ENT"}.issubset(df.columns): return df
            except Exception as exc: last=exc
    raise ValueError(f"No se pudo leer MOCIBA: {last}")

def load_microdata(path:Path)->tuple[pd.DataFrame,str]:
    if not zipfile.is_zipfile(path): raise ValueError(f"ZIP MOCIBA inválido: {path}")
    with zipfile.ZipFile(path) as z:
        for member in z.namelist():
            if member.lower().endswith(".csv"):
                try: df=_csv(z.read(member)); break
                except ValueError: continue
        else: raise ValueError("No se encontró CSV individual MOCIBA")
    required={"FACTOR","CVE_ENT","NOM_ENT","SEXO"}|{f"P4_{i:02d}" for i in range(1,14)}
    missing=sorted(required-set(df.columns))
    if missing: raise ValueError(f"Faltan variables MOCIBA: {missing}")
    print(f"  {FIGURE_ID} | {path.name}: {len(df):,} registros, {member}"); return df,member

def num(s:pd.Series)->pd.Series:return pd.to_numeric(s,errors="coerce")
def weights(df:pd.DataFrame)->pd.Series:return num(df["FACTOR"]).fillna(0)
def victims(df:pd.DataFrame)->pd.Series:return pd.concat([num(df[f"P4_{i:02d}"]).eq(1) for i in range(1,14)],axis=1).any(axis=1)
def sex(df:pd.DataFrame,label:str)->pd.Series:return num(df["SEXO"]).eq(1 if label=="Hombres" else 2)

def calculate(df:pd.DataFrame)->tuple[pd.DataFrame,dict[str,float]]:
    w=weights(df); victim=victims(df); parts=[]; totals={}
    for label in ("Hombres","Mujeres"):
        universe=victim&sex(df,label); totals[label]=float(w.loc[universe].sum())
        if totals[label]<=0: raise ValueError(f"Denominador no positivo para {label}")
        tmp=df.loc[universe,["CVE_ENT","NOM_ENT"]].copy(); tmp[label]=w.loc[universe]
        grouped=tmp.groupby(["CVE_ENT","NOM_ENT"],as_index=False)[label].sum(); grouped[label]=grouped[label]/totals[label]*100; parts.append(grouped)
    out=parts[0].merge(parts[1],on=["CVE_ENT","NOM_ENT"],validate="one_to_one").sort_values("NOM_ENT").reset_index(drop=True)
    if len(out)!=32 or any(abs(out[c].sum()-100)>1e-7 for c in ("Hombres","Mujeres")): raise ValueError("La distribución estatal por sexo no contiene 32 entidades o no suma 100%")
    return out,totals

def validate_reference(df:pd.DataFrame)->dict[str,float]:
    data,totals=calculate(df)
    if not 8_200_000<=totals["Hombres"]<=8_400_000 or not 10_500_000<=totals["Mujeres"]<=10_700_000: raise RuntimeError(f"MOCIBA 2024 no reproduce los totales oficiales por sexo: {totals}")
    return {"hombres":totals["Hombres"],"mujeres":totals["Mujeres"],"entidades":len(data)}

def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    _fonts(root); fig,ax=plt.subplots(figsize=(16,9)); fig.patch.set_facecolor("white"); ax.set_facecolor(BG)
    x=np.arange(len(data)); width=.34; bh=ax.bar(x-width/2,data["Hombres"],width,color=MEN,label="Hombres"); bw=ax.bar(x+width/2,data["Mujeres"],width,color=WOMEN,label="Mujeres")
    for bars in (bh,bw):
        for i,b in enumerate(bars): ax.text(b.get_x()+b.get_width()/2,b.get_height()+.22+(i%2)*.24,f"{b.get_height():.1f}%",ha="center",fontsize=5.5,fontweight="bold",color=TEXT,bbox=dict(boxstyle="round,pad=.18",fc="white",ec=b.get_facecolor(),lw=.6))
    labels=[str(v).title().replace(" De "," de ") for v in data.NOM_ENT]
    ax.set_xticks(x,labels,rotation=90,fontsize=6.1,color=TEXT); ax.set_ylim(0,max(data[["Hombres","Mujeres"]].max())*1.22); ax.set_yticks([]); ax.tick_params(axis="x",length=0,pad=7)
    for s in ax.spines.values(): s.set_visible(False)
    fig.legend(loc="upper center",bbox_to_anchor=(.5,.805),ncol=2,frameon=False,labelcolor=TEXT,fontsize=9)
    fig.add_artist(patches.FancyBboxPatch((.035,.09),.93,.83,transform=fig.transFigure,boxstyle="round,pad=.006,rounding_size=.018",fc=BG,ec="none",zorder=-1)); fig.add_artist(patches.FancyBboxPatch((.052,.864),.008,.018,transform=fig.transFigure,boxstyle="round,pad=0,rounding_size=.003",fc="#4a7d75",ec="none"))
    fig.text(.066,.873,"Figura F.4.",fontsize=14,fontweight="bold",color=TEXT,va="center"); fig.text(.151,.873,"Porcentaje de la población de 12 años y más que vivió ciberacoso por entidad federativa y sexo",fontsize=14,color=TEXT,va="center")
    fig.text(.052,.125,"Fuente:",fontsize=8.5,fontweight="bold",color=TEXT,va="top"); fig.text(.095,.125,textwrap.fill(f"IFT con datos del MOCIBA {PERIOD}, del INEGI. Para más información consultar {LANDING_PAGE}",190),fontsize=8.5,color=TEXT,va="top")
    fig.subplots_adjust(left=.055,right=.958,top=.74,bottom=.25); output.parent.mkdir(parents=True,exist_ok=True); fig.savefig(output,dpi=200); plt.close(fig)

def generate(context):
    print("  F.4 | 1/4 Adquisición o reutilización de MOCIBA 2024 y 2025"); ref_path=context.acquire_source(REFERENCE_SOURCE_ID); cur_path=context.acquire_source(CURRENT_SOURCE_ID)
    print("  F.4 | 2/4 Validación con MOCIBA 2024"); ref,ref_member=load_microdata(ref_path); validation=validate_reference(ref); del ref; print(f"  F.4 | Validación 2024 APROBADA: H={validation['hombres']:,.0f}, M={validation['mujeres']:,.0f}")
    print("  F.4 | 3/4 Cálculo MOCIBA 2025"); frame,member=load_microdata(cur_path); data,totals=calculate(frame); del frame; data.insert(0,"periodo",PERIOD)
    context.record_source_period(REFERENCE_SOURCE_ID,"2024","REFERENCIA_REPRODUCIDA"); context.record_source_period(CURRENT_SOURCE_ID,PERIOD,"AL_DIA"); context.write_data_used(data)
    context.record_calculation("validacion_2024","sum(FACTOR de víctimas por entidad y sexo) / sum(FACTOR de víctimas del sexo) * 100",{"miembro":ref_member},validation,"validación",2)
    context.record_calculation("distribucion_estatal_sexo_2025","sum(FACTOR de víctimas por entidad y sexo) / total nacional de víctimas del sexo * 100",{"miembro":member,"totales":totals,"entidades":32},{"suma_hombres":round(data.Hombres.sum(),6),"suma_mujeres":round(data.Mujeres.sum(),6)},"porcentaje",2)
    maxima={c:{"entidad":data.loc[data[c].idxmax(),"NOM_ENT"],"porcentaje":round(data[c].max(),2)} for c in ("Hombres","Mujeres")}; context.record_calculation("maximos_por_sexo","máximo de las 32 participaciones estatales",{"periodo":PERIOD},maxima,"porcentaje",2)
    summary=f"En {PERIOD}, la mayor participación estatal correspondió a {maxima['Mujeres']['entidad']} entre mujeres ({maxima['Mujeres']['porcentaje']:.1f}%) y a {maxima['Hombres']['entidad']} entre hombres ({maxima['Hombres']['porcentaje']:.1f}%)."; text_path=context.render_text("f_mociba.md.j2",{"resumen":summary})
    print(data.to_string(index=False,formatters={"Hombres":lambda x:f"{x:.1f}%","Mujeres":lambda x:f"{x:.1f}%"})); print("  F.4 | 4/4 Generación de gráfica PNG"); _plot(data,context.expected_figure_path,context.project_root)
    return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"detected_period":PERIOD,"rows_used":len(data),"reference_validation":"aprobada"}

def main()->int:
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID); return 0
if __name__=="__main__": raise SystemExit(main())
