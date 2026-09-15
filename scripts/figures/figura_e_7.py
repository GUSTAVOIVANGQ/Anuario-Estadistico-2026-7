"""Figura E.7: dispositivos utilizados por las MiPymes, 2023-2024."""
from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui

import re,sys,textwrap,unicodedata,zipfile
from io import BytesIO
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIGURE_ID,PERIOD="E.7","2024"; SOURCES={2023:"ift_mipymes_2023_base",2024:"ift_mipymes_2024_base"}; SIZES=["General","Micro","Pequeña","Mediana"]
DEVICES=[("Teléfonos móviles inteligentes",["smartphone"]),("Computadoras de escritorio",["escritorio"]),("Terminal punto de venta, clip o tableta",["terminal"]),("Laptop",["laptop"]),("Teléfonos móviles análogos",["sin acceso"]),("Servidores de almacenamiento",["servidor"])]
REFERENCE={2023:{"Teléfonos móviles inteligentes":[98.5,98.7,94.9,96.1],"Computadoras de escritorio":[49.1,47.4,74.1,93.3],"Terminal punto de venta, clip o tableta":[54.5,54.2,60.7,58.2],"Laptop":[41.9,40.5,62.1,73.6],"Teléfonos móviles análogos":[34.3,33.8,44.7,46.8],"Servidores de almacenamiento":[14.0,12.5,33.6,56.4]},2024:{"Teléfonos móviles inteligentes":[95.7,95.6,97.2,93.7],"Computadoras de escritorio":[51.3,49.7,74.3,87.5],"Terminal punto de venta, clip o tableta":[47.1,46.8,50.1,61.8],"Laptop":[38.2,36.7,60.3,59.1],"Teléfonos móviles análogos":[31.2,30.1,45.6,41.4],"Servidores de almacenamiento":[17.8,16.5,36.0,44.1]}}
TEXT,BG,CORAL,BLUE,CYAN="#4B4B7D","#EEF6F4","#F48D7E","#327BA0","#A9DADF"


def _norm(v:object)->str:
    t=unicodedata.normalize("NFKD",str(v).replace("\xa0"," ").lower()); return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9]+"," ","".join(c for c in t if not unicodedata.combining(c)))).strip()
def load_raw(path:Path)->pd.DataFrame:
    with zipfile.ZipFile(path) as z:
        ns=[n for n in z.namelist() if n.lower().endswith((".xlsx",".xls")) and "diccionario" not in _norm(n)]; n=max(ns,key=lambda x:z.getinfo(x).file_size); return pd.read_excel(BytesIO(z.read(n)))
def _find(df:pd.DataFrame,*tokens:str,reject:list[str]=[])->str:
    fs=[str(c) for c in df.columns if all(_norm(t) in _norm(c) for t in tokens) and not any(_norm(t) in _norm(c) for t in reject)]
    if not fs: raise KeyError(f"No se encontró columna {tokens}")
    return min(fs,key=lambda c:len(_norm(c)))
def _yes(s:pd.Series)->pd.Series: return s.astype("string").map(_norm).isin({"si","s","yes"})


def build_metrics(frames:dict[int,pd.DataFrame])->pd.DataFrame:
    rows=[]
    for year,df in frames.items():
        weight=_find(df,"factor","expansion","final"); size_col=_find(df,"clasificacion","empresa","tamano"); sizes={s:next(v for v in df[size_col].dropna().unique() if _norm(s)[:4] in _norm(v)) for s in SIZES[1:]}
        for device,tokens in DEVICES:
            # La encuesta también pregunta por servidores en una sección de
            # almacenamiento.  Acotar a la pregunta principal de dispositivos
            # evita mezclar ambas variables, que tienen denominadores distintos.
            col=_find(df,"ahora","digame","dispositivos",*tokens,reject=["beneficio","frecuencia","satisfech"])
            for size in SIZES:
                sub=df if size=="General" else df.loc[df[size_col].eq(sizes[size])]; valid=sub[[col,weight]].dropna(); weights=pd.to_numeric(valid[weight],errors="coerce").fillna(0); denominator=float(weights.sum()); numerator=float(weights.loc[_yes(valid[col])].sum()); rows.append({"anio":year,"dispositivo":device,"tamano":size,"porcentaje":numerator/denominator*100,"numerador_ponderado":numerator,"denominador_ponderado":denominator,"columna":col})
    return pd.DataFrame(rows)


def validate(data:pd.DataFrame)->float:
    dev=max(abs(round(float(data.loc[(data.anio.eq(y))&(data.dispositivo.eq(device))&(data.tamano.eq(size)),"porcentaje"].iloc[0]),1)-value) for y in REFERENCE for device,vals in REFERENCE[y].items() for size,value in zip(SIZES,vals))
    if dev>.11: raise ValueError(f"E.7 no reproduce la referencia: {dev:.1f} pp")
    return dev


def _font(root:Path)->str:
    for n in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        p=root/"assets"/"fonts"/"Noto_Sans"/n
        if p.is_file(): fm.fontManager.addfont(p)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    plt.rcParams.update({"font.family":_font(root)}); fig=plt.figure(figsize=(16,9),facecolor="white"); fig.text(.045,.90,"•",color=CORAL,fontsize=20,va="center"); fig.text(.063,.90,"Figura E.7.",color=TEXT,fontsize=16,fontweight="bold",va="center"); fig.text(.17,.90,"Dispositivos que usan las MiPymes para realizar sus actividades (2023-2024)",color=TEXT,fontsize=16,va="center")
    for idx,(device,_) in enumerate(DEVICES):
        row,col=divmod(idx,3); ax=fig.add_axes([.055+col*.315,.54-row*.36,.285,.25]); ax.set_facecolor(BG); x=np.arange(4); width=.34
        for i,(year,color) in enumerate(((2023,CYAN if row==0 else CORAL),(2024,BLUE if row==0 else "#F0535A"))):
            vals=[float(data.loc[(data.anio.eq(year))&(data.dispositivo.eq(device))&(data.tamano.eq(s)),"porcentaje"].iloc[0]) for s in SIZES]; bars=ax.bar(x+(i-.5)*width,vals,width,color=color,label=str(year))
            for bar,v in zip(bars,vals): ax.text(bar.get_x()+bar.get_width()/2,v+2,f"{v:.1f}%",ha="center",fontsize=7.5,color=TEXT,fontweight="bold")
        ax.set_ylim(0,112); ax.set_xticks(x,SIZES,fontsize=7.5,color=TEXT); ax.set_yticks([]); ax.tick_params(length=0); ax.spines[:].set_visible(False); ax.set_title(textwrap.fill(device,31),fontsize=11,color=TEXT,fontweight="bold",pad=5); ax.legend(ncol=2,loc="upper center",bbox_to_anchor=(.5,-.12),frameon=False,fontsize=7)
    fig.text(.045,.105,"Fuente:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.091,.105,"IFT, Cuarta Encuesta 2023 y 2024, Usuarios de Servicios de Telecomunicaciones (MiPymes).",color=TEXT,fontsize=9)
    fig.text(.045,.077,"Nota:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.08,.077,"Respuesta múltiple, por lo que la suma no da 100%.",color=TEXT,fontsize=9)
    output.parent.mkdir(parents=True,exist_ok=True); apply_reference_ui(fig, FIGURE_ID); fig.savefig(output,dpi=200); plt.close(fig)


def generate(context):
    frames={}
    for year,source in SOURCES.items(): print(f"  E.7 | Descarga o reutilización de MiPymes {year}"); frames[year]=load_raw(context.acquire_source(source)); context.record_source_period(source,str(year),"ULTIMO_PUBLICADO" if year==2024 else "HISTORICO")
    data=build_metrics(frames); deviation=validate(data); context.write_data_used(data[["anio","dispositivo","tamano","porcentaje"]])
    for row in data.itertuples(index=False): context.record_calculation(f"dispositivo_{row.anio}_{_norm(row.dispositivo)}_{_norm(row.tamano)}","sum(factor donde respuesta Sí) / sum(factor con respuesta) * 100",{"anio":row.anio,"dispositivo":row.dispositivo,"tamano":row.tamano,"numerador":row.numerador_ponderado,"denominador":row.denominador_ponderado,"columna":row.columna},row.porcentaje,"porcentaje",1)
    top=data.loc[data.anio.eq(2024)].sort_values("porcentaje",ascending=False).iloc[0]; text_path=context.render_text("f_digital.md.j2",{"resumen":f"En 2024 el dispositivo con mayor uso fue {top.dispositivo.lower()} ({top.porcentaje:.1f}% en {top.tamano.lower()})."}); print(f"Validación 2023-2024: desviación máxima {deviation:.1f} pp"); _plot(data,context.expected_figure_path,context.project_root)
    return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"source_latest_period":PERIOD,"rows_used":len(data)}


def main()->int:
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID); return 0
if __name__=="__main__": raise SystemExit(main())
