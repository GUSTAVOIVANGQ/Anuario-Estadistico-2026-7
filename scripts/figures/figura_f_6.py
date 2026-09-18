"""Figura F.6: situaciones de ciberacoso experimentadas, por sexo."""
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

FIGURE_ID="F.6";CURRENT_SOURCE_ID="inegi_mociba_2025";REFERENCE_SOURCE_ID="inegi_mociba_2024_reference";PERIOD="2025";LANDING_PAGE="https://www.inegi.org.mx/programas/mociba/2025/"
TEXT="#3c3c3b";WOMEN="#86adae";MEN="#335a5c";BG="#F8F8FA"
SITUATIONS={1:"Mensajes ofensivos",2:"Llamadas ofensivas",3:"Críticas por apariencia o clase social",4:"Suplantación de identidad",5:"Contacto mediante identidades falsas",6:"Rastreo de cuentas o sitios web",7:"Provocaciones para reaccionar de forma negativa",8:"Insinuaciones o propuestas sexuales",9:"Recibir contenido sexual",10:"Publicar o vender imágenes o videos de contenido sexual",11:"Publicar y/o enviar información personal, fotos o videos",12:"Amenazar con publicar información personal, audios o videos",13:"Otra situación"}
OFFICIAL_W={"Contacto mediante identidades falsas":36.0,"Mensajes ofensivos":32.4,"Llamadas ofensivas":21.0,"Insinuaciones o propuestas sexuales":29.0,"Recibir contenido sexual":27.5};OFFICIAL_H={"Contacto mediante identidades falsas":36.0,"Mensajes ofensivos":35.9,"Llamadas ofensivas":24.6,"Insinuaciones o propuestas sexuales":13.9,"Recibir contenido sexual":15.8}

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
                if {"P4_01","FACTOR","SEXO"}.issubset(df.columns):return df
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
    required={"FACTOR","SEXO"}|{f"P4_{i:02d}" for i in range(1,14)};missing=sorted(required-set(df.columns))
    if missing:raise ValueError(f"Faltan variables MOCIBA: {missing}")
    print(f"  {FIGURE_ID} | {path.name}: {len(df):,} registros, {member}");return df,member
def num(s:pd.Series)->pd.Series:return pd.to_numeric(s,errors="coerce")
def weights(df:pd.DataFrame)->pd.Series:return num(df.FACTOR).fillna(0)
def victims(df:pd.DataFrame)->pd.Series:return pd.concat([num(df[f"P4_{i:02d}"]).eq(1) for i in range(1,14)],axis=1).any(axis=1)
def sex(df:pd.DataFrame,label:str)->pd.Series:return num(df.SEXO).eq(1 if label=="Hombres" else 2)
def pct(mask:pd.Series,universe:pd.Series,w:pd.Series)->float:
    den=float(w.loc[universe].sum())
    if den<=0:raise ValueError("Denominador ponderado no positivo")
    return float(w.loc[mask&universe].sum()/den*100)
def calculate(df:pd.DataFrame)->pd.DataFrame:
    w=weights(df);victim=victims(df);rows=[]
    for code,label in SITUATIONS.items():
        yes=num(df[f"P4_{code:02d}"]).eq(1);rows.append({"situacion":label,"Hombres":pct(yes,victim&sex(df,"Hombres"),w),"Mujeres":pct(yes,victim&sex(df,"Mujeres"),w)})
    return pd.DataFrame(rows).sort_values("Mujeres").reset_index(drop=True)
def validate_reference(df:pd.DataFrame)->dict[str,float]:
    data=calculate(df).set_index("situacion");errors=[]
    for column,expected in (("Mujeres",OFFICIAL_W),("Hombres",OFFICIAL_H)):
        for key,value in expected.items():
            difference=abs(float(data.loc[key,column])-value)
            if difference>.25:errors.append(f"{column}/{key}: {difference:.3f}")
    if errors:raise RuntimeError("MOCIBA 2024 no reproduce las cifras oficiales: "+" | ".join(errors))
    return {"comprobaciones":10,"tolerancia_pp":.25,"desviacion_maxima_pp":max(abs(float(data.loc[k,c])-v) for c,e in (("Mujeres",OFFICIAL_W),("Hombres",OFFICIAL_H)) for k,v in e.items())}
def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    _fonts(root);fig,ax=plt.subplots(figsize=(16,9));fig.patch.set_facecolor("white");ax.set_facecolor(BG);y=np.arange(len(data));h=.34
    ax.barh(y+h/2,data.Mujeres,height=h,color=WOMEN,label="Mujeres");ax.barh(y-h/2,data.Hombres,height=h,color=MEN,label="Hombres")
    for i,row in data.iterrows():
        ax.text(row.Mujeres+.35,i+h/2,f"{row.Mujeres:.1f}%",va="center",fontsize=7,color=TEXT);ax.text(row.Hombres+.35,i-h/2,f"{row.Hombres:.1f}%",va="center",fontsize=7,color=TEXT)
    ax.set_yticks(y,[textwrap.fill(x,38) for x in data.situacion],fontsize=8.2,color=TEXT);ax.set_xlim(0,max(data[["Hombres","Mujeres"]].max())*1.13);ax.set_xticks(np.arange(0,41,5),[f"{v:.1f}%" for v in np.arange(0,41,5)],fontsize=7.5,color=TEXT);ax.tick_params(length=0)
    for s in ax.spines.values():s.set_visible(False)
    fig.legend(loc="upper center",bbox_to_anchor=(.57,.815),ncol=2,frameon=False,labelcolor=TEXT)
    fig.add_artist(patches.FancyBboxPatch((.035,.09),.93,.83,transform=fig.transFigure,boxstyle="round,pad=.006,rounding_size=.018",fc=BG,ec="none",zorder=-1));fig.add_artist(patches.FancyBboxPatch((.052,.864),.008,.018,transform=fig.transFigure,boxstyle="round,pad=0,rounding_size=.003",fc="#4a7d75",ec="none"));fig.text(.066,.873,"Figura F.6.",fontsize=14,fontweight="bold",color=TEXT,va="center");fig.text(.151,.873,"Distribución porcentual de las situaciones de ciberacoso experimentadas por sexo",fontsize=14,color=TEXT,va="center");fig.text(.052,.125,"Fuente:",fontsize=8.5,fontweight="bold",color=TEXT,va="top");fig.text(.095,.125,textwrap.fill(f"IFT con datos del MOCIBA {PERIOD}, del INEGI. Para más información consultar {LANDING_PAGE}",190),fontsize=8.5,color=TEXT,va="top")
    fig.subplots_adjust(left=.34,right=.94,top=.75,bottom=.19);output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=200);plt.close(fig)
def generate(context):
    print("  F.6 | 1/4 Adquisición o reutilización de MOCIBA 2024 y 2025");ref_path=context.acquire_source(REFERENCE_SOURCE_ID);cur_path=context.acquire_source(CURRENT_SOURCE_ID);print("  F.6 | 2/4 Validación con MOCIBA 2024");ref,ref_member=load_microdata(ref_path);validation=validate_reference(ref);del ref;print(f"  F.6 | Validación 2024 APROBADA; desviación máxima {validation['desviacion_maxima_pp']:.3f} pp")
    print("  F.6 | 3/4 Cálculo MOCIBA 2025");frame,member=load_microdata(cur_path);data=calculate(frame);del frame;data.insert(0,"periodo",PERIOD);context.record_source_period(REFERENCE_SOURCE_ID,"2024","REFERENCIA_REPRODUCIDA");context.record_source_period(CURRENT_SOURCE_ID,PERIOD,"AL_DIA");context.write_data_used(data);context.record_calculation("validacion_2024","sum(FACTOR de víctimas que reportan la situación y sexo) / sum(FACTOR de víctimas del sexo) * 100",{"miembro":ref_member},validation,"validación",3);context.record_calculation("situaciones_por_sexo_2025","sum(FACTOR de respuesta Sí por situación y sexo) / total de víctimas del sexo * 100",{"miembro":member,"situaciones":13},{"max_mujeres":round(data.Mujeres.max(),2),"max_hombres":round(data.Hombres.max(),2)},"porcentaje",2);summary=f"En {PERIOD}, la situación más frecuente entre mujeres fue {data.loc[data.Mujeres.idxmax(),'situacion']} ({data.Mujeres.max():.1f}%) y entre hombres {data.loc[data.Hombres.idxmax(),'situacion']} ({data.Hombres.max():.1f}%).";text_path=context.render_text("f_mociba.md.j2",{"resumen":summary});print(data.to_string(index=False,formatters={"Hombres":lambda x:f"{x:.1f}%","Mujeres":lambda x:f"{x:.1f}%"}));print("  F.6 | 4/4 Generación de gráfica PNG");_plot(data,context.expected_figure_path,context.project_root);return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"detected_period":PERIOD,"rows_used":len(data),"reference_validation":"aprobada"}
def main()->int:
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
