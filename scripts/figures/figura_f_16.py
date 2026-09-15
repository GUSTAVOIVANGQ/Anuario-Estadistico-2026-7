"""Figura F.16: medidas que se tomarían ante violencia en Internet, por sexo."""
from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui
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
FIGURE_ID="F.16";SOURCE_ID="ift_tercera_encuesta_usuarios_2023_base";PERIOD="2023";TEXT="#4B4B83";BLUE="#317DA3";SALMON="#F58F82";MINT="#ACDDE0";BACKGROUND="#FBFBF7"
REF_G=[32.7,30.3,30.2,16.8,15.2,12.5,11.8,6.8,6.3];REF_M=[33.2,28.6,29.5,17.0,15.4,10.6,12.8,6.6,6.9];REF_H=[32.1,32.1,31.0,16.6,14.9,14.4,10.6,7.1,5.8]
def _norm(v):
    t=unicodedata.normalize("NFKD",str(v).replace("\xa0"," ").strip().lower());return re.sub(r"\s+"," ","".join(c for c in t if not unicodedata.combining(c)))
def _find(d,*tokens):
    for c in d.columns:
        if all(_norm(t) in _norm(c) for t in tokens):return str(c)
    raise KeyError(tokens)
def _option_col(d,*aliases):
    for alias in aliases:
        for c in d.columns:
            n=_norm(c)
            if "independientemente de si ha sido" in n and _norm(alias) in n:return str(c)
    raise KeyError(aliases)
def _yes(s):return s.astype("string").map(_norm).str.startswith("si",na=False)
def load_raw(path):
    with zipfile.ZipFile(path) as z:
        n=next((n for n in z.namelist() if "int&tv" in _norm(Path(n).name) and n.lower().endswith(".xlsx")),None)
        if not n:raise ValueError("Falta la base Internet y TV")
        return pd.read_excel(BytesIO(z.read(n))),n
def build_metrics(raw):
    w=_find(raw,"factor de expansion final normalizado");internet=_find(raw,"internet fijo en su hogar");gender=_find(raw,"genero");d=raw.copy();d[w]=pd.to_numeric(d[w],errors="coerce");d=d.loc[_yes(d[internet])&d[w].notna()].copy();g=d[gender].astype("string").map(_norm);women=g.str.startswith("mujer",na=False);men=g.str.startswith("hombre",na=False);den=float(d[w].sum());dw=float(d.loc[women,w].sum());dh=float(d.loc[men,w].sum())
    def opt(*aliases):return _yes(d[_option_col(raw,*aliases)])
    authorities=opt("Denunciar ante el Ministerio Público")|opt("Denunciar ante autoridades escolares/centro de trabajo")|opt("Denunciar a Seguridad Pública")|opt("Denunciar ante la Comisión Nacional de Derechos Humanos (CNDH)")|opt("Reportarlo ante la SEDENA")|opt("Denunciar/ Reportarlo (No especifica ante qué autoridades o dónde haría la denuncia/reporte)")
    categories=[("Denunciar ante la Policía Cibernética",opt("Denunciar ante la Policía Cibernética")),("Denunciar a otras autoridades",authorities),("Bloquear a la persona",opt("Bloquear a la persona")),("Denunciar en la plataforma o red social",opt("Denunciar en la plataforma/red social")),("Cerrar la cuenta",opt("Cerrar la cuenta (red social/correo electrónico)")),("Ignorar o no hacer algo",opt("No hacer caso/ Hacer caso omiso/ Ignorar")|opt("Nada")),("Cambiar número de teléfono",opt("Cambiar número de teléfono")),("Acudir con familiares, amistades o pareja",opt("Acudir con algún familiar/amigo/pareja")),("No sabe / no contestó",opt("Ns/Nc"))];rows=[]
    for label,selected in categories:
        ng=float(d.loc[selected,w].sum());nw=float(d.loc[selected&women,w].sum());nh=float(d.loc[selected&men,w].sum());rows.append({"categoria":label,"general_pct":ng/den*100,"mujeres_pct":nw/dw*100,"hombres_pct":nh/dh*100,"num_general":ng,"num_mujeres":nw,"num_hombres":nh})
    return pd.DataFrame(rows),{"den_general":den,"den_mujeres":dw,"den_hombres":dh,"factor":w}
def validate_reference(d):
    diffs=[]
    for r,eg,em,eh in zip(d.itertuples(),REF_G,REF_M,REF_H):diffs += [abs(round(r.general_pct,1)-eg),abs(round(r.mujeres_pct,1)-em),abs(round(r.hombres_pct,1)-eh)]
    m=max(diffs)
    if m>.11:raise ValueError(f"F.16 no reproduce la referencia: {m:.1f} pp")
    return m
def _font(root):
    for n in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        p=root/"assets"/"fonts"/"Noto_Sans"/n
        if p.is_file():fm.fontManager.addfont(p)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"
def _plot(d,out,root):
    plt.rcParams.update({"font.family":_font(root)}); fig,ax=plt.subplots(figsize=(16,8.5)); fig.patch.set_facecolor("white"); ax.set_facecolor("#F8F8FA")
    text="#3c3c3b"; general="#afafaf"; women="#86adae"; men="#335a5c"; x=np.arange(len(d)); width=.26
    b0=ax.bar(x-width,d.general_pct,width,label="General",color=general,edgecolor="none",zorder=2); b1=ax.bar(x,d.mujeres_pct,width,label="Mujeres",color=women,edgecolor="none",zorder=2); b2=ax.bar(x+width,d.hombres_pct,width,label="Hombres",color=men,edgecolor="none",zorder=2)
    ymax=max(float(d.general_pct.max()),float(d.mujeres_pct.max()),float(d.hombres_pct.max()))*1.25; ax.set_ylim(0,ymax); ax.set_xticks(x,d.categoria.astype(str),fontsize=7.8,color=text); ax.tick_params(axis="x",length=0); ax.tick_params(axis="y",labelsize=8.5,colors=text,length=0); ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v,_:f"{v:.0f}%")); ax.grid(axis="y",color="#d1d1d1",linewidth=1,zorder=0); ax.set_axisbelow(True); ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False); ax.spines["left"].set_color("#7c7c7c"); ax.spines["bottom"].set_color("#7c7c7c")
    for bars,color in ((b0,general),(b1,women),(b2,men)):
        for bar in bars:
            h=bar.get_height(); ax.annotate(f"{h:.1f}%",(bar.get_x()+bar.get_width()/2,h),xytext=(0,5),textcoords="offset points",ha="center",fontsize=6.7,color=text,bbox=dict(boxstyle="round,pad=.25,rounding_size=.7",fc="white",ec=color,lw=.8))
    fig.add_artist(patches.Rectangle((.060,.916),.009,.020,transform=fig.transFigure,facecolor="#4a7d75",edgecolor="none")); fig.text(.075,.926,"Figura F.16.",fontsize=14,fontweight="bold",color=text,va="center"); fig.text(.168,.926,"Medidas que se tomarían ante violencia en Internet, por sexo (2023)",fontsize=14,color=text,va="center"); fig.legend(loc="lower center",bbox_to_anchor=(.5,.11),ncol=3,frameon=False,fontsize=10)
    fig.text(.06,.062,"Fuente:",fontsize=8,fontweight="bold",color=text); fig.text(.098,.062,"IFT con información de la Tercera Encuesta 2023, Personas Usuarias de Servicios de Telecomunicaciones.",fontsize=8,color=text); fig.text(.06,.041,"Nota:",fontsize=8,fontweight="bold",color=text); fig.text(.091,.041,"Porcentajes ponderados; las respuestas son de selección múltiple.",fontsize=8,color=text)
    fig.subplots_adjust(left=.06,right=.96,top=.81,bottom=.25); out.parent.mkdir(parents=True,exist_ok=True); apply_reference_ui(fig, FIGURE_ID); fig.savefig(out,dpi=200,facecolor="white"); plt.close(fig)

def generate(context):
    print("  F.16 | Reutilización o descarga de la base oficial IFT");source=context.acquire_source(SOURCE_ID);raw,member=load_raw(source);d,m=build_metrics(raw);dev=validate_reference(d);context.record_source_period(SOURCE_ID,PERIOD,"ULTIMO_COMPATIBLE");context.write_data_used(d[["categoria","general_pct","mujeres_pct","hombres_pct"]])
    for r in d.itertuples(index=False):
        for segment,num,den,value in (("general",r.num_general,m["den_general"],r.general_pct),("mujeres",r.num_mujeres,m["den_mujeres"],r.mujeres_pct),("hombres",r.num_hombres,m["den_hombres"],r.hombres_pct)):context.record_calculation(f"{segment}_{_norm(r.categoria).replace(' ','_')}","sum(factor de respuestas Sí del segmento) / sum(factor del segmento elegible) * 100",{"archivo":member,"numerador":num,"denominador":den},value,"porcentaje",1)
    text=context.render_text("f_digital.md.j2",{"resumen":f"La medida general con mayor porcentaje fue {d.iloc[0].categoria.lower()} ({d.iloc[0].general_pct:.1f}%)."});print(d[["categoria","general_pct","mujeres_pct","hombres_pct"]].to_string(index=False));print(f"Validación: desviación máxima {dev:.1f} pp.");_plot(d,context.expected_figure_path,context.project_root);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":PERIOD,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
