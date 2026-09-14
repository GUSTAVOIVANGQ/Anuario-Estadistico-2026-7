from __future__ import annotations
import importlib.util
from pathlib import Path
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    path=ROOT/"scripts"/"figures"/f"figura_{name}.py"; spec=importlib.util.spec_from_file_location(f"test_{name}",path); module=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module); return module
B23=load("b_23"); B24=load("b_24"); B25=load("b_25"); C1=load("c_1"); C2=load("c_2")

def test_b23_uses_latest_december_and_calculates_segments():
    rows=[]
    for year,mult in ((2023,1),(2024,2)):
        for tech,value in (("Cable",50),("DTH",30),("IPTV",20)):
            rows.append({"ANIO":year,"MES":12,"TECNO_ACCESO_TV":tech,"A_RESIDENCIAL_E":value*mult,"A_NO_RESIDENCIAL_E":value})
    data,meta=B23.build_metrics(pd.DataFrame(rows)); assert meta["anio"]==2024; assert meta["total_residencial"]==200; assert data.loc[(data.segmento=="Residencial")&(data.tecnologia=="Cable"),"participacion"].iloc[0]==50

def test_b24_maps_groups_and_keeps_latest_year():
    raw=pd.DataFrame([{"ANIO":y,"MES":12,"GRUPO":g,"MARKET_SHARE":v} for y in (2023,2024) for g,v in (("Grupo Televisa",.6),("Megacable",.2),("Dish",.1),("Totalplay",.1))])
    data,meta=B24.build_metrics(raw); assert meta["anio"]==2024; assert data.iloc[-1]["Grupo Televisa"]==60; assert data.iloc[-1]["Grupo Salinas"]==10

def test_b25_selects_latest_december():
    data,meta=B25.build_metrics(pd.DataFrame({"ANIO":[2015,2024,2025],"MES":[12,12,6],"IHH_TVRES_E":[5000,3691,3600]})); assert meta["anio"]==2024; assert data.iloc[-1].ihh==3691

def test_c1_selects_latest_spectrum_row_and_totals_645():
    cols={c:[1,v] for c,v in zip(C1.BANDS,[90,20,47,68,130,140,50,100])}; raw=pd.DataFrame({"ESTADO":["dic-22","ago-24"],**cols}); data,meta=C1.build_metrics(raw); assert (meta["anio"],meta["mes"],meta["total"])==(2024,8,645); assert len(data)==8

def test_c2_validates_operator_shares():
    rows=[]
    for op,share in (("TELCEL",.6),("AT&T",.4),("ALTAN",0)):
        row={"OPERADOR":op}; row.update({c:share for c in C2.BANDS}); rows.append(row)
    data=C2.build_metrics(pd.DataFrame(rows)); assert data.loc[(data.operador=="TELCEL")&(data.banda=="850 MHz"),"participacion"].iloc[0]==pytest.approx(60)
