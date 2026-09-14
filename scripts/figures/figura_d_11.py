"""Figura D.11: seguridad percibida en redes sociales por sexo (ECSI 2024)."""
from __future__ import annotations

import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIGURE_ID, SOURCE_ID, PERIOD = "D.11", "ift_ecsi_2024_base", "2024"
TEXT, BG = "#4B4B7D", "#FBFBF7"
GROUPS = [("Total", None), ("Mujeres", 1), ("Hombres", 2)]
LEVELS = [(9,"NS/NR"),(4,"Inseguro"),(3,"Ni seguro ni inseguro"),(2,"Seguro"),(1,"Muy seguro")]
COLORS = ["#65B9D8","#F0535A","#F48D7E","#A9DADF","#327BA0"]
REFERENCE = {"Total":{"Muy seguro":3.5,"Seguro":48.8,"Ni seguro ni inseguro":15.5,"Inseguro":18.3,"NS/NR":12.8},
             "Mujeres":{"Muy seguro":2.8,"Seguro":43.1,"Ni seguro ni inseguro":16.2,"Inseguro":22.1,"NS/NR":14.7},
             "Hombres":{"Muy seguro":4.4,"Seguro":55.4,"Ni seguro ni inseguro":14.6,"Inseguro":14.0,"NS/NR":10.5}}


def load_and_calculate(path:Path)->pd.DataFrame:
    data=pd.read_csv(path,usecols=["rescate_internet","sexo","seg_redes","fac_per"],low_memory=False); data["fac_per"]=pd.to_numeric(data.fac_per,errors="coerce").fillna(0)
    data=data.loc[data.rescate_internet.eq(1)&data.sexo.isin([1,2])].copy(); data["seg_redes"]=data.seg_redes.fillna(9); rows=[]
    for group,sex in GROUPS:
        sub=data if sex is None else data.loc[data.sexo.eq(sex)]; denominator=float(sub.fac_per.sum())
        for code,level in LEVELS:
            numerator=float(sub.loc[sub.seg_redes.eq(code),"fac_per"].sum()); rows.append({"grupo":group,"sexo_codigo":"total" if sex is None else sex,"nivel":level,"codigo_nivel":code,"porcentaje":numerator/denominator*100,"numerador_ponderado":numerator,"denominador_ponderado":denominator})
    return pd.DataFrame(rows)


def _font(root:Path)->str:
    for name in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        path=root/"assets"/"fonts"/"Noto_Sans"/name
        if path.is_file(): fm.fontManager.addfont(path)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    plt.rcParams.update({"font.family":_font(root)}); fig=plt.figure(figsize=(16,9),facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.035,.06),.93,.86,boxstyle="round,pad=.012,rounding_size=.02",fc=BG,ec="none",transform=fig.transFigure,zorder=-2))
    fig.text(.055,.88,"•",color="#F58F82",fontsize=20,va="center"); fig.text(.073,.88,"Figura D.11.",color=TEXT,fontsize=16,fontweight="bold",va="center")
    fig.text(.195,.88,"Seguridad percibida al compartir información en redes sociales, por sexo (2024)",color=TEXT,fontsize=16,va="center")
    ax=fig.add_axes([.19,.19,.72,.60]); ax.set_facecolor(BG); y=np.arange(len(LEVELS)); height=.22
    group_colors={"Total":"#4F5082","Mujeres":"#F48D7E","Hombres":"#327BA0"}
    for i,(group,_) in enumerate(GROUPS):
        values=data.loc[data.grupo.eq(group),"porcentaje"].to_numpy(); bars=ax.barh(y+(i-1)*height,values,height,color=group_colors[group],label=group,zorder=2)
        for bar,value in zip(bars,values): ax.text(value+.7,bar.get_y()+bar.get_height()/2,f"{value:.1f}%",va="center",color=TEXT,fontsize=10,fontweight="bold",bbox=dict(boxstyle="round,pad=.2",fc="white",ec="none"))
    ax.set_xlim(0,65); ax.set_xticks(range(0,61,10),[f"{x}%" for x in range(0,61,10)]); ax.set_yticks(y,[x[1] for x in LEVELS],color=TEXT,fontsize=11); ax.invert_yaxis()
    ax.tick_params(axis="both",length=0,pad=8,colors=TEXT); ax.grid(axis="x",color="#DADAE3",linewidth=.7,zorder=0); ax.spines[:].set_visible(False)
    ax.legend(ncol=3,loc="upper center",bbox_to_anchor=(.5,1.10),frameon=False,labelcolor=TEXT)
    fig.text(.055,.116,"Fuente:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.101,.116,"IFT, Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.",color=TEXT,fontsize=9)
    fig.text(.055,.088,"Nota:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.09,.088,"Porcentajes ponderados entre personas usuarias de Internet; los casos sin respuesta se integran en NS/NR.",color=TEXT,fontsize=9)
    output.parent.mkdir(parents=True,exist_ok=True); fig.savefig(output,dpi=200); plt.close(fig)


def generate(context):
    print("  D.11 | Descarga o reutilización de la base oficial ECSI 2024")
    raw=context.acquire_source(SOURCE_ID); data=load_and_calculate(raw)
    deviation=max(abs(round(float(data.loc[(data.grupo.eq(group))&(data.nivel.eq(level)),"porcentaje"].iloc[0]),1)-REFERENCE[group][level]) for group,_ in GROUPS for _,level in LEVELS)
    if deviation>.11: raise ValueError(f"D.11 no reproduce la referencia: desviación {deviation:.1f} pp")
    context.record_source_period(SOURCE_ID,PERIOD,"ULTIMO_PUBLICADO"); context.write_data_used(data[["grupo","nivel","porcentaje"]])
    for row in data.itertuples(index=False): context.record_calculation(f"seg_redes_{row.sexo_codigo}_{row.codigo_nivel}","sum(fac_per del nivel) / sum(fac_per de usuarios de Internet del grupo) * 100",{"grupo":row.grupo,"nivel":row.nivel,"numerador":row.numerador_ponderado,"denominador":row.denominador_ponderado},row.porcentaje,"porcentaje",1)
    top=data.loc[data.porcentaje.idxmax()]; text_path=context.render_text("f_digital.md.j2",{"resumen":f"La proporción mayor fue {top.nivel.lower()} entre {top.grupo.lower()} ({top.porcentaje:.1f}%)."})
    print(f"Validación contra el anuario: desviación máxima {deviation:.1f} pp"); _plot(data,context.expected_figure_path,context.project_root)
    return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"source_latest_period":PERIOD,"rows_used":len(data)}


def main()->int:
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID); return 0
if __name__=="__main__": raise SystemExit(main())
