"""Figura E.3: IGS por servicio y tamaño de empresa, 2023-2024."""
from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui

import re, sys, unicodedata, zipfile
from io import BytesIO
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIGURE_ID, PERIOD = "E.3", "2024"
SOURCES={2022:"ift_mipymes_2022_base",2023:"ift_mipymes_2023_base",2024:"ift_mipymes_2024_base"}
SIZES=["Micro","Pequeña","Mediana"]; SERVICES=["Internet fijo","Telefonía fija"]
REFERENCE={2022:{"Internet fijo":[74.0,76.0,73.9],"Telefonía fija":[75.0,76.9,74.1]},2023:{"Internet fijo":[74.4,76.9,79.2],"Telefonía fija":[75.2,76.0,78.2]},2024:{"Internet fijo":[76.2,76.1,75.6],"Telefonía fija":[76.8,77.5,78.9]}}
TEXT,BG,BLUE,CYAN,CORAL,RED="#4B4B7D","#FBFBF7","#327BA0","#A9DADF","#F48D7E","#F0535A"


def _norm(value:object)->str:
    text=unicodedata.normalize("NFKD",str(value).replace("\xa0"," ").lower()); return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9]+"," ","".join(c for c in text if not unicodedata.combining(c)))).strip()


def load_raw(path:Path)->pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        choices=[n for n in archive.namelist() if n.lower().endswith((".xlsx",".xls")) and "diccionario" not in _norm(n)]
        if not choices: raise ValueError(f"El ZIP {path.name} no contiene la base Excel")
        member=max(choices,key=lambda n:archive.getinfo(n).file_size); return pd.read_excel(BytesIO(archive.read(member)))


def _column(df:pd.DataFrame,*tokens:str,prefer:str="")->str:
    found=[]
    for column in df.columns:
        n=_norm(column)
        if all(_norm(t) in n for t in tokens): found.append((1 if prefer and _norm(prefer) in n else 0,-len(n),str(column)))
    if not found: raise KeyError(f"No se encontró columna con {tokens}")
    return max(found)[2]


def _size_values(df:pd.DataFrame)->tuple[str,dict[str,object]]:
    col=_column(df,"clasificacion","empresa","tamano"); values={}
    for label in SIZES:
        values[label]=next(v for v in df[col].dropna().unique() if _norm(label)[:4] in _norm(v))
    return col,values


def build_metrics(frames:dict[int,pd.DataFrame])->pd.DataFrame:
    rows=[]
    for year,df in frames.items():
        weight=_column(df,"factor","expansion","final"); size_col,size_values=_size_values(df)
        cols={"Internet fijo":_column(df,"satisfech","internet","recodificada"),"Telefonía fija":_column(df,"satisfech","telefonia","fija","recodificada")}
        for service in SERVICES:
            for size in SIZES:
                sub=df.loc[df[size_col].eq(size_values[size]),[cols[service],weight]].copy(); sub.iloc[:,0]=pd.to_numeric(sub.iloc[:,0],errors="coerce"); sub.iloc[:,1]=pd.to_numeric(sub.iloc[:,1],errors="coerce"); sub=sub.dropna()
                denominator=float(sub.iloc[:,1].sum()); numerator=float((sub.iloc[:,0]*sub.iloc[:,1]).sum())
                rows.append({"anio":year,"servicio":service,"tamano":size,"igs":numerator/denominator,"numerador_ponderado":numerator,"denominador_ponderado":denominator})
    return pd.DataFrame(rows)


def validate(data:pd.DataFrame)->float:
    dev=max(abs(round(float(data.loc[(data.anio.eq(y))&(data.servicio.eq(s))&(data.tamano.eq(z)),"igs"].iloc[0]),1)-v) for y in REFERENCE for s,vals in REFERENCE[y].items() for z,v in zip(SIZES,vals))
    if dev>.11: raise ValueError(f"E.3 no reproduce la referencia: desviación {dev:.1f} puntos")
    return dev


def _font(root:Path)->str:
    for n in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        p=root/"assets"/"fonts"/"Noto_Sans"/n
        if p.is_file(): fm.fontManager.addfont(p)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    plt.rcParams.update({"font.family":_font(root)}); fig=plt.figure(figsize=(16,9),facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.035,.06),.93,.86,boxstyle="round,pad=.012,rounding_size=.02",fc=BG,ec="none",transform=fig.transFigure,zorder=-2))
    fig.text(.055,.88,"•",color=CORAL,fontsize=20,va="center"); fig.text(.073,.88,"Figura E.3.",color=TEXT,fontsize=16,fontweight="bold",va="center"); fig.text(.18,.88,"Índice General de Satisfacción por servicio y tamaño de la empresa (2023-2024)",color=TEXT,fontsize=16,va="center")
    for pos,service in zip(([.08,.20,.40,.55],[.53,.20,.40,.55]),SERVICES):
        ax=fig.add_axes(pos); ax.set_facecolor(BG); x=np.arange(3); width=.32
        for i,(year,color) in enumerate(((2023,BLUE if service=="Internet fijo" else CYAN),(2024,TEXT if service=="Internet fijo" else BLUE))):
            vals=[float(data.loc[(data.anio.eq(year))&(data.servicio.eq(service))&(data.tamano.eq(size)),"igs"].iloc[0]) for size in SIZES]
            bars=ax.bar(x+(i-.5)*width,vals,width,color=color,label=str(year),zorder=2)
            for bar,v in zip(bars,vals): ax.text(bar.get_x()+bar.get_width()/2,v+.45,f"{v:.1f}",ha="center",color=TEXT,fontsize=12,fontweight="bold",bbox=dict(boxstyle="round,pad=.25",fc="white",ec="none"))
        ax.set_ylim(0,100); ax.set_xticks(x,SIZES,color=TEXT,fontsize=11); ax.set_yticks([]); ax.tick_params(length=0); ax.spines[:].set_visible(False); ax.set_title(service,color=TEXT,fontsize=18,fontweight="bold",pad=32); ax.legend(ncol=2,loc="upper center",bbox_to_anchor=(.5,1.08),frameon=False,labelcolor=TEXT)
    fig.text(.055,.112,"Fuente:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.101,.112,"IFT, Cuarta Encuesta 2023 y 2024, Usuarios de Servicios de Telecomunicaciones (MiPymes).",color=TEXT,fontsize=9)
    fig.text(.055,.084,"Nota:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.09,.084,"Indicadores medidos en una escala de 0 a 100 puntos.",color=TEXT,fontsize=9)
    output.parent.mkdir(parents=True,exist_ok=True); apply_reference_ui(fig, FIGURE_ID); fig.savefig(output,dpi=200); plt.close(fig)


def generate(context):
    frames={};
    for year,source_id in SOURCES.items(): print(f"  E.3 | Descarga o reutilización de MiPymes {year}"); frames[year]=load_raw(context.acquire_source(source_id)); context.record_source_period(source_id,str(year),"ULTIMO_PUBLICADO" if year==2024 else "HISTORICO")
    data=build_metrics(frames); deviation=validate(data); current=data.loc[data.anio.isin([2023,2024])].copy(); context.write_data_used(current[["anio","servicio","tamano","igs"]])
    for row in current.itertuples(index=False): context.record_calculation(f"igs_{row.anio}_{_norm(row.servicio)}_{_norm(row.tamano)}","sum(IGS recodificado * factor) / sum(factor)",{"anio":row.anio,"servicio":row.servicio,"tamano":row.tamano,"numerador":row.numerador_ponderado,"denominador":row.denominador_ponderado},row.igs,"puntos",1)
    top=current.loc[current.anio.eq(2024)].sort_values("igs",ascending=False).iloc[0]; text_path=context.render_text("f_digital.md.j2",{"resumen":f"En 2024 el IGS más alto fue telefonía fija en empresas medianas ({top.igs:.1f} puntos)."})
    print(f"Validación 2022-2024: desviación máxima {deviation:.1f} puntos"); _plot(current,context.expected_figure_path,context.project_root)
    return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"source_latest_period":PERIOD,"rows_used":len(current)}


def main()->int:
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID); return 0
if __name__=="__main__": raise SystemExit(main())
