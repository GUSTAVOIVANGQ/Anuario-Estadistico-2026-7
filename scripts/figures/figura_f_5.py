"""Figura F.5: víctimas de ciberacoso por sexo y grupo de edad."""
from __future__ import annotations
import sys,textwrap,zipfile
from io import BytesIO
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIGURE_ID="F.5"; CURRENT_SOURCE_ID="inegi_mociba_2025"; REFERENCE_SOURCE_ID="inegi_mociba_2024_reference"; PERIOD="2025"; LANDING_PAGE="https://www.inegi.org.mx/programas/mociba/2025/"
TEXT="#50517F"; WOMEN="#ADDCDD"; MEN="#F58F82"; BG="#FBFBF7"; BINS=[(12,19,"De 12 a\n19 años"),(20,29,"De 20 a\n29 años"),(30,39,"De 30 a\n39 años"),(40,49,"De 40 a\n49 años"),(50,59,"De 50 a\n59 años"),(60,200,"De 60 años\ny más")]

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
                if {"P4_01","FACTOR","EDAD"}.issubset(df.columns): return df
            except Exception as exc:last=exc
    raise ValueError(f"No se pudo leer MOCIBA: {last}")
def load_microdata(path:Path)->tuple[pd.DataFrame,str]:
    if not zipfile.is_zipfile(path):raise ValueError(f"ZIP MOCIBA inválido: {path}")
    with zipfile.ZipFile(path) as z:
        for member in z.namelist():
            if member.lower().endswith(".csv"):
                try:df=_csv(z.read(member));break
                except ValueError:continue
        else:raise ValueError("No se encontró CSV individual MOCIBA")
    required={"FACTOR","SEXO","EDAD"}|{f"P4_{i:02d}" for i in range(1,14)}; missing=sorted(required-set(df.columns))
    if missing:raise ValueError(f"Faltan variables MOCIBA: {missing}")
    print(f"  {FIGURE_ID} | {path.name}: {len(df):,} registros, {member}");return df,member
def num(s:pd.Series)->pd.Series:return pd.to_numeric(s,errors="coerce")
def weights(df:pd.DataFrame)->pd.Series:return num(df.FACTOR).fillna(0)
def victims(df:pd.DataFrame)->pd.Series:return pd.concat([num(df[f"P4_{i:02d}"]).eq(1) for i in range(1,14)],axis=1).any(axis=1)
def sex(df:pd.DataFrame,label:str)->pd.Series:return num(df.SEXO).eq(1 if label=="Hombres" else 2)

def calculate(df:pd.DataFrame)->tuple[pd.DataFrame,dict[str,float]]:
    w=weights(df); victim=victims(df); age=num(df.EDAD); rows=[]; totals={}
    for label in ("Hombres","Mujeres"):totals[label]=float(w.loc[victim&sex(df,label)].sum())
    for lo,hi,label in BINS:
        row={"edad":label,"orden":lo}; age_mask=age.between(lo,hi,inclusive="both")
        for gender in ("Hombres","Mujeres"):
            universe=victim&sex(df,gender); row[gender]=float(w.loc[universe&age_mask].sum()/totals[gender]*100)
        rows.append(row)
    out=pd.DataFrame(rows)
    if any(abs(out[c].sum()-100)>1e-7 for c in ("Hombres","Mujeres")):raise ValueError("Los grupos de edad no cubren 100% de las víctimas por sexo")
    return out,totals
def validate_reference(df:pd.DataFrame)->dict[str,float]:
    data,totals=calculate(df)
    if not 8_200_000<=totals["Hombres"]<=8_400_000 or not 10_500_000<=totals["Mujeres"]<=10_700_000:raise RuntimeError("MOCIBA 2024 no reproduce los totales oficiales por sexo")
    return {"suma_hombres":float(data.Hombres.sum()),"suma_mujeres":float(data.Mujeres.sum()),"total_hombres":totals["Hombres"],"total_mujeres":totals["Mujeres"]}

def _panel(fig:plt.Figure,rect:list[float],data:pd.DataFrame,column:str,color:str)->None:
    left,bottom,width,height=rect; fig.add_artist(patches.FancyBboxPatch((left,bottom),width,height,transform=fig.transFigure,boxstyle="round,pad=.006,rounding_size=.018",fc=BG,ec="#9296B5",lw=.8,zorder=0)); ax=fig.add_axes([left+.025,bottom+.08,width-.05,height-.14]);ax.set_zorder(2);ax.patch.set_alpha(0)
    x=np.arange(len(data));bars=ax.bar(x,data[column],width=.38,color=color)
    for bar,value in zip(bars,data[column]):ax.text(bar.get_x()+bar.get_width()/2,value*.55,f"{value:.1f}%",ha="center",va="center",fontsize=9,fontweight="bold",color=TEXT,bbox=dict(boxstyle="round,pad=.25",fc="white",ec="none"))
    ax.set_xticks(x,data.edad,fontsize=7.4,fontweight="bold",color=TEXT);ax.set_ylim(0,max(35,data[column].max()*1.2));ax.set_yticks([]);ax.tick_params(axis="x",length=0,pad=8)
    for s in ax.spines.values():s.set_visible(False)
    fig.text(left+width*.72,bottom+height-.055,column,ha="center",va="center",fontsize=18,fontweight="bold",color=TEXT,bbox=dict(boxstyle="round,pad=.55,rounding_size=.8",fc="white",ec="none"),zorder=5)
def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    _fonts(root);fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.035,.09),.93,.83,transform=fig.transFigure,boxstyle="round,pad=.006,rounding_size=.018",fc=BG,ec="none",zorder=-1));fig.add_artist(patches.FancyBboxPatch((.052,.864),.008,.018,transform=fig.transFigure,boxstyle="round,pad=0,rounding_size=.003",fc=MEN,ec="none"))
    fig.text(.066,.873,"Figura F.5.",fontsize=14,fontweight="bold",color=TEXT,va="center");fig.text(.151,.873,"Porcentaje de la población que vivió ciberacoso por sexo y rango de edad",fontsize=14,color=TEXT,va="center")
    _panel(fig,[.055,.20,.43,.57],data,"Mujeres",WOMEN);_panel(fig,[.515,.20,.43,.57],data,"Hombres",MEN)
    fig.text(.052,.125,"Fuente:",fontsize=8.5,fontweight="bold",color=TEXT,va="top");fig.text(.095,.125,textwrap.fill(f"IFT con datos del MOCIBA {PERIOD}, del INEGI. Para más información consultar {LANDING_PAGE}",190),fontsize=8.5,color=TEXT,va="top");output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=200);plt.close(fig)

def generate(context):
    print("  F.5 | 1/4 Adquisición o reutilización de MOCIBA 2024 y 2025");ref_path=context.acquire_source(REFERENCE_SOURCE_ID);cur_path=context.acquire_source(CURRENT_SOURCE_ID)
    print("  F.5 | 2/4 Validación con MOCIBA 2024");ref,ref_member=load_microdata(ref_path);validation=validate_reference(ref);del ref;print("  F.5 | Validación 2024 APROBADA: cada sexo suma 100%")
    print("  F.5 | 3/4 Cálculo MOCIBA 2025");frame,member=load_microdata(cur_path);data,totals=calculate(frame);del frame;data.insert(0,"periodo",PERIOD)
    context.record_source_period(REFERENCE_SOURCE_ID,"2024","REFERENCIA_REPRODUCIDA");context.record_source_period(CURRENT_SOURCE_ID,PERIOD,"AL_DIA");context.write_data_used(data.drop(columns="orden"));context.record_calculation("validacion_2024","sum(FACTOR de víctimas del grupo de edad y sexo) / total de víctimas del sexo * 100",{"miembro":ref_member},validation,"validación",2);context.record_calculation("distribucion_edad_sexo_2025","sum(FACTOR de víctimas por edad y sexo) / sum(FACTOR de víctimas del sexo) * 100",{"miembro":member,"totales":totals},{"suma_hombres":round(data.Hombres.sum(),6),"suma_mujeres":round(data.Mujeres.sum(),6)},"porcentaje",2)
    maxima={c:{"edad":data.loc[data[c].idxmax(),"edad"].replace("\n"," "),"porcentaje":round(data[c].max(),2)} for c in ("Hombres","Mujeres")};context.record_calculation("maximos_edad_por_sexo","máximo de seis grupos de edad",{"periodo":PERIOD},maxima,"porcentaje",2);summary=f"En {PERIOD}, el grupo con mayor participación entre las víctimas fue {maxima['Mujeres']['edad']} para mujeres ({maxima['Mujeres']['porcentaje']:.1f}%) y {maxima['Hombres']['edad']} para hombres ({maxima['Hombres']['porcentaje']:.1f}%).";text_path=context.render_text("f_mociba.md.j2",{"resumen":summary});print(data.drop(columns="orden").to_string(index=False,formatters={"Hombres":lambda x:f"{x:.1f}%","Mujeres":lambda x:f"{x:.1f}%"}));print("  F.5 | 4/4 Generación de gráfica PNG");_plot(data,context.expected_figure_path,context.project_root)
    return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"detected_period":PERIOD,"rows_used":len(data),"reference_validation":"aprobada"}
def main()->int:
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
