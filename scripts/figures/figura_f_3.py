"""Figura F.3: distribución estatal de víctimas de ciberacoso, MOCIBA."""
from __future__ import annotations

import sys, textwrap, zipfile
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

FIGURE_ID = "F.3"
CURRENT_SOURCE_ID = "inegi_mociba_2025"
REFERENCE_SOURCE_ID = "inegi_mociba_2024_reference"
PERIOD = "2025"
LANDING_PAGE = "https://www.inegi.org.mx/programas/mociba/2025/"
TEXT, BLUE, ACCENT, BG = "#50517F", "#2F7C9F", "#F58F82", "#FBFBF7"


def _fonts(root: Path) -> None:
    directory = root / "assets" / "fonts" / "Noto_Sans"
    for name in ("NotoSans-Regular.ttf", "NotoSans-Medium.ttf", "NotoSans-Bold.ttf"):
        if (directory / name).is_file(): fm.fontManager.addfont(directory / name)
    names = {x.name for x in fm.fontManager.ttflist}
    plt.rcParams["font.family"] = "Noto Sans" if "Noto Sans" in names else "DejaVu Sans"


def _read_csv(raw: bytes) -> pd.DataFrame:
    error = None
    for encoding in ("utf-8-sig", "latin1", "cp1252"):
        for separator in (",", "|", ";"):
            try:
                frame = pd.read_csv(BytesIO(raw), encoding=encoding, sep=separator, low_memory=False)
                frame.columns = [str(c).strip().upper() for c in frame.columns]
                if {"P4_01", "FACTOR", "CVE_ENT"}.issubset(frame.columns): return frame
            except Exception as exc: error = exc
    raise ValueError(f"No se pudo leer la base MOCIBA: {error}")


def load_microdata(path: Path) -> tuple[pd.DataFrame, str]:
    if not zipfile.is_zipfile(path): raise ValueError(f"El insumo no es ZIP válido: {path}")
    with zipfile.ZipFile(path) as archive:
        for member in archive.namelist():
            if member.lower().endswith(".csv"):
                try: frame = _read_csv(archive.read(member)); break
                except ValueError: continue
        else: raise ValueError(f"No se encontró el CSV individual MOCIBA en {path.name}")
    required = {"FACTOR", "CVE_ENT", "NOM_ENT", "SEXO", "EDAD"} | {f"P4_{i:02d}" for i in range(1, 14)}
    missing = sorted(required - set(frame.columns))
    if missing: raise ValueError(f"Faltan variables MOCIBA: {missing}")
    print(f"  {FIGURE_ID} | Base {path.name}: {len(frame):,} registros, miembro {member}")
    return frame, member


def num(series: pd.Series) -> pd.Series: return pd.to_numeric(series, errors="coerce")
def weights(frame: pd.DataFrame) -> pd.Series: return num(frame["FACTOR"]).fillna(0.0)
def victim_mask(frame: pd.DataFrame) -> pd.Series:
    return pd.concat([num(frame[f"P4_{i:02d}"]).eq(1) for i in range(1, 14)], axis=1).any(axis=1)


def calculate(frame: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    w, victim = weights(frame), victim_mask(frame)
    total = float(w.loc[victim].sum())
    if total <= 0: raise ValueError("El total ponderado de víctimas no es positivo")
    data = frame.loc[victim, ["CVE_ENT", "NOM_ENT"]].copy()
    data["personas"] = w.loc[victim]
    out = data.groupby(["CVE_ENT", "NOM_ENT"], as_index=False)["personas"].sum()
    out["porcentaje"] = out["personas"] / total * 100
    out = out.sort_values("porcentaje", ascending=False).reset_index(drop=True)
    if len(out) != 32 or abs(out["porcentaje"].sum() - 100) > 1e-7:
        raise ValueError("La distribución estatal no contiene 32 entidades o no suma 100%")
    return out, total


def validate_reference(frame: pd.DataFrame) -> dict[str, float]:
    data, total = calculate(frame)
    if not 18_800_000 <= total <= 19_000_000:
        raise RuntimeError(f"MOCIBA 2024 no reproduce el total oficial aproximado de 18.9 millones: {total:,.0f}")
    return {"total_victimas": total, "suma_porcentajes": float(data.porcentaje.sum()), "entidades": len(data)}


def _plot(data: pd.DataFrame, output: Path, root: Path) -> None:
    _fonts(root); fig, ax = plt.subplots(figsize=(16, 9)); fig.patch.set_facecolor("white"); ax.set_facecolor(BG)
    values = data["porcentaje"].tolist(); x = range(len(data))
    bars = ax.bar(x, values, width=.43, color=BLUE, edgecolor="none")
    for i, (bar, value) in enumerate(zip(bars, values)):
        bar.set_clip_path(mpatches.FancyBboxPatch((bar.get_x(), 0), bar.get_width(), value, boxstyle="round,pad=0,rounding_size=.18", transform=ax.transData))
        ax.text(bar.get_x()+bar.get_width()/2, value+.28+(i%2)*.43, f"{value:.1f}%", ha="center", fontsize=6.8, fontweight="bold", color=TEXT,
                bbox=dict(boxstyle="round,pad=.25", fc="white", ec="none"))
    ax.set_xticks(list(x), [str(v).replace(" ", "\n", 1) for v in data["NOM_ENT"]], rotation=90, fontsize=6.6, color=TEXT)
    ax.set_ylim(0, max(values)*1.23); ax.set_yticks([]); ax.tick_params(axis="x", length=0, pad=7)
    for spine in ax.spines.values(): spine.set_visible(False)
    fig.add_artist(mpatches.FancyBboxPatch((.035,.09),.93,.83,transform=fig.transFigure,boxstyle="round,pad=.006,rounding_size=.018",fc=BG,ec="none",zorder=-1))
    fig.add_artist(mpatches.FancyBboxPatch((.052,.864),.008,.018,transform=fig.transFigure,boxstyle="round,pad=0,rounding_size=.003",fc=ACCENT,ec="none"))
    fig.text(.066,.873,"Figura F.3.",fontsize=14,fontweight="bold",color=TEXT,va="center")
    fig.text(.151,.873,"Porcentaje de la población de 12 años y más que vivió ciberacoso por entidad federativa",fontsize=14,color=TEXT,va="center")
    fig.text(.052,.125,"Fuente:",fontsize=8.5,fontweight="bold",color=TEXT,va="top")
    fig.text(.095,.125,textwrap.fill(f"IFT con datos del MOCIBA {PERIOD}, del INEGI. Para más información consultar {LANDING_PAGE}",190),fontsize=8.5,color=TEXT,va="top")
    fig.subplots_adjust(left=.055,right=.958,top=.80,bottom=.25); output.parent.mkdir(parents=True,exist_ok=True); fig.savefig(output,dpi=200); plt.close(fig)


def generate(context):
    print("  F.3 | 1/4 Reutilización o descarga de MOCIBA 2024 y 2025")
    reference = context.acquire_source(REFERENCE_SOURCE_ID); current = context.acquire_source(CURRENT_SOURCE_ID)
    print("  F.3 | 2/4 Validación del modelo con MOCIBA 2024")
    ref, ref_member = load_microdata(reference); validation = validate_reference(ref); del ref
    print(f"  F.3 | Validación 2024 APROBADA: {validation['total_victimas']:,.0f} víctimas")
    print("  F.3 | 3/4 Cálculo con MOCIBA 2025")
    frame, member = load_microdata(current); data, total = calculate(frame); del frame
    data.insert(0,"periodo",PERIOD); context.record_source_period(REFERENCE_SOURCE_ID,"2024","REFERENCIA_REPRODUCIDA"); context.record_source_period(CURRENT_SOURCE_ID,PERIOD,"AL_DIA")
    context.write_data_used(data)
    context.record_calculation("validacion_2024","32 participaciones estatales = sum(FACTOR de víctimas de la entidad) / sum(FACTOR de víctimas nacional) * 100",{"miembro":ref_member},validation,"validación",2)
    context.record_calculation("distribucion_estatal_2025","sum(FACTOR de víctimas de la entidad) / sum(FACTOR de víctimas nacional) * 100",{"miembro":member,"total_victimas":round(total),"entidades":32},{"mayor":data.iloc[0].NOM_ENT,"mayor_pct":round(data.iloc[0].porcentaje,2),"menor":data.iloc[-1].NOM_ENT,"menor_pct":round(data.iloc[-1].porcentaje,2)},"porcentaje",2)
    summary=f"En {PERIOD}, {data.iloc[0].NOM_ENT} concentró la mayor proporción nacional de personas que vivieron ciberacoso ({data.iloc[0].porcentaje:.1f}%), mientras que {data.iloc[-1].NOM_ENT} registró la menor ({data.iloc[-1].porcentaje:.1f}%)."
    text_path=context.render_text("f_mociba.md.j2",{"resumen":summary}); print(data[["NOM_ENT","personas","porcentaje"]].to_string(index=False,formatters={"personas":lambda x:f"{x:,.0f}","porcentaje":lambda x:f"{x:.1f}%"}))
    print("  F.3 | 4/4 Generación de gráfica PNG"); _plot(data,context.expected_figure_path,context.project_root)
    return {"figure_path":str(context.expected_figure_path),"text_path":str(text_path),"detected_period":PERIOD,"rows_used":len(data),"reference_validation":"aprobada"}


def main() -> int:
    root=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(root/"src")); from anuario2026.pipeline import run_pipeline
    run_pipeline(root,only=FIGURE_ID); return 0
if __name__ == "__main__": raise SystemExit(main())
