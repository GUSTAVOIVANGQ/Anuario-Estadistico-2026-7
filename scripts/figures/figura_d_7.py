"""Figura D.7: experiencias negativas en Internet por edad (ECSI 2024)."""
from __future__ import annotations

import sys, textwrap
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIGURE_ID, SOURCE_ID, PERIOD = "D.7", "ift_ecsi_2024_base", "2024"
TEXT, BG = "#3c3c3b", "#F8F8FA"
AGES = [(1, "18 a 24 años"), (2, "25 a 34 años"), (3, "35 a 44 años"), (4, "45 a 54 años"), (5, "55 años o más")]
VARIABLES = [("expp_mensnd", "Mensajes no deseados"), ("expp_pubipi", "Información personal publicada sin permiso"),
             ("expp_datpre", "Datos usados para préstamos sin permiso"), ("expp_robcon", "Robo de contraseñas")]
COLORS = ["#86adae", "#64a0a1", "#335a5c", "#132b2d"]
REFERENCE = [[64.8,16.5,8.6,23.1],[62.7,14.5,13.9,20.0],[60.8,13.1,11.9,18.2],[57.6,14.5,11.4,11.2],[53.4,9.4,8.6,9.5]]


def load_and_calculate(path: Path) -> pd.DataFrame:
    cols = [x for x, _ in VARIABLES] + ["rescate_internet", "edad_gpos", "fac_per"]
    data = pd.read_csv(path, usecols=cols, low_memory=False); data["fac_per"] = pd.to_numeric(data.fac_per, errors="coerce").fillna(0)
    data = data.loc[data.rescate_internet.eq(1)].copy(); rows = []
    for code, age in AGES:
        sub = data.loc[data.edad_gpos.eq(code)]; denominator = float(sub.fac_per.sum())
        for variable, label in VARIABLES:
            numerator = float(sub.loc[sub[variable].eq(1), "fac_per"].sum())
            rows.append({"edad": age, "codigo_edad": code, "variable": variable, "experiencia": label,
                         "porcentaje": numerator/denominator*100, "numerador_ponderado": numerator, "denominador_ponderado": denominator})
    return pd.DataFrame(rows)


def _font(root: Path) -> str:
    for name in ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"):
        path = root/"assets"/"fonts"/"Noto_Sans"/name
        if path.is_file(): fm.fontManager.addfont(path)
    return "Noto Sans" if any(x.name == "Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data: pd.DataFrame, output: Path, root: Path) -> None:
    plt.rcParams.update({"font.family": _font(root)})
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.035,.06),.93,.86,boxstyle="round,pad=.012,rounding_size=.02",fc=BG,ec="none",transform=fig.transFigure,zorder=-2))
    fig.text(.055,.88,"   ",fontsize=2,va="center",bbox=dict(boxstyle="round,pad=1.6,rounding_size=.2",fc="#4a7d75",ec="none")); fig.text(.073,.88,"Figura D.7.",color=TEXT,fontsize=16,fontweight="bold",va="center")
    fig.text(.18,.88,"Experiencias negativas en Internet por grupo de edad (2024)",color=TEXT,fontsize=16,va="center")
    ax=fig.add_axes([.075,.23,.86,.54]); ax.set_facecolor(BG); x=np.arange(len(AGES)); width=.18
    for i,(variable,label) in enumerate(VARIABLES):
        values=data.loc[data.variable.eq(variable),"porcentaje"].to_numpy(); bars=ax.bar(x+(i-1.5)*width,values,width,color=COLORS[i],label=label,zorder=2)
        for bar,value in zip(bars,values): ax.text(bar.get_x()+bar.get_width()/2,value+1,f"{value:.1f}%",ha="center",fontsize=8.5,color=TEXT,fontweight="bold",bbox=dict(boxstyle="round,pad=.18",fc="white",ec=COLORS[i],lw=.8))
    ax.set_ylim(0,75); ax.set_yticks(range(0,71,10),[f"{x}%" for x in range(0,71,10)]); ax.set_xticks(x,[age for _,age in AGES],color=TEXT)
    ax.tick_params(axis="both",length=0,pad=9,colors=TEXT); ax.grid(axis="y",color="#d1d1d1",linewidth=.7,zorder=0); ax.spines[:].set_visible(False)
    ax.legend(ncol=2,loc="upper center",bbox_to_anchor=(.5,1.13),frameon=False,labelcolor=TEXT,fontsize=9)
    fig.text(.055,.116,"Fuente:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.101,.116,"IFT, Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.",color=TEXT,fontsize=9)
    fig.text(.055,.088,"Nota:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.09,.088,"Porcentajes ponderados entre personas usuarias de Internet; las respuestas no son excluyentes.",color=TEXT,fontsize=9)
    output.parent.mkdir(parents=True,exist_ok=True); fig.savefig(output,dpi=200); plt.close(fig)


def generate(context):
    print("  D.7 | Descarga o reutilización de la base oficial ECSI 2024")
    raw=context.acquire_source(SOURCE_ID); data=load_and_calculate(raw)
    deviation=max(abs(round(float(data.loc[(data.codigo_edad.eq(code))&(data.variable.eq(variable)),"porcentaje"].iloc[0]),1)-REFERENCE[i][j]) for i,(code,_) in enumerate(AGES) for j,(variable,_) in enumerate(VARIABLES))
    if deviation>.11: raise ValueError(f"D.7 no reproduce la referencia: desviación {deviation:.1f} pp")
    context.record_source_period(SOURCE_ID,PERIOD,"ULTIMO_PUBLICADO"); context.write_data_used(data[["edad","experiencia","porcentaje"]])
    for row in data.itertuples(index=False): context.record_calculation(f"{row.variable}_edad_{row.codigo_edad}","sum(fac_per donde respuesta=1) / sum(fac_per del grupo de edad) * 100",{"edad":row.edad,"numerador":row.numerador_ponderado,"denominador":row.denominador_ponderado},row.porcentaje,"porcentaje",1)
    top=data.loc[data.porcentaje.idxmax()]; text_path=context.render_text("f_digital.md.j2",{"resumen":f"El valor mayor fue {top.experiencia.lower()} en {top.edad.lower()} ({top.porcentaje:.1f}%)."})
    print(f"Validación contra el anuario: desviación máxima {deviation:.1f} pp"); _plot(data,context.expected_figure_path,context.project_root)
    return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"source_latest_period":PERIOD,"rows_used":len(data)}


def main()->int:
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID); return 0


if __name__=="__main__": raise SystemExit(main())
