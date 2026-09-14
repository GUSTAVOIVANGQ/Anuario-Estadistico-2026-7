"""Figura F.12: percepción del riesgo de violencia mediante telefonía móvil."""
from __future__ import annotations
import re,sys,unicodedata,zipfile
from io import BytesIO
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd

FIGURE_ID="F.12";SOURCE_ID="ift_tercera_encuesta_usuarios_2023_base";PERIOD="2023";TEXT="#4B4B83";BLUE="#317DA3";SALMON="#F58F82";BACKGROUND="#FBFBF7"
OPTIONS=[("Menores de edad","Niños, niñas y adolescentes"),("Adultos mayores / Personas de la tercera edad","Personas adultas mayores"),("Mujeres","Mujeres"),("Parientes (familiares)","Parientes (familiares)"),("Hombres","Hombres"),("Personas con discapacidad","Personas con discapacidad"),("Todas las personas son vulnerables","Todas las personas son vulnerables")];REFERENCE=[46.5,20.5,12.2,6.7,1.5,1.0,23.8]
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
    w=_find(raw,"calibrador","post-estratificacion");user=_find(raw,"usuario habitual de esta linea");d=raw.copy();d[w]=pd.to_numeric(d[w],errors="coerce");d=d.loc[_yes(d[user])&d[w].notna()].copy();den=float(d[w].sum());rows=[]
    for option,label in OPTIONS:
        yes=_yes(d[_opt(raw,"mayor riesgo",option)]);num=float(d.loc[yes,w].sum());rows.append({"categoria":label,"porcentaje":num/den*100,"numerador_ponderado":num})
    all_row=next(r for r in rows if r["categoria"]=="Todas las personas son vulnerables");ordered=sorted((r for r in rows if r is not all_row),key=lambda r:r["porcentaje"],reverse=True)+[all_row];return pd.DataFrame(ordered),{"factor":w,"denominador":den,"casos":len(d)}
def validate_reference(d):
    actual={r.categoria:r.porcentaje for r in d.itertuples()};expected=dict(zip([l for _,l in OPTIONS],REFERENCE));m=max(abs(round(actual[k],1)-v) for k,v in expected.items())
    if m>.11:raise ValueError(f"F.12 no reproduce la referencia: {m:.1f} pp")
    return m
def _font(root):
    for n in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        p=root/"assets"/"fonts"/"Noto_Sans"/n
        if p.is_file():fm.fontManager.addfont(p)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"
def _plot(d,out,root):
    plt.rcParams.update({"font.family":_font(root)});fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.055),.95,.87,boxstyle="round,pad=.012,rounding_size=.02",fc=BACKGROUND,ec="none",transform=fig.transFigure,zorder=-2));fig.text(.047,.887,"•",color=SALMON,fontsize=20,va="center");fig.text(.064,.887,"Figura F.12.",color=TEXT,fontsize=16,fontweight="bold",va="center");fig.text(.171,.887,"Personas con mayor riesgo de violencia a través del teléfono móvil (2023)",color=TEXT,fontsize=16,va="center")
    ax=fig.add_axes([.16,.19,.78,.60]);bars=ax.bar(range(len(d)),d.porcentaje,color=BLUE,width=.58);ax.set_xticks(range(len(d)),[x.replace(" ","\n",1) if len(x)>20 else x for x in d.categoria],fontsize=9,color=TEXT);ax.set_ylim(0,max(52,d.porcentaje.max()*1.18));ax.set_yticks([]);ax.spines[:].set_visible(False);ax.set_facecolor(BACKGROUND)
    for bar,v in zip(bars,d.porcentaje):ax.text(bar.get_x()+bar.get_width()/2,v+1,f"{v:.1f}%",ha="center",fontsize=11,fontweight="bold",color=TEXT,bbox=dict(boxstyle="round,pad=.22",fc="white",ec="none"))
    fig.text(.047,.09,"Fuente:",color=TEXT,fontsize=9,fontweight="bold");fig.text(.094,.09,"IFT con información de la Tercera Encuesta 2023, Personas Usuarias de Servicios de Telecomunicaciones.",color=TEXT,fontsize=9);fig.text(.047,.067,"Nota:",color=TEXT,fontsize=9,fontweight="bold");fig.text(.081,.067,"Porcentajes ponderados; las respuestas son de selección múltiple y no suman 100%.",color=TEXT,fontsize=9);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=200);plt.close(fig)
def generate(context):
    print("  F.12 | Reutilización o descarga de la base oficial IFT");source=context.acquire_source(SOURCE_ID);raw,member=load_raw(source);d,m=build_metrics(raw);dev=validate_reference(d);context.record_source_period(SOURCE_ID,PERIOD,"ULTIMO_COMPATIBLE");context.write_data_used(d[["categoria","porcentaje"]])
    for r in d.itertuples(index=False):context.record_calculation(f"riesgo_{_norm(r.categoria).replace(' ','_')}","sum(calibrador de casos Sí) / sum(calibrador de personas usuarias) * 100",{"archivo":member,"numerador":r.numerador_ponderado,"denominador":m["denominador"]},r.porcentaje,"porcentaje",1)
    text=context.render_text("f_digital.md.j2",{"resumen":f"La categoría con mayor porcentaje fue {d.iloc[0].categoria.lower()} ({d.iloc[0].porcentaje:.1f}%)."});print(d[["categoria","porcentaje"]].to_string(index=False));print(f"Validación: desviación máxima {dev:.1f} pp.");_plot(d,context.expected_figure_path,context.project_root);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":PERIOD,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
