"""Figura F.7: medidas de seguridad para equipos o cuentas, por sexo."""
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

FIGURE_ID="F.7";CURRENT_SOURCE_ID="inegi_mociba_2025";REFERENCE_SOURCE_ID="inegi_mociba_2024_reference";PERIOD="2025";LANDING_PAGE="https://www.inegi.org.mx/programas/mociba/2025/";TEXT="#50517F";WOMEN="#50517F";MEN="#F58F82";BG="#FBFBF7"
MEASURES={1:"Crear o poner contraseñas (claves, huella digital, patrón, etcétera)",2:"Instalar o actualizar programas antivirus, cortafuegos o antiespías",3:"Bloquear ventanas emergentes del navegador",4:"Cambiar periódicamente las contraseñas",5:"No ingresar a sitios web inseguros o desconocidos",6:"No abrir ni guardar archivos que envían personas desconocidas",7:"No publicar su correo o número telefónico en redes sociales",8:"Otra"}
OFFICIAL_H={1:95.2,2:23.2,3:9.0,4:9.0,5:7.4,6:6.6,7:5.9,8:.8};OFFICIAL_M={1:96.5,2:16.3,3:7.5,4:7.2,5:5.7,6:6.3,7:5.4,8:.8}
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
                if {"P1","P2_1","FACTOR","SEXO"}.issubset(df.columns):return df
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
    required={"FACTOR","SEXO","P1"}|{f"P2_{i}" for i in range(1,9)};missing=sorted(required-set(df.columns))
    if missing:raise ValueError(f"Faltan variables MOCIBA: {missing}")
    print(f"  {FIGURE_ID} | {path.name}: {len(df):,} registros, {member}");return df,member
def num(s:pd.Series)->pd.Series:return pd.to_numeric(s,errors="coerce")
def selected(df:pd.DataFrame,column:str,code:int)->pd.Series:
    own=0
    for c in [x for x in df.columns if x.startswith("P2_")]:
        match=re.search(r"(\d+)$",c)
        if match and int(match.group(1))>2 and int(match.group(1)) in set(num(df[c]).dropna().astype(int).unique()):own+=1
    return num(df[column]).eq(code if own>=2 else 1)
def pct(mask:pd.Series,universe:pd.Series,w:pd.Series)->float:
    den=float(w.loc[universe].sum())
    if den<=0:raise ValueError("Denominador ponderado no positivo")
    return float(w.loc[mask&universe].sum()/den*100)
def calculate(df:pd.DataFrame)->pd.DataFrame:
    w=num(df.FACTOR).fillna(0);eligible=num(df.P1).eq(1);rows=[]
    for code,label in MEASURES.items():
        choice=selected(df,f"P2_{code}",code);rows.append({"codigo":code,"medida":label,"Hombres":pct(choice,eligible&num(df.SEXO).eq(1),w),"Mujeres":pct(choice,eligible&num(df.SEXO).eq(2),w)})
    return pd.DataFrame(rows)
def validate_reference(df:pd.DataFrame)->dict[str,float]:
    data=calculate(df).set_index("codigo");differences=[abs(float(data.loc[k,c])-v) for c,e in (("Hombres",OFFICIAL_H),("Mujeres",OFFICIAL_M)) for k,v in e.items()]
    if max(differences)>.25:raise RuntimeError(f"MOCIBA 2024 no reproduce las medidas oficiales; desviación {max(differences):.3f} pp")
    return {"comprobaciones":16,"tolerancia_pp":.25,"desviacion_maxima_pp":max(differences)}
def _panel(fig:plt.Figure,rect:list[float],data:pd.DataFrame,column:str,color:str)->None:
    l,b,w,h=rect;fig.add_artist(patches.FancyBboxPatch((l,b),w,h,transform=fig.transFigure,boxstyle="round,pad=.006,rounding_size=.018",fc=BG,ec="#9296B5",lw=.8,zorder=0));ax=fig.add_axes([l+.025,b+.11,w-.05,h-.19]);ax.set_zorder(2);ax.patch.set_alpha(0);x=np.arange(len(data));bars=ax.bar(x,data[column],width=.42,color=color)
    for bar,value in zip(bars,data[column]):ax.text(bar.get_x()+bar.get_width()/2,value+2,f"{value:.1f}%",ha="center",fontsize=7.3,fontweight="bold",color=TEXT,bbox=dict(boxstyle="round,pad=.22",fc="white",ec="none"))
    ax.set_xticks(x,[textwrap.fill(v,14) for v in data.medida],fontsize=5.4,color=TEXT);ax.set_ylim(0,112);ax.set_yticks([0,20,40,60,80,100],[f"{v:.1f}%" for v in [0,20,40,60,80,100]],fontsize=7,color=TEXT);ax.tick_params(length=0,pad=5)
    for s in ax.spines.values():s.set_visible(False)
    fig.text(l+w*.72,b+h-.055,column,ha="center",va="center",fontsize=18,fontweight="bold",color=TEXT,bbox=dict(boxstyle="round,pad=.55,rounding_size=.8",fc="white",ec="none"),zorder=5)
def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    _fonts(root);fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.035,.09),.93,.83,transform=fig.transFigure,boxstyle="round,pad=.006,rounding_size=.018",fc=BG,ec="none",zorder=-1));fig.add_artist(patches.FancyBboxPatch((.052,.864),.008,.018,transform=fig.transFigure,boxstyle="round,pad=0,rounding_size=.003",fc=MEN,ec="none"));fig.text(.066,.873,"Figura F.7.",fontsize=14,fontweight="bold",color=TEXT,va="center");fig.text(.151,.873,"Medidas de seguridad para proteger equipos o cuentas de Internet, por sexo",fontsize=14,color=TEXT,va="center");_panel(fig,[.055,.20,.43,.57],data,"Mujeres",WOMEN);_panel(fig,[.515,.20,.43,.57],data,"Hombres",MEN);fig.text(.052,.125,"Fuente:",fontsize=8.5,fontweight="bold",color=TEXT,va="top");fig.text(.095,.125,textwrap.fill(f"IFT con datos del MOCIBA {PERIOD}, del INEGI. Para más información consultar {LANDING_PAGE}",190),fontsize=8.5,color=TEXT,va="top");output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=200);plt.close(fig)
def generate(context):
    print("  F.7 | 1/4 Adquisición o reutilización de MOCIBA 2024 y 2025");ref_path=context.acquire_source(REFERENCE_SOURCE_ID);cur_path=context.acquire_source(CURRENT_SOURCE_ID);print("  F.7 | 2/4 Validación con MOCIBA 2024");ref,ref_member=load_microdata(ref_path);validation=validate_reference(ref);del ref;print(f"  F.7 | Validación 2024 APROBADA; desviación máxima {validation['desviacion_maxima_pp']:.3f} pp");print("  F.7 | 3/4 Cálculo MOCIBA 2025");frame,member=load_microdata(cur_path);data=calculate(frame);del frame;data.insert(0,"periodo",PERIOD);context.record_source_period(REFERENCE_SOURCE_ID,"2024","REFERENCIA_REPRODUCIDA");context.record_source_period(CURRENT_SOURCE_ID,PERIOD,"AL_DIA");context.write_data_used(data);context.record_calculation("validacion_2024","sum(FACTOR de selección por medida y sexo) / sum(FACTOR de población elegible del sexo) * 100",{"miembro":ref_member},validation,"validación",3);context.record_calculation("medidas_seguridad_2025","sum(FACTOR de selección por medida y sexo) / total elegible por sexo * 100",{"miembro":member,"medidas":8},{"max_hombres":round(data.Hombres.max(),2),"max_mujeres":round(data.Mujeres.max(),2)},"porcentaje",2);summary=f"En {PERIOD}, la medida más utilizada fue {data.loc[data.Mujeres.idxmax(),'medida'].lower()}, con {data.Mujeres.max():.1f}% de las mujeres y {data.Hombres.max():.1f}% de los hombres.";text_path=context.render_text("f_mociba.md.j2",{"resumen":summary});print(data.to_string(index=False,formatters={"Hombres":lambda x:f"{x:.1f}%","Mujeres":lambda x:f"{x:.1f}%"}));print("  F.7 | 4/4 Generación de gráfica PNG");_plot(data,context.expected_figure_path,context.project_root);return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"detected_period":PERIOD,"rows_used":len(data),"reference_validation":"aprobada"}
def main()->int:
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
