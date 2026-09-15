"""Figura E.6: beneficios de vender mediante Internet fijo, 2024."""
from __future__ import annotations

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

FIGURE_ID,SOURCE_ID,PERIOD="E.6","ift_mipymes_2024_base","2024"; SIZES=["General","Micro","Pequeña","Mediana"]
CATEGORIES=["Incremento de ventas","Ampliar canales de venta","Inclusión de marketing digital","Rapidez de ventas o compras","Otros"]
REFERENCE={"General":[65.7,17.2,6.7,8.1,1.2],"Micro":[66.2,16.9,6.4,8.0,1.2],"Pequeña":[57.2,20.8,11.4,9.5,.6],"Mediana":[60.2,20.1,8.0,9.2,1.4]}
TEXT,BG,CORAL="#4B4B7D","#FBFBF7","#F48D7E"; COLORS=["#A9DADF","#F48D7E","#327BA0","#F0535A"]


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


def build_metrics(df:pd.DataFrame)->pd.DataFrame:
    weight=_find(df,"factor","expansion","final"); size_col=_find(df,"clasificacion","empresa","tamano"); sizes={s:next(v for v in df[size_col].dropna().unique() if _norm(s)[:4] in _norm(v)) for s in SIZES[1:]}
    sell=_find(df,"vender","producto",reject=["beneficio"]); benefit=_find(df,"cual","principal","beneficio","empresa","venda"); sellers=df.loc[_yes(df[sell])].copy(); rows=[]
    for size in SIZES:
        sub=sellers if size=="General" else sellers.loc[sellers[size_col].eq(sizes[size])]; weights=pd.to_numeric(sub[weight],errors="coerce").fillna(0); denominator=float(weights.sum()); normalized=sub[benefit].astype("string").map(_norm)
        masks=[normalized.str.contains("increment")&normalized.str.contains("venta"),normalized.str.contains("ampli")&normalized.str.contains("canal"),normalized.str.contains("marketing"),normalized.str.contains("rapidez")|(normalized.str.contains("rapida")&normalized.str.contains("venta")),normalized.str.startswith("otro")]
        for category,mask in zip(CATEGORIES,masks):
            numerator=float(weights.loc[mask.fillna(False)].sum()); rows.append({"tamano":size,"beneficio":category,"porcentaje":numerator/denominator*100,"numerador_ponderado":numerator,"denominador_ponderado":denominator})
    return pd.DataFrame(rows)


def _font(root:Path)->str:
    for n in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        p=root/"assets"/"fonts"/"Noto_Sans"/n
        if p.is_file(): fm.fontManager.addfont(p)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    plt.rcParams.update({"font.family":_font(root)}); fig=plt.figure(figsize=(16,9),facecolor="white"); fig.add_artist(patches.FancyBboxPatch((.035,.06),.93,.86,boxstyle="round,pad=.012,rounding_size=.02",fc=BG,ec="none",transform=fig.transFigure,zorder=-2))
    fig.text(.055,.88,"•",color=CORAL,fontsize=20,va="center"); fig.text(.073,.88,"Figura E.6.",color=TEXT,fontsize=16,fontweight="bold",va="center"); fig.text(.18,.88,"Beneficios de vender a través de Internet fijo (2024)",color=TEXT,fontsize=16,va="center")
    ax=fig.add_axes([.075,.22,.86,.56]); ax.set_facecolor(BG); x=np.arange(5); width=.18
    for i,size in enumerate(SIZES):
        vals=data.loc[data.tamano.eq(size),"porcentaje"].to_numpy(); bars=ax.bar(x+(i-1.5)*width,vals,width,color=COLORS[i],label=size,zorder=2)
        for bar,v in zip(bars,vals): ax.text(bar.get_x()+bar.get_width()/2,v+1,f"{v:.1f}%",ha="center",fontsize=8.5,color=TEXT,fontweight="bold",bbox=dict(boxstyle="round,pad=.18",fc="white",ec="none"))
    ax.set_ylim(0,75); ax.set_yticks(range(0,71,10),[f"{x}%" for x in range(0,71,10)]); ax.set_xticks(x,[textwrap.fill(c,22) for c in CATEGORIES],fontsize=9,color=TEXT); ax.tick_params(axis="both",length=0,pad=8,colors=TEXT); ax.grid(axis="y",color="#DADAE3",linewidth=.7,zorder=0); ax.spines[:].set_visible(False); ax.legend(ncol=4,loc="upper center",bbox_to_anchor=(.5,1.10),frameon=False,labelcolor=TEXT)
    fig.text(.055,.12,"Fuente:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.101,.12,"IFT, Cuarta Encuesta 2024, Usuarios de Servicios de Telecomunicaciones (MiPymes).",color=TEXT,fontsize=9)
    fig.text(.055,.092,"Nota:",color=TEXT,fontsize=9,fontweight="bold"); fig.text(.09,.092,"Respuesta espontánea; se excluye No sabe/No contestó, por lo que la suma no da 100%.",color=TEXT,fontsize=9)
    output.parent.mkdir(parents=True,exist_ok=True); fig.savefig(output,dpi=200); plt.close(fig)


def generate(context):
    print("  E.6 | Descarga o reutilización de MiPymes 2024"); raw=context.acquire_source(SOURCE_ID); data=build_metrics(load_raw(raw)); context.record_source_period(SOURCE_ID,PERIOD,"ULTIMO_PUBLICADO")
    deviation=max(abs(round(float(data.loc[(data.tamano.eq(size))&(data.beneficio.eq(cat)),"porcentaje"].iloc[0]),1)-value) for size,vals in REFERENCE.items() for cat,value in zip(CATEGORIES,vals))
    if deviation>.11: raise ValueError(f"E.6 no reproduce la referencia oficial 2024: {deviation:.1f} pp")
    context.write_data_used(data[["tamano","beneficio","porcentaje"]])
    for row in data.itertuples(index=False): context.record_calculation(f"venta_{_norm(row.tamano)}_{_norm(row.beneficio)}","sum(factor de categoría) / sum(factor de empresas que venden por Internet) * 100",{"tamano":row.tamano,"beneficio":row.beneficio,"numerador":row.numerador_ponderado,"denominador":row.denominador_ponderado},row.porcentaje,"porcentaje",1)
    top=data.sort_values("porcentaje",ascending=False).iloc[0]; text_path=context.render_text("f_digital.md.j2",{"resumen":f"El beneficio más señalado fue {top.beneficio.lower()} ({top.porcentaje:.1f}% en {top.tamano.lower()})."}); print(f"Validación 2024: desviación máxima {deviation:.1f} pp"); _plot(data,context.expected_figure_path,context.project_root)
    return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"source_latest_period":PERIOD,"rows_used":len(data)}


def main()->int:
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID); return 0
if __name__=="__main__": raise SystemExit(main())
