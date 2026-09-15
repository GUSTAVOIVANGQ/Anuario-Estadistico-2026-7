"""Figura E.8: beneficios de contar con una aplicación móvil, 2024."""
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

FIGURE_ID,PERIOD="E.8","2024"; SOURCES={2023:"ift_mipymes_2023_base",2024:"ift_mipymes_2024_base"}; SIZES=["General","Micro","Pequeña","Mediana"]
BENEFITS=[("Contacto más rápido con clientes",["contacto","clientes"]),("Solicitud de pedidos más ágil",["solicitud","pedidos"]),("Mayor competitividad en el mercado",["competitividad"]),("Facilita el control de ventas",["control","ventas"])]
REFERENCE_2024={"Contacto más rápido con clientes":[60.1,59.9,62.5,60.8],"Solicitud de pedidos más ágil":[39.7,39.3,44.8,40.1],"Mayor competitividad en el mercado":[37.8,38.2,33.7,25.9],"Facilita el control de ventas":[23.7,24.5,14.5,23.1]}
TEXT,BG,CORAL="#4B4B7D","#EEF6F4","#F48D7E"; COLORS=["#327BA0","#4F5082","#F48D7E","#F0535A"]


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
        for benefit,tokens in BENEFITS:
            col=_find(df,*tokens,reject=["pagina","correo","banca","nube"])
            for size in SIZES:
                sub=df if size=="General" else df.loc[df[size_col].eq(sizes[size])]; valid=sub[[col,weight]].dropna(); weights=pd.to_numeric(valid[weight],errors="coerce").fillna(0); denominator=float(weights.sum()); numerator=float(weights.loc[_yes(valid[col])].sum()); rows.append({"anio":year,"beneficio":benefit,"tamano":size,"porcentaje":numerator/denominator*100,"numerador_ponderado":numerator,"denominador_ponderado":denominator,"columna":col})
    return pd.DataFrame(rows)


def validate(data:pd.DataFrame)->float:
    dev=max(abs(round(float(data.loc[(data.anio.eq(2024))&(data.beneficio.eq(benefit))&(data.tamano.eq(size)),"porcentaje"].iloc[0]),1)-value) for benefit,vals in REFERENCE_2024.items() for size,value in zip(SIZES,vals))
    if dev>.11: raise ValueError(f"E.8 no reproduce la referencia oficial 2024: {dev:.1f} pp")
    return dev


def _font(root:Path)->str:
    for n in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        p=root/"assets"/"fonts"/"Noto_Sans"/n
        if p.is_file(): fm.fontManager.addfont(p)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    plt.rcParams.update({"font.family":_font(root)}); fig=plt.figure(figsize=(16,9),facecolor="white"); fig.text(.045,.90,"•",color=CORAL,fontsize=20,va="center"); fig.text(.063,.90,"Figura E.8.",color=TEXT,fontsize=16,fontweight="bold",va="center"); fig.text(.17,.90,"Beneficios de contar con una aplicación móvil para la empresa o negocio (2024)",color=TEXT,fontsize=16,va="center"); current=data.loc[data.anio.eq(2024)]
    for i,(benefit,_) in enumerate(BENEFITS):
        left=.045+i*.238; fig.add_artist(patches.FancyBboxPatch((left,.18),.215,.62,boxstyle="round,pad=.008,rounding_size=.018",fc=BG,ec="#7E82A8",lw=.8,transform=fig.transFigure,zorder=-2)); vals=[float(current.loc[(current.beneficio.eq(benefit))&(current.tamano.eq(s)),"porcentaje"].iloc[0]) for s in SIZES]
        fig.text(left+.1075,.742,f"{vals[0]:.1f}%",ha="center",color=TEXT,fontsize=24,fontweight="bold",bbox=dict(boxstyle="round,pad=.55",fc="white",ec="none")); fig.text(left+.1075,.64,textwrap.fill(benefit,23),ha="center",color=TEXT,fontsize=12,fontweight="bold")
        ax=fig.add_axes([left+.028,.25,.16,.31]); x=np.arange(3); bars=ax.bar(x,vals[1:],color=COLORS[i],width=.56); ax.set_ylim(0,75); ax.set_xticks(x,SIZES[1:],fontsize=8,color=TEXT); ax.set_yticks([]); ax.tick_params(length=0); ax.spines[:].set_visible(False); ax.set_facecolor(BG)
        for bar,v in zip(bars,vals[1:]): ax.text(bar.get_x()+bar.get_width()/2,v+2,f"{v:.1f}%",ha="center",fontsize=9,color=TEXT,fontweight="bold")
    fig.text(.045,.105,"Fuente:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.091,.105,"IFT, Cuarta Encuesta 2024, Usuarios de Servicios de Telecomunicaciones (MiPymes).",color=TEXT,fontsize=9)
    fig.text(.045,.077,"Nota:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.08,.077,"Respuesta espontánea y múltiple, por lo que la suma no da 100%.",color=TEXT,fontsize=9)
    output.parent.mkdir(parents=True,exist_ok=True); apply_reference_ui(fig, FIGURE_ID); fig.savefig(output,dpi=200); plt.close(fig)


def generate(context):
    frames={}
    for year,source in SOURCES.items(): print(f"  E.8 | Descarga o reutilización de MiPymes {year}"); frames[year]=load_raw(context.acquire_source(source)); context.record_source_period(source,str(year),"ULTIMO_PUBLICADO" if year==2024 else "HISTORICO")
    data=build_metrics(frames); deviation=validate(data); current=data.loc[data.anio.eq(2024)].copy(); context.write_data_used(current[["anio","beneficio","tamano","porcentaje"]])
    for row in current.itertuples(index=False): context.record_calculation(f"app_{_norm(row.beneficio)}_{_norm(row.tamano)}","sum(factor donde respuesta Sí) / sum(factor con respuesta) * 100",{"beneficio":row.beneficio,"tamano":row.tamano,"numerador":row.numerador_ponderado,"denominador":row.denominador_ponderado,"columna":row.columna},row.porcentaje,"porcentaje",1)
    top=current.sort_values("porcentaje",ascending=False).iloc[0]; text_path=context.render_text("f_digital.md.j2",{"resumen":f"El beneficio más señalado fue {top.beneficio.lower()} ({top.porcentaje:.1f}% en {top.tamano.lower()})."}); print(f"Validación 2024: desviación máxima {deviation:.1f} pp"); _plot(current,context.expected_figure_path,context.project_root)
    return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"source_latest_period":PERIOD,"rows_used":len(current)}


def main()->int:
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID); return 0
if __name__=="__main__": raise SystemExit(main())
