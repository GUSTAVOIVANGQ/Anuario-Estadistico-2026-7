"""Figura F.9: medidas tomadas contra el ciberacoso experimentado."""
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

FIGURE_ID="F.9";CURRENT_SOURCE_ID="inegi_mociba_2025";REFERENCE_SOURCE_ID="inegi_mociba_2024_reference";PERIOD="2025";LANDING_PAGE="https://www.inegi.org.mx/programas/mociba/2025/";TEXT="#3c3c3b";BLUE="#335a5c";ACCENT="#4a7d75";BG="#F8F8FA"
ACTIONS=[("Bloquear (a la persona, cuenta o página)",[("P12_01",1)]),("Ignorar o no contestar",[("P12_08",8)]),("Eliminar la publicación, el mensaje o video",[("P12_03",3)]),("Cambiar o cancelar número telefónico, cuenta o contraseña",[("P12_02",2)]),("Denunciar ante el Ministerio Público, Fiscalía Estatal o el proveedor del servicio",[("P12_05",5),("P12_06",6)]),("Informar a una persona (madre, padre, amiga(o), compañera(o) de trabajo, etcétera)",[("P12_07",7)]),("Reclamar o confrontar a la persona",[("P12_04",4)]),("Denunciar ante las autoridades escolares o laborales",[("P12_10",10)]),("Publicar la situación en redes sociales",[("P12_09",9)]),("Reportar ante la policía",[("P12_11",11)]),("Ninguna",[("P12_13",13)]),("Otra",[("P12_12",12)])]
OFFICIAL_H={"Bloquear":60.9,"Ignorar":16.5,"Ninguna":11.1};OFFICIAL_M={"Bloquear":71.2,"Ignorar":12.2,"Ninguna":5.5}
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
                if {"P4_01","P12_01","FACTOR","SEXO"}.issubset(df.columns):return df
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
    required={"FACTOR","SEXO"}|{f"P4_{i:02d}" for i in range(1,14)}|{f"P12_{i:02d}" for i in range(1,14)};missing=sorted(required-set(df.columns))
    if missing:raise ValueError(f"Faltan variables MOCIBA: {missing}")
    print(f"  {FIGURE_ID} | {path.name}: {len(df):,} registros, {member}");return df,member
def num(s:pd.Series)->pd.Series:return pd.to_numeric(s,errors="coerce")
def victims(df:pd.DataFrame)->pd.Series:return pd.concat([num(df[f"P4_{i:02d}"]).eq(1) for i in range(1,14)],axis=1).any(axis=1)
def selected(df:pd.DataFrame,column:str,code:int)->pd.Series:
    own=0
    for c in [x for x in df.columns if x.startswith("P12_")]:
        match=re.search(r"(\d+)$",c)
        if match and int(match.group(1))>2 and int(match.group(1)) in set(num(df[c]).dropna().astype(int).unique()):own+=1
    return num(df[column]).eq(code if own>=2 else 1)
def action_mask(df:pd.DataFrame,spec:list[tuple[str,int]])->pd.Series:return pd.concat([selected(df,c,k) for c,k in spec],axis=1).any(axis=1)
def pct(mask:pd.Series,universe:pd.Series,w:pd.Series)->float:
    den=float(w.loc[universe].sum())
    if den<=0:raise ValueError("Denominador ponderado no positivo")
    return float(w.loc[mask&universe].sum()/den*100)
def calculate(df:pd.DataFrame)->tuple[pd.DataFrame,dict[str,dict[str,float]]]:
    w=num(df.FACTOR).fillna(0);victim=victims(df);rows=[];checks={"Hombres":{},"Mujeres":{}}
    for label,spec in ACTIONS:
        mask=action_mask(df,spec);rows.append({"medida":label,"porcentaje":pct(mask,victim,w)})
        key="Bloquear" if label.startswith("Bloquear") else "Ignorar" if label.startswith("Ignorar") else "Ninguna" if label=="Ninguna" else None
        if key:
            for gender,code in (("Hombres",1),("Mujeres",2)):checks[gender][key]=pct(mask,victim&num(df.SEXO).eq(code),w)
    return pd.DataFrame(rows).sort_values("porcentaje").reset_index(drop=True),checks
def validate_reference(df:pd.DataFrame)->dict[str,float]:
    _,checks=calculate(df);diff=[abs(checks[c][k]-v) for c,e in (("Hombres",OFFICIAL_H),("Mujeres",OFFICIAL_M)) for k,v in e.items()]
    if max(diff)>.25:raise RuntimeError(f"MOCIBA 2024 no reproduce las medidas oficiales; desviación {max(diff):.3f} pp")
    return {"comprobaciones":6,"tolerancia_pp":.25,"desviacion_maxima_pp":max(diff)}
def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    _fonts(root);fig,ax=plt.subplots(figsize=(16,9));fig.patch.set_facecolor("white");ax.set_facecolor(BG);y=np.arange(len(data));bars=ax.barh(y,data.porcentaje,height=.48,color=BLUE)
    for bar,value in zip(bars,data.porcentaje):ax.text(value+.5,bar.get_y()+bar.get_height()/2,f"{value:.1f}%",va="center",fontsize=8.5,color=TEXT)
    ax.set_yticks(y,[textwrap.fill(v,42) for v in data.medida],fontsize=8,color=TEXT);upper=max(80,np.ceil(data.porcentaje.max()/10)*10+10);ax.set_xlim(0,upper);ax.set_xticks(np.arange(0,upper+1,10),[f"{v:.1f}%" for v in np.arange(0,upper+1,10)],fontsize=7.5,color=TEXT);ax.tick_params(length=0)
    for s in ax.spines.values():s.set_visible(False)
    fig.add_artist(patches.FancyBboxPatch((.035,.09),.93,.83,transform=fig.transFigure,boxstyle="round,pad=.006,rounding_size=.018",fc=BG,ec="none",zorder=-1));fig.add_artist(patches.FancyBboxPatch((.052,.864),.008,.018,transform=fig.transFigure,boxstyle="round,pad=0,rounding_size=.003",fc=ACCENT,ec="none"));fig.text(.066,.873,"Figura F.9.",fontsize=14,fontweight="bold",color=TEXT,va="center");fig.text(.151,.873,"Medidas tomadas contra el ciberacoso experimentado",fontsize=14,color=TEXT,va="center");fig.text(.052,.125,"Fuente:",fontsize=8.5,fontweight="bold",color=TEXT,va="top");fig.text(.095,.125,textwrap.fill(f"IFT con datos del MOCIBA {PERIOD}, del INEGI. Para más información consultar {LANDING_PAGE}",190),fontsize=8.5,color=TEXT,va="top");fig.subplots_adjust(left=.34,right=.94,top=.79,bottom=.19);output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=200);plt.close(fig)
def generate(context):
    print("  F.9 | 1/4 Adquisición o reutilización de MOCIBA 2024 y 2025");ref_path=context.acquire_source(REFERENCE_SOURCE_ID);cur_path=context.acquire_source(CURRENT_SOURCE_ID);print("  F.9 | 2/4 Validación con MOCIBA 2024");ref,ref_member=load_microdata(ref_path);validation=validate_reference(ref);del ref;print(f"  F.9 | Validación 2024 APROBADA; desviación máxima {validation['desviacion_maxima_pp']:.3f} pp");print("  F.9 | 3/4 Cálculo MOCIBA 2025");frame,member=load_microdata(cur_path);data,checks=calculate(frame);del frame;data.insert(0,"periodo",PERIOD);context.record_source_period(REFERENCE_SOURCE_ID,"2024","REFERENCIA_REPRODUCIDA");context.record_source_period(CURRENT_SOURCE_ID,PERIOD,"AL_DIA");context.write_data_used(data);context.record_calculation("validacion_2024","sum(FACTOR de víctimas que reportan la medida por sexo) / total de víctimas del sexo * 100",{"miembro":ref_member},validation,"validación",3);context.record_calculation("medidas_ciberacoso_2025","sum(FACTOR de víctimas que reportan la medida) / total de víctimas * 100",{"miembro":member,"medidas":12},{"mayor":data.iloc[-1].medida,"mayor_pct":round(data.iloc[-1].porcentaje,2),"comprobacion_sexo":checks},"porcentaje",2);summary=f"En {PERIOD}, la medida más reportada fue {data.iloc[-1].medida.lower()} ({data.iloc[-1].porcentaje:.1f}%).";text_path=context.render_text("f_mociba.md.j2",{"resumen":summary});print(data.to_string(index=False,formatters={"porcentaje":lambda x:f"{x:.1f}%"}));print("  F.9 | 4/4 Generación de gráfica PNG");_plot(data,context.expected_figure_path,context.project_root);return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"detected_period":PERIOD,"rows_used":len(data),"reference_validation":"aprobada"}
def main()->int:
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
