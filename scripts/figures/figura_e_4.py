"""Figura E.4: servicios contratados por las MiPymes, 2023-2024."""
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
import pandas as pd

FIGURE_ID,PERIOD="E.4","2024"; SOURCES={2023:"ift_mipymes_2023_base",2024:"ift_mipymes_2024_base"}
SIZES=["General","Micro","Pequeña","Mediana"]; SERVICES=["Internet fijo","Telefonía fija","Telefonía móvil","Televisión de paga"]
REFERENCE={2023:{"Internet fijo":[89.4,89.3,89.8,99.5],"Telefonía fija":[78.9,78.4,85.8,94.6],"Telefonía móvil":[29.6,30.2,19.9,27.4],"Televisión de paga":[25.4,25.7,21.7,17.8]},2024:{"Internet fijo":[95.3,95.2,96.3,98.1],"Telefonía fija":[69.0,68.3,78.6,85.5],"Telefonía móvil":[29.0,28.7,34.9,31.9],"Televisión de paga":[27.0,27.4,22.1,20.9]}}
TEXT,BG,TITLE_MARKER="#3C3C3B","#F8F8FA","#4A7D75"
HEADER_BG="#E6F0EF"; YEAR_2023_BG="#F3E8E4"; YEAR_2024_BG="#D9EBED"; ROW_LABEL_BG="#FFFFFF"; BORDER="#9CB7B4"


def _norm(value:object)->str:
    text=unicodedata.normalize("NFKD",str(value).replace(" "," ").lower()); return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9]+"," ","".join(c for c in text if not unicodedata.combining(c)))).strip()


def load_raw(path:Path)->pd.DataFrame:
    with zipfile.ZipFile(path) as z:
        names=[n for n in z.namelist() if n.lower().endswith((".xlsx",".xls")) and "diccionario" not in _norm(n)]
        if not names: raise ValueError(f"El ZIP {path.name} no contiene base Excel")
        name=max(names,key=lambda n:z.getinfo(n).file_size); return pd.read_excel(BytesIO(z.read(name)))


def _find(df:pd.DataFrame,*tokens:str)->str:
    found=[str(c) for c in df.columns if all(_norm(t) in _norm(c) for t in tokens)]
    if not found: raise KeyError(f"No se encontró columna con {tokens}")
    return min(found,key=lambda c:len(_norm(c)))


def _main_service_col(df:pd.DataFrame,service:str)->str:
    wanted={"Internet fijo":["conexion","internet","fijo"],"Telefonía fija":["telefonia","fija"],"Telefonía móvil":["telefonia","movil"],"Televisión de paga":["television","paga"]}[service]
    found=[str(c) for c in df.columns if "hablando exclusivamente" in _norm(c) and "actividades laborales" in _norm(c) and all(t in _norm(c) for t in wanted)]
    if service=="Telefonía móvil": found=[c for c in found if "datos moviles" not in _norm(c)]
    if len(found)!=1: raise KeyError(f"Se esperaba una pregunta principal para {service} y se encontraron {len(found)}")
    return found[0]


def _yes(series:pd.Series)->pd.Series:
    return series.astype("string").map(_norm).isin({"si","s","yes"})


def build_metrics(frames:dict[int,pd.DataFrame])->pd.DataFrame:
    rows=[]
    for year,df in frames.items():
        weight=_find(df,"factor","expansion","final"); size_col=_find(df,"clasificacion","empresa","tamano")
        size_values={s:next(v for v in df[size_col].dropna().unique() if _norm(s)[:4] in _norm(v)) for s in SIZES[1:]}
        for service in SERVICES:
            col=_main_service_col(df,service)
            for size in SIZES:
                sub=df if size=="General" else df.loc[df[size_col].eq(size_values[size])]; valid=sub[[col,weight]].dropna(); weights=pd.to_numeric(valid[weight],errors="coerce").fillna(0); denominator=float(weights.sum()); numerator=float(weights.loc[_yes(valid[col])].sum())
                rows.append({"anio":year,"servicio":service,"tamano":size,"porcentaje":numerator/denominator*100,"numerador_ponderado":numerator,"denominador_ponderado":denominator,"columna":col})
    return pd.DataFrame(rows)


def validate(data:pd.DataFrame)->float:
    dev=max(abs(round(float(data.loc[(data.anio.eq(y))&(data.servicio.eq(s))&(data.tamano.eq(z)),"porcentaje"].iloc[0]),1)-v) for y in REFERENCE for s,vals in REFERENCE[y].items() for z,v in zip(SIZES,vals))
    if dev>.11: raise ValueError(f"E.4 no reproduce las bases oficiales: desviación {dev:.1f} pp")
    return dev


def _font(root:Path)->str:
    for n in ("NotoSans-Regular.ttf","NotoSans-Bold.ttf"):
        p=root/"assets"/"fonts"/"Noto_Sans"/n
        if p.is_file(): fm.fontManager.addfont(p)
    return "Noto Sans" if any(x.name=="Noto Sans" for x in fm.fontManager.ttflist) else "DejaVu Sans"


def _plot(data:pd.DataFrame,output:Path,root:Path)->None:
    plt.rcParams.update({"font.family":_font(root)})
    fig=plt.figure(figsize=(16,9),facecolor="white")
    fig.add_artist(patches.FancyBboxPatch((.035,.06),.93,.86,boxstyle="round,pad=.012,rounding_size=.02",fc=BG,ec="none",transform=fig.transFigure,zorder=-2))
    fig.text(.055,.88,"▪",color=TITLE_MARKER,fontsize=16,va="center")
    fig.text(.073,.88,"Figura E.4.",color=TEXT,fontsize=16,fontweight="bold",va="center")
    fig.text(.18,.88,"Servicios de telecomunicaciones que contratan las MiPymes (2023-2024)",color=TEXT,fontsize=16,va="center")

    ax=fig.add_axes([.055,.20,.89,.57]); ax.axis("off")
    columns=[f"{s}\n{y}" for s in SERVICES for y in (2023,2024)]
    cells=[]
    for size in SIZES:
        cells.append([f"{float(data.loc[(data.tamano.eq(size))&(data.servicio.eq(service))&(data.anio.eq(year)), 'porcentaje'].iloc[0]):.1f}%" for service in SERVICES for year in (2023,2024)])
    table=ax.table(cellText=cells,rowLabels=SIZES,colLabels=columns,cellLoc="center",rowLoc="center",bbox=[0,0,1,1])
    table.auto_set_font_size(False); table.set_fontsize(10.5)

    for (row,col),cell in table.get_celld().items():
        cell.set_edgecolor(BORDER); cell.set_linewidth(.8); cell.get_text().set_color(TEXT)
        if row==0:
            cell.set_facecolor(HEADER_BG)
            cell.get_text().set_fontweight("bold")
        elif col==-1:
            cell.set_facecolor(ROW_LABEL_BG)
            cell.get_text().set_fontweight("bold")
        else:
            cell.set_facecolor(YEAR_2023_BG if col%2==0 else YEAR_2024_BG)
            cell.get_text().set_fontweight("bold")

    fig.text(.055,.122,"Fuente:",color=TEXT,fontsize=9,fontweight="bold")
    fig.text(.101,.122,"IFT, Cuarta Encuesta 2023 y 2024, Usuarios de Servicios de Telecomunicaciones (MiPymes).",color=TEXT,fontsize=9)
    fig.text(.055,.094,"Nota:",color=TEXT,fontsize=9,fontweight="bold")
    fig.text(.09,.094,"Respuesta múltiple, por lo que la suma no da 100%. En 2024 no se publicó Datos móviles como categoría separada.",color=TEXT,fontsize=9)
    output.parent.mkdir(parents=True,exist_ok=True); apply_reference_ui(fig, FIGURE_ID); fig.savefig(output,dpi=200); plt.close(fig)


def generate(context):
    frames={}
    for year,source in SOURCES.items(): print(f"  E.4 | Descarga o reutilización de MiPymes {year}"); frames[year]=load_raw(context.acquire_source(source)); context.record_source_period(source,str(year),"ULTIMO_PUBLICADO" if year==2024 else "HISTORICO")
    data=build_metrics(frames); deviation=validate(data); context.write_data_used(data[["anio","servicio","tamano","porcentaje"]])
    for row in data.itertuples(index=False): context.record_calculation(f"contratacion_{row.anio}_{_norm(row.servicio)}_{_norm(row.tamano)}","sum(factor donde respuesta Sí) / sum(factor con respuesta) * 100",{"anio":row.anio,"servicio":row.servicio,"tamano":row.tamano,"numerador":row.numerador_ponderado,"denominador":row.denominador_ponderado,"columna":row.columna},row.porcentaje,"porcentaje",1)
    top=data.loc[data.anio.eq(2024)].sort_values("porcentaje",ascending=False).iloc[0]; text_path=context.render_text("f_digital.md.j2",{"resumen":f"En 2024, {top.servicio.lower()} fue el servicio más contratado ({top.porcentaje:.1f}% en {top.tamano.lower()})."})
    print(f"Validación con bases oficiales: desviación máxima {deviation:.1f} pp"); _plot(data,context.expected_figure_path,context.project_root)
    return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"source_latest_period":PERIOD,"rows_used":len(data)}


def main()->int:
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID); return 0
if __name__=="__main__": raise SystemExit(main())
