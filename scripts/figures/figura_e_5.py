"""Figura E.5: beneficios percibidos de Internet y telefonía fija, 2024."""
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

FIGURE_ID,PERIOD="E.5","2024"; SOURCES={2023:"ift_mipymes_2023_base",2024:"ift_mipymes_2024_base"}; SIZES=["Micro","Pequeña","Mediana"]
BENEFITS=[("Más gente conoce la empresa",["mas","gente","conoce","empresa"]),("Están más cerca de sus clientes/consumidores",["cerca","consumidores"]),("Hay más ventas/clientes",["mas","ventas","clientes"]),("Disminución de costos al encontrar mejores proveedores",["costos","proveedores"]),("Desarrollar nuevos productos o servicios",["desarroll","nuevos","productos","servicios"]),("Entrega más rápida o menos costosa",["entrega","productos","servicios","rapida"]),("Los empleados hacen más en el mismo tiempo",["empleados","mismo","tiempo"])]
REFERENCE_2023={"Micro":{"Internet fijo":[7.6,7.4,7.4,6.7,6.5,6.4,6.0],"Telefonía fija":[6.4,6.8,6.4,6.1,5.8,6.0,5.4]},"Pequeña":{"Internet fijo":[8.1,7.9,7.8,7.1,6.9,7.0,6.8],"Telefonía fija":[7.3,7.4,7.1,6.8,6.5,6.6,6.1]},"Mediana":{"Internet fijo":[8.3,8.1,8.0,7.4,7.4,7.6,7.3],"Telefonía fija":[7.2,7.5,7.1,6.7,6.5,6.8,6.4]}}
TEXT,BG,CORAL,BLUE,CYAN="#3c3c3b","#F8F8FA","#4a7d75","#335a5c","#86adae"


def _norm(v:object)->str:
    t=unicodedata.normalize("NFKD",str(v).replace("\xa0"," ").lower()); return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9]+"," ","".join(c for c in t if not unicodedata.combining(c)))).strip()


def load_raw(path:Path)->pd.DataFrame:
    with zipfile.ZipFile(path) as z:
        ns=[n for n in z.namelist() if n.lower().endswith((".xlsx",".xls")) and "diccionario" not in _norm(n)]; n=max(ns,key=lambda x:z.getinfo(x).file_size); return pd.read_excel(BytesIO(z.read(n)))


def _find(df:pd.DataFrame,tokens:list[str],*,must:list[str]=[],reject:list[str]=[])->str:
    found=[str(c) for c in df.columns if all(_norm(t) in _norm(c) for t in tokens+must) and not any(_norm(t) in _norm(c) for t in reject)]
    if not found: raise KeyError(f"No se encontró columna: {tokens}, {must}")
    return min(found,key=lambda c:len(_norm(c)))


def _basics(df:pd.DataFrame):
    weight=_find(df,["factor","expansion","final"]); size_col=_find(df,["clasificacion","empresa","tamano"]); sizes={s:next(v for v in df[size_col].dropna().unique() if _norm(s)[:4] in _norm(v)) for s in SIZES}; return weight,size_col,sizes


def _weighted_mean(df:pd.DataFrame,value:str,weight:str)->tuple[float,float,float]:
    tmp=df[[value,weight]].copy(); tmp[value]=pd.to_numeric(tmp[value],errors="coerce"); tmp[weight]=pd.to_numeric(tmp[weight],errors="coerce"); tmp=tmp.dropna(); den=float(tmp[weight].sum()); num=float((tmp[value]*tmp[weight]).sum()); return num/den,num,den


def build_metrics(frames:dict[int,pd.DataFrame])->pd.DataFrame:
    rows=[]
    for year,df in frames.items():
        weight,size_col,sizes=_basics(df)
        for benefit,tokens in BENEFITS:
            columns={"Internet fijo":_find(df,tokens,must=["internet"],reject=["telefon"]),"Telefonía fija":_find(df,tokens,must=["telefon"])}
            for size in SIZES:
                sub=df.loc[df[size_col].eq(sizes[size])]
                for service,column in columns.items():
                    value,num,den=_weighted_mean(sub,column,weight); rows.append({"anio":year,"tamano":size,"beneficio":benefit,"servicio":service,"promedio":value,"numerador_ponderado":num,"denominador_ponderado":den,"columna":column})
    return pd.DataFrame(rows)


def validate(data:pd.DataFrame)->float:
    dev=max(abs(round(float(data.loc[(data.anio.eq(2023))&(data.tamano.eq(size))&(data.servicio.eq(service))&(data.beneficio.eq(benefit)),"promedio"].iloc[0]),1)-value) for size in SIZES for service,vals in REFERENCE_2023[size].items() for (benefit,_),value in zip(BENEFITS,vals))
    if dev>.11: raise ValueError(f"E.5 no reproduce la referencia 2023: {dev:.1f} puntos")
    return dev


def _font(root:Path)->str:
    for n in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        p=root/"assets"/"fonts"/"Noto_Sans"/n
        if p.is_file(): fm.fontManager.addfont(p)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    plt.rcParams.update({"font.family":_font(root)}); fig=plt.figure(figsize=(16,9),facecolor="white"); fig.add_artist(patches.FancyBboxPatch((.025,.055),.95,.87,boxstyle="round,pad=.012,rounding_size=.02",fc=BG,ec="none",transform=fig.transFigure,zorder=-2))
    fig.add_artist(patches.Rectangle((.045,.881),.009,.018,transform=fig.transFigure,fc=CORAL,ec="none")); fig.text(.063,.89,"Figura E.5.",color=TEXT,fontsize=16,fontweight="bold",va="center"); fig.text(.17,.89,"Beneficios de contar con Internet fijo y/o telefonía fija (2024)",color=TEXT,fontsize=16,va="center")
    current=data.loc[data.anio.eq(2024)]; y=np.arange(len(BENEFITS)); labels=[textwrap.fill(x[0],30) for x in BENEFITS]
    for i,(size,left) in enumerate(zip(SIZES,(.19,.47,.75))):
        ax=fig.add_axes([left,.20,.22,.58]); ax.set_facecolor(BG); a=current.loc[(current.tamano.eq(size))&(current.servicio.eq("Internet fijo")),"promedio"].to_numpy(); b=current.loc[(current.tamano.eq(size))&(current.servicio.eq("Telefonía fija")),"promedio"].to_numpy(); ax.barh(y+.18,a,.34,color=CYAN,label="Internet fijo"); ax.barh(y-.18,b,.34,color=BLUE,label="Telefonía fija")
        for yy,v in zip(y+.18,a): ax.text(v+.08,yy,f"{v:.1f}",va="center",color=TEXT,fontsize=9,fontweight="bold")
        for yy,v in zip(y-.18,b): ax.text(v+.08,yy,f"{v:.1f}",va="center",color=TEXT,fontsize=9,fontweight="bold")
        ax.set_xlim(0,10); ax.set_xticks([]); ax.set_yticks(y,labels if i==0 else []); ax.invert_yaxis(); ax.tick_params(axis="y",length=0,labelsize=8.5,colors=TEXT,pad=8); ax.spines[:].set_visible(False); ax.set_title(size,color=TEXT,fontweight="bold",fontsize=14,pad=12)
    fig.legend(
        handles=[patches.Patch(color=CYAN,label="Internet fijo"),patches.Patch(color=BLUE,label="Telefonía fija")],
        loc="lower center",bbox_to_anchor=(.5,.135),ncol=2,frameon=False,fontsize=8.5,
    )
    fig.text(.045,.105,"Fuente:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.091,.105,"IFT, Cuarta Encuesta 2024, Usuarios de Servicios de Telecomunicaciones (MiPymes).",color=TEXT,fontsize=9)
    fig.text(.045,.077,"Nota:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.08,.077,"Promedios ponderados en escala de 0 a 10; se excluyen No sabe/No contestó.",color=TEXT,fontsize=9)
    output.parent.mkdir(parents=True,exist_ok=True); apply_reference_ui(fig, FIGURE_ID); fig.savefig(output,dpi=200); plt.close(fig)


def generate(context):
    frames={}
    for year,source in SOURCES.items(): print(f"  E.5 | Descarga o reutilización de MiPymes {year}"); frames[year]=load_raw(context.acquire_source(source)); context.record_source_period(source,str(year),"ULTIMO_PUBLICADO" if year==2024 else "HISTORICO")
    data=build_metrics(frames); deviation=validate(data); current=data.loc[data.anio.eq(2024)].copy(); context.write_data_used(current[["anio","tamano","beneficio","servicio","promedio"]])
    for row in current.itertuples(index=False): context.record_calculation(f"beneficio_{_norm(row.tamano)}_{_norm(row.servicio)}_{current.index.get_loc(row.Index) if hasattr(row,'Index') else _norm(row.beneficio)}","sum(respuesta * factor) / sum(factor)",{"tamano":row.tamano,"servicio":row.servicio,"beneficio":row.beneficio,"numerador":row.numerador_ponderado,"denominador":row.denominador_ponderado,"columna":row.columna},row.promedio,"puntos",1)
    top=current.sort_values("promedio",ascending=False).iloc[0]; text_path=context.render_text("f_digital.md.j2",{"resumen":f"El promedio más alto fue {top.beneficio.lower()} para {top.servicio.lower()} en empresas {top.tamano.lower()}s ({top.promedio:.1f})."})
    print(f"Validación 2023: desviación máxima {deviation:.1f} puntos"); _plot(current,context.expected_figure_path,context.project_root)
    return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"source_latest_period":PERIOD,"rows_used":len(current)}


def main()->int:
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID); return 0
if __name__=="__main__": raise SystemExit(main())
