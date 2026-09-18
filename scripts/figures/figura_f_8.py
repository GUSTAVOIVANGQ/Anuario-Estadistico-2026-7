"""Figura F.8: medios digitales usados para cometer ciberacoso."""
from __future__ import annotations
import re,sys,textwrap,zipfile
from io import BytesIO
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIGURE_ID="F.8";CURRENT_SOURCE_ID="inegi_mociba_2025";REFERENCE_SOURCE_ID="inegi_mociba_2024_reference";PERIOD="2025";LANDING_PAGE="https://www.inegi.org.mx/programas/mociba/2025/";TEXT="#3c3c3b";BLUE="#86adae";ACCENT="#4a7d75";BG="#F8F8FA"
MEDIA={1:"WhatsApp",2:"Facebook",3:"Messenger",4:"Instagram",5:"TikTok",6:"Telegram",7:"X (antes Twitter)",8:"YouTube",9:"SMS",10:"Correo electrónico institucional",11:"Correo electrónico personal",12:"Llamadas de teléfono celular",13:"Llamadas de teléfono fijo",14:"Otro medio"}
OFFICIAL={"WhatsApp":39.8,"Facebook":39.7,"Llamadas de teléfono celular":29.3,"Messenger":16.9,"Instagram":12.7,"SMS":4.7,"Llamadas de teléfono fijo":4.2,"Correo electrónico personal":2.7,"TikTok":2.4}
def _fonts(root:Path)->None:
    d=root/"assets"/"fonts"/"Noto_Sans"
    for n in ("NotoSans-Regular.ttf","NotoSans-Medium.ttf","NotoSans-Bold.ttf"):
        if (d/n).is_file():fm.fontManager.addfont(d/n)
    plt.rcParams["font.family"]="Noto Sans" if "Noto Sans" in {x.name for x in fm.fontManager.ttflist} else "DejaVu Sans"
def _csv(raw:bytes)->pd.DataFrame:
    for enc in ("utf-8-sig","latin1","cp1252"):
        for sep in (",","|",";"):
            try:
                df=pd.read_csv(BytesIO(raw),encoding=enc,sep=sep,low_memory=False);df.columns=[str(c).strip().upper() for c in df.columns]
                if {"P4_01","P11_01_1","FACTOR"}.issubset(df.columns):return df
            except Exception:pass
    raise ValueError("No se pudo leer el CSV MOCIBA")
def load_microdata(path:Path)->tuple[pd.DataFrame,str]:
    if not zipfile.is_zipfile(path):raise ValueError(f"ZIP MOCIBA inválido: {path}")
    with zipfile.ZipFile(path) as z:
        for member in z.namelist():
            if member.lower().endswith(".csv"):
                try:df=_csv(z.read(member));break
                except ValueError:continue
        else:raise ValueError("No se encontró CSV individual MOCIBA")
    required={"FACTOR"}|{f"P4_{i:02d}" for i in range(1,14)};missing=sorted(required-set(df.columns))
    if missing:raise ValueError(f"Faltan variables MOCIBA: {missing}")
    print(f"  {FIGURE_ID} | {path.name}: {len(df):,} registros, {member}");return df,member
def num(s:pd.Series)->pd.Series:return pd.to_numeric(s,errors="coerce")
def victims(df:pd.DataFrame)->pd.Series:return pd.concat([num(df[f"P4_{i:02d}"]).eq(1) for i in range(1,14)],axis=1).any(axis=1)
def calculate(df:pd.DataFrame)->pd.DataFrame:
    w=num(df.FACTOR).fillna(0);victim=victims(df);den=float(w.loc[victim].sum());columns=[c for c in df.columns if re.fullmatch(r"P11_\d{2}_[123]",c)]
    if not columns or den<=0:raise ValueError("No se localizaron P11_xx_1..3 o el denominador no es positivo")
    numeric=pd.concat([num(df[c]) for c in columns],axis=1);rows=[]
    for code,label in MEDIA.items():rows.append({"codigo":code,"medio":label,"porcentaje":float(w.loc[victim&numeric.eq(code).any(axis=1)].sum()/den*100)})
    return pd.DataFrame(rows).sort_values("porcentaje",ascending=False).reset_index(drop=True)
def validate_reference(df:pd.DataFrame)->dict[str,float]:
    data=calculate(df).set_index("medio");diff=[abs(float(data.loc[k,"porcentaje"])-v) for k,v in OFFICIAL.items()]
    if max(diff)>.25:raise RuntimeError(f"MOCIBA 2024 no reproduce los medios oficiales; desviación {max(diff):.3f} pp")
    return {"comprobaciones":len(diff),"tolerancia_pp":.25,"desviacion_maxima_pp":max(diff)}
def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    _fonts(root);fig,ax=plt.subplots(figsize=(16,9));fig.patch.set_facecolor("white");ax.set_facecolor(BG);x=np.arange(len(data));bars=ax.bar(x,data.porcentaje,width=.48,color=BLUE)
    for bar,value in zip(bars,data.porcentaje):ax.text(bar.get_x()+bar.get_width()/2,value+.65,f"{value:.1f}%",ha="center",fontsize=8.2,fontweight="bold",color=TEXT,bbox=dict(boxstyle="round,pad=.25,rounding_size=.8",fc="white",ec=BLUE,lw=.8))
    ax.set_xticks(x,[textwrap.fill(v,16) for v in data.medio],fontsize=7.2,fontweight="bold",color=TEXT);ax.set_ylim(0,max(data.porcentaje)*1.2);ax.set_yticks([]);ax.tick_params(axis="x",length=0,pad=9)
    for s in ax.spines.values():s.set_visible(False)
    fig.add_artist(patches.FancyBboxPatch((.035,.09),.93,.83,transform=fig.transFigure,boxstyle="round,pad=.006,rounding_size=.018",fc=BG,ec="none",zorder=-1));fig.add_artist(patches.FancyBboxPatch((.052,.864),.008,.018,transform=fig.transFigure,boxstyle="round,pad=0,rounding_size=.003",fc=ACCENT,ec="none"));fig.text(.066,.873,"Figura F.8.",fontsize=14,fontweight="bold",color=TEXT,va="center");fig.text(.151,.873,"Porcentaje de población de 12 años y más que vivió ciberacoso por medios digitales",fontsize=14,color=TEXT,va="center");fig.text(.052,.125,"Fuente:",fontsize=8.5,fontweight="bold",color=TEXT,va="top");fig.text(.095,.125,textwrap.fill(f"IFT con datos del MOCIBA {PERIOD}, del INEGI. Para más información consultar {LANDING_PAGE}",190),fontsize=8.5,color=TEXT,va="top");fig.subplots_adjust(left=.055,right=.958,top=.78,bottom=.27);output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=200);plt.close(fig)
def generate(context):
    print("  F.8 | 1/4 Adquisición o reutilización de MOCIBA 2024 y 2025");ref_path=context.acquire_source(REFERENCE_SOURCE_ID);cur_path=context.acquire_source(CURRENT_SOURCE_ID);print("  F.8 | 2/4 Validación con MOCIBA 2024");ref,ref_member=load_microdata(ref_path);validation=validate_reference(ref);del ref;print(f"  F.8 | Validación 2024 APROBADA; desviación máxima {validation['desviacion_maxima_pp']:.3f} pp");print("  F.8 | 3/4 Cálculo MOCIBA 2025");frame,member=load_microdata(cur_path);data=calculate(frame);del frame;data.insert(0,"periodo",PERIOD);context.record_source_period(REFERENCE_SOURCE_ID,"2024","REFERENCIA_REPRODUCIDA");context.record_source_period(CURRENT_SOURCE_ID,PERIOD,"AL_DIA");context.write_data_used(data);context.record_calculation("validacion_2024","sum(FACTOR de víctimas que reportan cada medio) / sum(FACTOR de víctimas) * 100",{"miembro":ref_member},validation,"validación",3);context.record_calculation("medios_digitales_2025","sum(FACTOR de víctimas que reportan el medio en P11) / total de víctimas * 100",{"miembro":member,"medios":14},{"mayor":data.iloc[0].medio,"mayor_pct":round(data.iloc[0].porcentaje,2),"menor":data.iloc[-1].medio,"menor_pct":round(data.iloc[-1].porcentaje,2)},"porcentaje",2);summary=f"En {PERIOD}, {data.iloc[0].medio} fue el medio más reportado ({data.iloc[0].porcentaje:.1f}%) y {data.iloc[-1].medio} el menos reportado ({data.iloc[-1].porcentaje:.1f}%).";text_path=context.render_text("f_mociba.md.j2",{"resumen":summary});print(data.to_string(index=False,formatters={"porcentaje":lambda x:f"{x:.1f}%"}));print("  F.8 | 4/4 Generación de gráfica PNG");_plot(data,context.expected_figure_path,context.project_root);return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"detected_period":PERIOD,"rows_used":len(data),"reference_validation":"aprobada"}
def main()->int:
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
