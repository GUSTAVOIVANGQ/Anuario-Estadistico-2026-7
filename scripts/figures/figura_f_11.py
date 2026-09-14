"""Figura F.11: percepción del riesgo de violencia en Internet, por sexo."""
from __future__ import annotations
import re,sys,unicodedata,zipfile
from io import BytesIO
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIGURE_ID="F.11"; SOURCE_ID="ift_tercera_encuesta_usuarios_2023_base"; PERIOD="2023"
TEXT="#4B4B83"; BLUE="#317DA3"; SALMON="#F58F82"; BACKGROUND="#FBFBF7"
OPTIONS=[("Menores de edad","Niños, niñas y adolescentes"),("Mujeres","Mujeres"),("Adultos mayores / Personas de la tercera edad","Personas adultas mayores"),("Personas con discapacidad","Personas con discapacidad"),("Integrantes de la comunidad LGBTIQ+","Personas de la comunidad LGBTIQ+"),("Personas indígenas","Personas indígenas"),("Hombres","Hombres"),("Personas negras o afrodescendientes","Personas afrodescendientes"),("Todas las personas son vulnerables","Todas las personas son vulnerables")]
REFERENCE_H=[54.1,43.5,11.5,9.8,9.8,5.5,5.6,4.3,29.8]; REFERENCE_M=[58.4,43.0,10.1,10.1,8.3,5.1,4.4,3.1,28.4]

def _norm(v):
    t=unicodedata.normalize("NFKD",str(v).replace("\xa0"," ").strip().lower());return re.sub(r"\s+"," ","".join(c for c in t if not unicodedata.combining(c)))
def _find(frame,*tokens):
    wanted=[_norm(t) for t in tokens]
    for c in frame.columns:
        if all(t in _norm(c) for t in wanted): return str(c)
    raise KeyError(tokens)
def _opt(frame,q,option):
    for c in frame.columns:
        if _norm(q) in _norm(c) and _norm(option) in _norm(c): return str(c)
    raise KeyError(option)
def _yes(s): return s.astype("string").map(_norm).str.startswith("si",na=False)
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        name=next((n for n in z.namelist() if "int&tv" in _norm(Path(n).name) and n.lower().endswith(".xlsx")),None)
        if not name: raise ValueError("Falta la base Internet y TV")
        return pd.read_excel(BytesIO(z.read(name))),name
def build_metrics(raw):
    w=_find(raw,"factor de expansion final normalizado"); internet=_find(raw,"internet fijo en su hogar"); gender=_find(raw,"genero")
    d=raw.copy();d[w]=pd.to_numeric(d[w],errors="coerce");d=d.loc[_yes(d[internet])&d[w].notna()].copy();g=d[gender].astype("string").map(_norm);women=g.str.startswith("mujer",na=False);men=g.str.startswith("hombre",na=False);dw=float(d.loc[women,w].sum());dh=float(d.loc[men,w].sum());rows=[]
    for option,label in OPTIONS:
        selected=_yes(d[_opt(raw,"mayor riesgo",option)]);nw=float(d.loc[selected&women,w].sum());nh=float(d.loc[selected&men,w].sum());rows.append({"categoria":label,"mujeres_pct":nw/dw*100,"hombres_pct":nh/dh*100,"numerador_mujeres":nw,"numerador_hombres":nh})
    return pd.DataFrame(rows),{"factor":w,"denominador_mujeres":dw,"denominador_hombres":dh,"casos":len(d)}
def validate_reference(data):
    diffs=[]
    for r,eh,em in zip(data.itertuples(),REFERENCE_H,REFERENCE_M): diffs += [abs(round(r.hombres_pct,1)-eh),abs(round(r.mujeres_pct,1)-em)]
    maximum=max(diffs)
    if maximum>.11: raise ValueError(f"F.11 no reproduce la referencia: {maximum:.1f} pp")
    return maximum
def _font(root):
    for n in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        p=root/"assets"/"fonts"/"Noto_Sans"/n
        if p.is_file(): fm.fontManager.addfont(p)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"
def _plot(data,out,root):
    plt.rcParams.update({"font.family":_font(root)});fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.055),.95,.87,boxstyle="round,pad=.012,rounding_size=.02",fc=BACKGROUND,ec="none",transform=fig.transFigure,zorder=-2));fig.text(.047,.887,"•",color=SALMON,fontsize=20,va="center");fig.text(.064,.887,"Figura F.11.",color=TEXT,fontsize=16,fontweight="bold",va="center");fig.text(.171,.887,"Personas con mayor riesgo de violencia en Internet, por sexo (2023)",color=TEXT,fontsize=16,va="center")
    ax=fig.add_axes([.23,.16,.70,.65]);ordered=data.iloc[::-1].reset_index(drop=True);y=np.arange(len(ordered));h=.34;b1=ax.barh(y-h/2,ordered.hombres_pct,height=h,color=BLUE,label="Hombres");b2=ax.barh(y+h/2,ordered.mujeres_pct,height=h,color=SALMON,label="Mujeres");ax.set_yticks(y,ordered.categoria);ax.set_xlim(0,65);ax.set_xticks(np.arange(0,66,10),[f"{x}%" for x in range(0,66,10)]);ax.tick_params(axis="both",length=0,labelsize=10,colors=TEXT);ax.grid(axis="x",color="#DCEBE9",lw=.8);ax.set_axisbelow(True);ax.spines[:].set_visible(False);ax.set_facecolor(BACKGROUND);ax.legend(loc="lower right",frameon=False,ncol=2,labelcolor=TEXT,fontsize=11)
    for bars in (b1,b2):
        for bar in bars: ax.text(bar.get_width()+.5,bar.get_y()+bar.get_height()/2,f"{bar.get_width():.1f}%",va="center",fontsize=9,fontweight="bold",color=TEXT)
    fig.text(.047,.09,"Fuente:",color=TEXT,fontsize=9,fontweight="bold");fig.text(.094,.09,"IFT con información de la Tercera Encuesta 2023, Personas Usuarias de Servicios de Telecomunicaciones.",color=TEXT,fontsize=9);fig.text(.047,.067,"Nota:",color=TEXT,fontsize=9,fontweight="bold");fig.text(.081,.067,"Porcentajes ponderados por sexo; respuestas de selección múltiple.",color=TEXT,fontsize=9);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200);plt.close(fig)
def generate(context):
    print("  F.11 | Reutilización o descarga de la base oficial IFT");source=context.acquire_source(SOURCE_ID);raw,member=load_raw(source);data,meta=build_metrics(raw);deviation=validate_reference(data);context.record_source_period(SOURCE_ID,PERIOD,"ULTIMO_COMPATIBLE");context.write_data_used(data[["categoria","mujeres_pct","hombres_pct"]])
    for r in data.itertuples(index=False):
        context.record_calculation(f"mujeres_{_norm(r.categoria).replace(' ','_')}","sum(factor de mujeres con respuesta Sí) / sum(factor de mujeres elegibles) * 100",{"archivo":member,"numerador":r.numerador_mujeres,"denominador":meta["denominador_mujeres"]},r.mujeres_pct,"porcentaje",1);context.record_calculation(f"hombres_{_norm(r.categoria).replace(' ','_')}","sum(factor de hombres con respuesta Sí) / sum(factor de hombres elegibles) * 100",{"archivo":member,"numerador":r.numerador_hombres,"denominador":meta["denominador_hombres"]},r.hombres_pct,"porcentaje",1)
    text=context.render_text("f_digital.md.j2",{"resumen":f"El mayor porcentaje correspondió a {data.iloc[0].categoria.lower()}: {data.iloc[0].mujeres_pct:.1f}% en mujeres y {data.iloc[0].hombres_pct:.1f}% en hombres."});print(data[["categoria","mujeres_pct","hombres_pct"]].to_string(index=False));print(f"Validación: desviación máxima {deviation:.1f} pp.");_plot(data,context.expected_figure_path,context.project_root);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":PERIOD,"rows_used":len(data)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__": raise SystemExit(main())
