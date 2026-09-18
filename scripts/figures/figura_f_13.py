"""Figura F.13: percepción del riesgo mediante telefonía móvil, por sexo."""
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
FIGURE_ID="F.13";SOURCE_ID="ift_tercera_encuesta_usuarios_2023_base";PERIOD="2023";TEXT="#3c3c3b";BLUE="#335a5c";SALMON="#86adae";BACKGROUND="#F8F8FA"
OPTIONS=[("Menores de edad","Niños, niñas y adolescentes"),("Adultos mayores / Personas de la tercera edad","Personas adultas mayores"),("Mujeres","Mujeres"),("Parientes (familiares)","Parientes (familiares)"),("Hombres","Hombres"),("Personas con discapacidad","Personas con discapacidad"),("Todas las personas son vulnerables","Todas las personas son vulnerables")];REFERENCE_H=[43.7,20.4,12.7,7.2,1.0,.9,22.1];REFERENCE_M=[49.1,20.5,11.9,6.3,2.0,1.2,25.2]
def _norm(v):
    t=unicodedata.normalize("NFKD",str(v).replace("\xa0"," ").strip().lower());return re.sub(r"\s+"," ","".join(c for c in t if not unicodedata.combining(c)))
def _find(d,*tokens):
    for c in d.columns:
        if all(_norm(t) in _norm(c) for t in tokens):return str(c)
    raise KeyError(tokens)
def _opt(d,q,o):
    for c in d.columns:
        if _norm(q) in _norm(c) and _norm(o) in _norm(c):return str(c)
    raise KeyError(o)
def _yes(s):return s.astype("string").map(_norm).str.startswith("si",na=False)
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        n=next((n for n in z.namelist() if "movil" in _norm(Path(n).name) and n.lower().endswith(".xlsx")),None)
        if not n:raise ValueError("Falta la base de Telefonía Móvil")
        return pd.read_excel(BytesIO(z.read(n))),n
def build_metrics(raw):
    w=_find(raw,"calibrador","post-estratificacion");user=_find(raw,"usuario habitual de esta linea");gender=_find(raw,"genero");d=raw.copy();d[w]=pd.to_numeric(d[w],errors="coerce");d=d.loc[_yes(d[user])&d[w].notna()].copy();g=d[gender].astype("string").map(_norm);women=g.str.startswith("mujer",na=False);men=g.str.startswith("hombre",na=False);dw=float(d.loc[women,w].sum());dh=float(d.loc[men,w].sum());rows=[]
    for option,label in OPTIONS:
        yes=_yes(d[_opt(raw,"mayor riesgo",option)]);nw=float(d.loc[yes&women,w].sum());nh=float(d.loc[yes&men,w].sum());rows.append({"categoria":label,"mujeres_pct":nw/dw*100,"hombres_pct":nh/dh*100,"numerador_mujeres":nw,"numerador_hombres":nh})
    return pd.DataFrame(rows),{"factor":w,"denominador_mujeres":dw,"denominador_hombres":dh,"casos":len(d)}
def validate_reference(d):
    diffs=[]
    for r,eh,em in zip(d.itertuples(),REFERENCE_H,REFERENCE_M):diffs += [abs(round(r.hombres_pct,1)-eh),abs(round(r.mujeres_pct,1)-em)]
    m=max(diffs)
    if m>.11:raise ValueError(f"F.13 no reproduce la referencia: {m:.1f} pp")
    return m
def _font(root):
    for n in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        p=root/"assets"/"fonts"/"Noto_Sans"/n
        if p.is_file():fm.fontManager.addfont(p)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"
def _plot(d,out,root):
    plt.rcParams.update({"font.family":_font(root)});fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.055),.95,.87,boxstyle="round,pad=.012,rounding_size=.02",fc=BACKGROUND,ec="none",transform=fig.transFigure,zorder=-2));fig.text(.047,.887,"   ",fontsize=2,va="center",bbox=dict(boxstyle="round,pad=1.6,rounding_size=.2",fc="#4a7d75",ec="none"));fig.text(.064,.887,"Figura F.13.",color=TEXT,fontsize=16,fontweight="bold",va="center");fig.text(.171,.887,"Personas con mayor riesgo de violencia mediante telefonía móvil, por sexo (2023)",color=TEXT,fontsize=16,va="center")
    ax=fig.add_axes([.25,.16,.68,.65]);ordered=d.iloc[::-1].reset_index(drop=True);y=np.arange(len(ordered));h=.34;b1=ax.barh(y-h/2,ordered.hombres_pct,height=h,color=BLUE,label="Hombres");b2=ax.barh(y+h/2,ordered.mujeres_pct,height=h,color=SALMON,label="Mujeres");ax.set_yticks(y,ordered.categoria);ax.set_xlim(0,55);ax.set_xticks(range(0,56,10),[f"{x}%" for x in range(0,56,10)]);ax.tick_params(axis="both",length=0,labelsize=10,colors=TEXT);ax.grid(axis="x",color="#d1d1d1",lw=.8);ax.set_axisbelow(True);ax.spines[:].set_visible(False);ax.set_facecolor(BACKGROUND);ax.legend(loc="lower right",frameon=False,ncol=2,labelcolor=TEXT,fontsize=11)
    for bars in (b1,b2):
        for b in bars:ax.text(b.get_width()+.45,b.get_y()+b.get_height()/2,f"{b.get_width():.1f}%",va="center",fontsize=9,fontweight="bold",color=TEXT,bbox=dict(boxstyle="round,pad=.22,rounding_size=.8",fc="white",ec=b.get_facecolor(),lw=.8))
    fig.text(.047,.09,"Fuente:",color=TEXT,fontsize=9,fontweight="bold");fig.text(.094,.09,"IFT con información de la Tercera Encuesta 2023, Personas Usuarias de Servicios de Telecomunicaciones.",color=TEXT,fontsize=9);fig.text(.047,.067,"Nota:",color=TEXT,fontsize=9,fontweight="bold");fig.text(.081,.067,"Porcentajes ponderados por sexo; respuestas de selección múltiple.",color=TEXT,fontsize=9);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200);plt.close(fig)
def generate(context):
    print("  F.13 | Reutilización o descarga de la base oficial IFT");source=context.acquire_source(SOURCE_ID);raw,member=load_raw(source);d,m=build_metrics(raw);dev=validate_reference(d);context.record_source_period(SOURCE_ID,PERIOD,"ULTIMO_COMPATIBLE");context.write_data_used(d[["categoria","mujeres_pct","hombres_pct"]])
    for r in d.itertuples(index=False):context.record_calculation(f"mujeres_{_norm(r.categoria).replace(' ','_')}","sum(calibrador mujeres Sí) / sum(calibrador mujeres elegibles) * 100",{"archivo":member,"numerador":r.numerador_mujeres,"denominador":m["denominador_mujeres"]},r.mujeres_pct,"porcentaje",1);context.record_calculation(f"hombres_{_norm(r.categoria).replace(' ','_')}","sum(calibrador hombres Sí) / sum(calibrador hombres elegibles) * 100",{"archivo":member,"numerador":r.numerador_hombres,"denominador":m["denominador_hombres"]},r.hombres_pct,"porcentaje",1)
    text=context.render_text("f_digital.md.j2",{"resumen":f"Entre {d.iloc[0].categoria.lower()}, el porcentaje fue {d.iloc[0].mujeres_pct:.1f}% en mujeres y {d.iloc[0].hombres_pct:.1f}% en hombres."});print(d[["categoria","mujeres_pct","hombres_pct"]].to_string(index=False));print(f"Validación: desviación máxima {dev:.1f} pp.");_plot(d,context.expected_figure_path,context.project_root);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":PERIOD,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
