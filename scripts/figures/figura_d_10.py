"""Figura D.10: seguridad percibida en banca por Internet (ECSI 2024)."""
from __future__ import annotations

# Capa visual 2024: sólo modifica artistas de Matplotlib al guardar; no datos/cálculos.
import sys as _ui_sys
from pathlib import Path as _UIPath
_UI_SRC = _UIPath(__file__).resolve().parents[2] / "src"
if str(_UI_SRC) not in _ui_sys.path:
    _ui_sys.path.insert(0, str(_UI_SRC))
from anuario2026.ui_2024 import apply_reference_ui

import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIGURE_ID, SOURCE_ID, PERIOD = "D.10", "ift_ecsi_2024_base", "2024"
TEXT, BG = "#4B4B7D", "#FBFBF7"
AGES=[(1,"18 a 24 años"),(2,"25 a 34 años"),(3,"35 a 44 años"),(4,"45 a 54 años"),(5,"55 años o más")]
LEVELS=[(1,"Muy seguro"),(2,"Seguro"),(3,"Ni seguro ni inseguro"),(4,"Inseguro"),(9,"NS/NR")]
COLORS=["#327BA0","#A9DADF","#4F5082","#F48D7E","#F0535A"]
REFERENCE=[[5.2,58.8,9.6,11.3,14.9],[4.8,52.8,7.5,16.4,17.1],[4.4,47.4,7.4,19.8,20.1],[6.8,45.4,7.9,18.5,20.0],[3.5,33.9,6.8,21.0,32.1]]


def load_and_calculate(path:Path)->pd.DataFrame:
    data=pd.read_csv(path,usecols=["rescate_internet","edad_gpos","seg_banca","fac_per"],low_memory=False); data["fac_per"]=pd.to_numeric(data.fac_per,errors="coerce").fillna(0)
    data=data.loc[data.rescate_internet.eq(1)].copy(); data["seg_banca"]=data.seg_banca.fillna(9); rows=[]
    for age_code,age in AGES:
        sub=data.loc[data.edad_gpos.eq(age_code)]; denominator=float(sub.fac_per.sum())
        for level_code,level in LEVELS:
            numerator=float(sub.loc[sub.seg_banca.eq(level_code),"fac_per"].sum()); rows.append({"edad":age,"codigo_edad":age_code,"nivel":level,"codigo_nivel":level_code,"porcentaje":numerator/denominator*100,"numerador_ponderado":numerator,"denominador_ponderado":denominator})
    return pd.DataFrame(rows)


def _font(root:Path)->str:
    for name in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        path=root/"assets"/"fonts"/"Noto_Sans"/name
        if path.is_file(): fm.fontManager.addfont(path)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    plt.rcParams.update({"font.family":_font(root)}); fig=plt.figure(figsize=(16,9),facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.035,.06),.93,.86,boxstyle="round,pad=.012,rounding_size=.02",fc=BG,ec="none",transform=fig.transFigure,zorder=-2))
    fig.text(.055,.88,"•",color="#F58F82",fontsize=20,va="center"); fig.text(.073,.88,"Figura D.10.",color=TEXT,fontsize=16,fontweight="bold",va="center")
    fig.text(.19,.88,"Seguridad percibida al usar banca por Internet, por grupo de edad (2024)",color=TEXT,fontsize=16,va="center")
    ax=fig.add_axes([.075,.23,.86,.54]); ax.set_facecolor(BG); x=np.arange(len(AGES)); width=.15
    for i,(code,level) in enumerate(LEVELS):
        values=data.loc[data.codigo_nivel.eq(code),"porcentaje"].to_numpy(); bars=ax.bar(x+(i-2)*width,values,width,color=COLORS[i],label=level,zorder=2)
        for bar,value in zip(bars,values): ax.text(bar.get_x()+bar.get_width()/2,value+1,f"{value:.1f}%",ha="center",fontsize=7.8,color=TEXT,fontweight="bold",rotation=90 if value<10 else 0,bbox=dict(boxstyle="round,pad=.16",fc="white",ec="none"))
    ax.set_ylim(0,70); ax.set_yticks(range(0,71,10),[f"{x}%" for x in range(0,71,10)]); ax.set_xticks(x,[x[1] for x in AGES],color=TEXT)
    ax.tick_params(axis="both",length=0,pad=9,colors=TEXT); ax.grid(axis="y",color="#DADAE3",linewidth=.7,zorder=0); ax.spines[:].set_visible(False)
    ax.legend(ncol=5,loc="upper center",bbox_to_anchor=(.5,1.12),frameon=False,labelcolor=TEXT,fontsize=9)
    fig.text(.055,.116,"Fuente:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.101,.116,"IFT, Encuesta de Confianza en el Servicio de Internet (ECSI) 2024.",color=TEXT,fontsize=9)
    fig.text(.055,.088,"Nota:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.09,.088,"Porcentajes ponderados entre personas usuarias de Internet; los casos sin respuesta se integran en NS/NR.",color=TEXT,fontsize=9)
    output.parent.mkdir(parents=True,exist_ok=True); apply_reference_ui(fig, FIGURE_ID); fig.savefig(output,dpi=200); plt.close(fig)


def generate(context):
    print("  D.10 | Descarga o reutilización de la base oficial ECSI 2024")
    raw=context.acquire_source(SOURCE_ID); data=load_and_calculate(raw)
    deviation=max(abs(round(float(data.loc[(data.codigo_edad.eq(a))&(data.codigo_nivel.eq(l)),"porcentaje"].iloc[0]),1)-REFERENCE[i][j]) for i,(a,_) in enumerate(AGES) for j,(l,_) in enumerate(LEVELS))
    if deviation>.11: raise ValueError(f"D.10 no reproduce la referencia: desviación {deviation:.1f} pp")
    context.record_source_period(SOURCE_ID,PERIOD,"ULTIMO_PUBLICADO"); context.write_data_used(data[["edad","nivel","porcentaje"]])
    for row in data.itertuples(index=False): context.record_calculation(f"seg_banca_{row.codigo_edad}_{row.codigo_nivel}","sum(fac_per del nivel) / sum(fac_per de usuarios de Internet del grupo de edad) * 100",{"edad":row.edad,"nivel":row.nivel,"numerador":row.numerador_ponderado,"denominador":row.denominador_ponderado},row.porcentaje,"porcentaje",1)
    top=data.loc[data.porcentaje.idxmax()]; text_path=context.render_text("f_digital.md.j2",{"resumen":f"La proporción mayor fue {top.nivel.lower()} en {top.edad.lower()} ({top.porcentaje:.1f}%)."})
    print(f"Validación contra el anuario: desviación máxima {deviation:.1f} pp"); _plot(data,context.expected_figure_path,context.project_root)
    return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"source_latest_period":PERIOD,"rows_used":len(data)}


def main()->int:
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID); return 0
if __name__=="__main__": raise SystemExit(main())
