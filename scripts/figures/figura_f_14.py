"""Figura F.14: medidas cualitativas de prevención y protección digital."""
from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui
import sys
import textwrap
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd
FIGURE_ID="F.14";SOURCE_ID="ift_tercera_encuesta_usuarios_2023_pdf";PERIOD="2023";TEXT="#4B4B83";BLUE="#317DA3";SALMON="#F58F82";MINT="#ACDDE0";BACKGROUND="#FBFBF7"
PREVENTION=["Cuidar el tipo de información que comparten y evitar divulgar información personal privada, propia o de familiares.","Tener contacto solamente con personas conocidas y no aceptar a desconocidos.","No entrar a sitios ni vínculos desconocidos, aunque parezcan atractivos.","Utilizar los filtros de seguridad de las plataformas para restringir con quién se comparte información."]
PROTECTION=["En casos menos delicados, hacer caso omiso a comentarios negativos, provocaciones o ataques.","Platicar el caso con familiares y amistades de mucha confianza para recibir apoyo y consejo.","En casos graves, acudir a la Policía Cibernética.","Buscar ayuda psicológica."]
def build_metrics():
    return pd.DataFrame([{"tipo":"Prevención","orden":i,"medida":m} for i,m in enumerate(PREVENTION,1)]+[{"tipo":"Protección","orden":i,"medida":m} for i,m in enumerate(PROTECTION,1)])
def _font(root):
    for n in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        p=root/"assets"/"fonts"/"Noto_Sans"/n
        if p.is_file():fm.fontManager.addfont(p)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"
def _draw_column(fig,x,title,items,color):
    fig.add_artist(patches.FancyBboxPatch((x,.18),.41,.59,boxstyle="round,pad=.018,rounding_size=.02",fc="white",ec=TEXT,lw=.8,transform=fig.transFigure,zorder=-1));fig.text(x+.025,.71,title,fontsize=19,fontweight="bold",color=TEXT)
    for i,item in enumerate(items,1):
        y=.63-(i-1)*.125;fig.add_artist(patches.Circle((x+.045,y+.01),.022,transform=fig.transFigure,fc=color,ec="none"));fig.text(x+.045,y+.01,str(i),ha="center",va="center",fontsize=12,fontweight="bold",color="white");fig.text(x+.082,y+.035,textwrap.fill(item,width=42),ha="left",va="top",fontsize=11,color="#222222",linespacing=1.25)
def _plot(d,out,root):
    plt.rcParams.update({"font.family":_font(root)});fig=plt.figure(figsize=(16,9),facecolor="white");fig.add_artist(patches.FancyBboxPatch((.025,.055),.95,.87,boxstyle="round,pad=.012,rounding_size=.02",fc=BACKGROUND,ec="none",transform=fig.transFigure,zorder=-2));fig.text(.047,.887,"•",color=SALMON,fontsize=20,va="center");fig.text(.064,.887,"Figura F.14.",color=TEXT,fontsize=16,fontweight="bold",va="center");fig.text(.171,.887,"Medidas preventivas y de protección ante la violencia digital (2023)",color=TEXT,fontsize=16,va="center");_draw_column(fig,.065,"Medidas preventivas",PREVENTION,BLUE);_draw_column(fig,.525,"Medidas de protección",PROTECTION,SALMON);fig.text(.047,.102,"Fuente:",color=TEXT,fontsize=9,fontweight="bold");fig.text(.094,.102,"IFT con información de la Tercera Encuesta 2023, Personas Usuarias de Servicios de Telecomunicaciones.",color=TEXT,fontsize=9);fig.text(.047,.075,"Nota:",color=TEXT,fontsize=9,fontweight="bold");fig.text(.081,.075,"Información correspondiente al estudio cualitativo; no es representativa a nivel nacional.",color=TEXT,fontsize=9);out.parent.mkdir(parents=True,exist_ok=True);apply_reference_ui(fig, FIGURE_ID); fig.savefig(out,dpi=200);plt.close(fig)
def generate(context):
    print("  F.14 | Reutilización o descarga del reporte oficial IFT");source=context.acquire_source(SOURCE_ID)
    if source.read_bytes()[:4]!=b"%PDF":raise ValueError("La fuente de F.14 no es un PDF válido")
    d=build_metrics();context.record_source_period(SOURCE_ID,PERIOD,"ULTIMO_COMPATIBLE");context.write_data_used(d)
    for r in d.itertuples(index=False):context.record_calculation(f"{r.tipo.lower()}_{r.orden}","síntesis fiel del hallazgo cualitativo publicado",{"pagina_fuente":"apartado de violencia digital","tipo":r.tipo},r.medida,"texto cualitativo")
    text=context.render_text("f_digital.md.j2",{"resumen":"El estudio cualitativo recomienda limitar la exposición de información personal, usar filtros de seguridad y buscar apoyo o denunciar cuando corresponda."});print(d.to_string(index=False));_plot(d,context.expected_figure_path,context.project_root);return {"figure_path":str(context.expected_figure_path),"text_path":str(text),"source_latest_period":PERIOD,"rows_used":len(d)}
def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"src"));from anuario2026.pipeline import run_pipeline;run_pipeline(root,only=FIGURE_ID);return 0
if __name__=="__main__":raise SystemExit(main())
