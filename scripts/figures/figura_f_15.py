"""Figura F.15: acciones para prevenir la violencia en Internet, por sexo."""
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
FIGURE_ID="F.15";SOURCE_ID="ift_tercera_encuesta_usuarios_2023_base";PERIOD="2023";TEXT="#4B4B83";BLUE="#317DA3";SALMON="#F58F82";MINT="#ACDDE0";BACKGROUND="#FBFBF7"
OPTIONS=[("Evitar compartir información personal","Evitar compartir información personal"),("Evitar compartir contraseñas de sus dispositivos y/o aplicaciones","Evitar compartir contraseñas"),("Revisar un perfil antes de aceptarlo","Revisar un perfil antes de aceptarlo"),("Ser más precavido al abrir links o archivos recibidos","Ser más precavido al abrir vínculos o archivos"),("Evitar subir información donde sea fácil ubicarle a usted o a su familia","Evitar publicar información de ubicación"),("Redes sociales privadas solo para familiares y/o amistades","Mantener redes sociales privadas"),("Publicar fotos y/o videos con restricciones para no recibir acoso y evitar comentarios","Restringir fotos o videos"),("Cuestionarse sobre el contenido que publicará","Cuestionar el contenido antes de publicarlo"),("Evitar ser muy activo en redes sociales","Limitar la actividad en redes sociales"),("Comentar con otras personas sobre lo que sucede y ve en redes sociales","Comentar con otras personas lo que sucede")]
REF_G=[90.3,89.5,87.6,86.7,86.0,82.0,80.9,74.4,71.9,71.3];REF_M=[91.2,91.5,90.0,87.5,87.6,84.6,82.6,76.1,71.9,71.5];REF_H=[89.3,87.3,85.1,85.8,84.3,79.2,79.0,72.6,71.9,71.0]
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
        n=next((n for n in z.namelist() if "int&tv" in _norm(Path(n).name) and n.lower().endswith(".xlsx")),None)
        if not n:raise ValueError("Falta la base Internet y TV")
        return pd.read_excel(BytesIO(z.read(n))),n
def build_metrics(raw):
    w=_find(raw,"factor de expansion final normalizado");internet=_find(raw,"internet fijo en su hogar");gender=_find(raw,"genero");d=raw.copy();d[w]=pd.to_numeric(d[w],errors="coerce");d=d.loc[_yes(d[internet])&d[w].notna()].copy();g=d[gender].astype("string").map(_norm);women=g.str.startswith("mujer",na=False);men=g.str.startswith("hombre",na=False);den=float(d[w].sum());dw=float(d.loc[women,w].sum());dh=float(d.loc[men,w].sum());rows=[]
    for option,label in OPTIONS:
        yes=_yes(d[_opt(raw,"acciones realiza para protegerse o prevenir",option)]);ng=float(d.loc[yes,w].sum());nw=float(d.loc[yes&women,w].sum());nh=float(d.loc[yes&men,w].sum());rows.append({"categoria":label,"general_pct":ng/den*100,"mujeres_pct":nw/dw*100,"hombres_pct":nh/dh*100,"num_general":ng,"num_mujeres":nw,"num_hombres":nh})
    return pd.DataFrame(rows),{"den_general":den,"den_mujeres":dw,"den_hombres":dh,"factor":w}
def validate_reference(d):
    diffs=[]
    for r,eg,em,eh in zip(d.itertuples(),REF_G,REF_M,REF_H):diffs += [abs(round(r.general_pct,1)-eg),abs(round(r.mujeres_pct,1)-em),abs(round(r.hombres_pct,1)-eh)]
    m=max(diffs)
    if m>.11:raise ValueError(f"F.15 no reproduce la referencia: {m:.1f} pp")
    return m
def _font(root):
    for n in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        p=root/"assets"/"fonts"/"Noto_Sans"/n
        if p.is_file():fm.fontManager.addfont(p)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"
def _plot(d,out,root):
    plt.rcParams.update({"font.family":_font(root)});fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.055),.95,.87,boxstyle="round,pad=.012,rounding_size=.02",fc=BACKGROUND,ec="none",transform=fig.transFigure,zorder=-2));fig.text(.047,.887,"•",color=SALMON,fontsize=20,va="center");fig.text(.064,.887,"Figura F.15.",color=TEXT,fontsize=16,fontweight="bold",va="center");fig.text(.171,.887,"Acciones para protegerse o prevenir la violencia en Internet, por sexo (2023)",color=TEXT,fontsize=16,va="center")
    ax=fig.add_axes([.29,.16,.65,.66]);ordered=d.iloc[::-1].reset_index(drop=True);y=np.arange(len(ordered));h=.23;b0=ax.barh(y-h,ordered.general_pct,height=h,color=MINT,label="General");b1=ax.barh(y,ordered.mujeres_pct,height=h,color=SALMON,label="Mujeres");b2=ax.barh(y+h,ordered.hombres_pct,height=h,color=BLUE,label="Hombres");ax.set_yticks(y,ordered.categoria);ax.set_xlim(0,102);ax.set_xticks(range(0,101,20),[f"{x}%" for x in range(0,101,20)]);ax.tick_params(axis="both",length=0,labelsize=9.5,colors=TEXT);ax.grid(axis="x",color="#DCEBE9",lw=.8);ax.set_axisbelow(True);ax.spines[:].set_visible(False);ax.set_facecolor(BACKGROUND);ax.legend(loc="lower right",frameon=False,ncol=3,labelcolor=TEXT,fontsize=10)
    for bars in (b0,b1,b2):
        for b in bars:ax.text(b.get_width()+.35,b.get_y()+b.get_height()/2,f"{b.get_width():.1f}%",va="center",fontsize=7.8,color=TEXT)
    fig.text(.047,.09,"Fuente:",color=TEXT,fontsize=9,fontweight="bold");fig.text(.094,.09,"IFT con información de la Tercera Encuesta 2023, Personas Usuarias de Servicios de Telecomunicaciones.",color=TEXT,fontsize=9);fig.text(.047,.067,"Nota:",color=TEXT,fontsize=9,fontweight="bold");fig.text(.081,.067,"Porcentajes ponderados; las respuestas son de selección múltiple.",color=TEXT,fontsize=9);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200);plt.close(fig)
def generate(context):
    print("  F.15 | Reutilización o descarga de la base oficial IFT");source=context.acquire_source(SOURCE_ID);raw,member=load_raw(source);d,m=build_metrics(raw);dev=validate_reference(d);context.record_source_period(SOURCE_ID,PERIOD,"ULTIMO_COMPATIBLE");context.write_data_used(d[["categoria","general_pct","mujeres_pct","hombres_pct"]])
    for r in d.itertuples(index=False):
        for segment,num,den,value in (("general",r.num_general,m["den_general"],r.general_pct),("mujeres",r.num_mujeres,m["den_mujeres"],r.mujeres_pct),("hombres",r.num_hombres,m["den_hombres"],r.hombres_pct)):context.record_calculation(f"{segment}_{_norm(r.categoria).replace(' ','_')}","sum(factor de respuestas Sí del segmento) / sum(factor del segmento elegible) * 100",{"archivo":member,"numerador":num,"denominador":den},value,"porcentaje",1)
    text=context.render_text("f_digital.md.j2",{"resumen":f"La acción general más frecuente fue {d.iloc[0].categoria.lower()} ({d.iloc[0].general_pct:.1f}%)."});print(d[["categoria","general_pct","mujeres_pct","hombres_pct"]].to_string(index=False));print(f"Validación: desviación máxima {dev:.1f} pp.");_plot(d,context.expected_figure_path,context.project_root);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":PERIOD,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
