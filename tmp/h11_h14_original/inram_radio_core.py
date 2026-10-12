# -*- coding: utf-8 -*-
"""Motor de cálculo para las Figuras H.11-H.14 a partir de datos crudos INRAM.

El archivo ODS consolidado esperado contiene las hojas:
  CDMX_TOTAL, CDMX_HOMBRES, CDMX_MUJERES,
  GDL_TOTAL,  GDL_HOMBRES,  GDL_MUJERES,
  MTY_TOTAL,  MTY_HOMBRES,  MTY_MUJERES,
  UNIVERSOS.

Las hojas de datos conservan la estructura de exportación de INRAM
(Multiplaza - Rating por Horas). La hoja UNIVERSOS contiene la población
por plaza, target y estudio/mes.
"""
from __future__ import annotations

import argparse
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}

HORAS = [f"{h:02d}:00" for h in range(6, 24)]
MESES = {
    "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4,
    "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
    "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12,
}

PLAZA_HOJAS = {
    "CDMX": {"TOTAL": "CDMX_TOTAL", "HOMBRES": "CDMX_HOMBRES", "MUJERES": "CDMX_MUJERES"},
    "GDL":  {"TOTAL": "GDL_TOTAL",  "HOMBRES": "GDL_HOMBRES",  "MUJERES": "GDL_MUJERES"},
    "MTY":  {"TOTAL": "MTY_TOTAL",  "HOMBRES": "MTY_HOMBRES",  "MUJERES": "MTY_MUJERES"},
}
PLAZA_NOMBRE = {"CDMX": "Cd. de México", "GDL": "Guadalajara", "MTY": "Monterrey"}
TARGET_ETIQUETA = {"TOTAL": "Total personas", "HOMBRES": "Hombres", "MUJERES": "Mujeres"}

REFERENCIA_2024 = {
    "H11": {
        "TOTAL": (9.67, 16.91, "09:00"),
        "HOMBRES": (11.09, 19.00, "08:00"),
        "MUJERES": (8.54, 16.10, "10:00"),
    },
    "H12": {
        "TOTAL": (10.76, 18.73, "09:00"),
        "HOMBRES": (12.24, 20.62, "08:00"),
        "MUJERES": (9.59, 18.48, "10:00"),
    },
    "H13": {
        "TOTAL": (7.83, 13.06, "10:00"),
        "HOMBRES": (9.49, 15.99, "10:00"),
        "MUJERES": (6.51, 10.74, "10:00"),
    },
    "H14": {
        "TOTAL": (7.15, 14.43, "08:00"),
        "HOMBRES": (8.15, 16.06, "08:00"),
        "MUJERES": (6.32, 13.09, "08:00"),
    },
}


def _texto_celda(celda: ET.Element) -> str:
    ps = celda.findall(".//text:p", NS)
    texto = "\n".join("".join(p.itertext()) for p in ps)
    if texto:
        return texto.strip()
    return celda.attrib.get(f"{{{NS['office']}}}value", "").strip()


def _filas_tabla(tabla: ET.Element):
    """Expande celdas/filas repetidas de ODS a listas de texto."""
    for fila in tabla.findall("table:table-row", NS):
        rep_fila = int(fila.attrib.get(f"{{{NS['table']}}}number-rows-repeated", "1"))
        valores = []
        for celda in fila:
            if celda.tag not in (
                f"{{{NS['table']}}}table-cell",
                f"{{{NS['table']}}}covered-table-cell",
            ):
                continue
            rep = int(celda.attrib.get(f"{{{NS['table']}}}number-columns-repeated", "1"))
            valores.extend([_texto_celda(celda)] * min(rep, 200))
        while valores and valores[-1] == "":
            valores.pop()
        for _ in range(min(rep_fila, 1000)):
            yield list(valores)


def leer_ods(ruta: str | Path):
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo de datos: {ruta}")
    with zipfile.ZipFile(ruta) as z:
        raiz = ET.fromstring(z.read("content.xml"))
    hojas = {}
    for tabla in raiz.findall(".//table:table", NS):
        nombre = tabla.attrib.get(f"{{{NS['table']}}}name", "")
        hojas[nombre] = list(_filas_tabla(tabla))
    return hojas


def _orden_estudio(estudio: str):
    partes = estudio.strip().split()
    if len(partes) != 2 or partes[0] not in MESES:
        return (9999, 99, estudio)
    return (int(partes[1]), MESES[partes[0]], estudio)


def _leer_universos(hojas):
    if "UNIVERSOS" not in hojas:
        raise ValueError("El ODS no contiene la hoja UNIVERSOS.")
    filas = [r for r in hojas["UNIVERSOS"] if r]
    if not filas or filas[0][:4] != ["PLAZA", "TARGET", "ESTUDIO", "POBLACION"]:
        raise ValueError("La hoja UNIVERSOS no tiene la estructura esperada.")
    universos = {}
    for r in filas[1:]:
        if len(r) < 4:
            continue
        try:
            pop = float(str(r[3]).replace(",", ""))
        except ValueError:
            continue
        universos[(r[0].strip(), r[1].strip().upper(), r[2].strip())] = pop
    return universos


def _leer_datos_hoja(filas, hoja):
    idx = next((i for i, r in enumerate(filas) if r and r[0] == "TIPO DE ESTUDIO"), None)
    if idx is None:
        raise ValueError(f"La hoja {hoja} no contiene el encabezado TIPO DE ESTUDIO.")
    encabezado = filas[idx]
    if len(encabezado) < 26 or encabezado[8:26] != HORAS:
        raise ValueError(f"La hoja {hoja} no contiene las 18 horas 06:00-23:00 esperadas.")

    datos = []
    for r in filas[idx + 1:]:
        if len(r) < 26 or not r[0].startswith("Mediómetro"):
            continue
        vals = []
        for x in r[8:26]:
            try:
                vals.append(float(str(x).replace(",", "")))
            except ValueError:
                raise ValueError(f"Valor horario no numérico en {hoja}: {x!r}")
        datos.append({
            "tipo": r[0], "medio": r[1], "plaza": r[2], "estudio": r[3],
            "grupo": r[4], "emisora": r[5], "siglas": r[6], "banda": r[7],
            "valores": np.asarray(vals, dtype=float),
        })
    if not datos:
        raise ValueError(f"La hoja {hoja} no contiene registros de INRAM.")
    return datos


def _curvas_mensuales(hojas, hoja):
    datos = _leer_datos_hoja(hojas[hoja], hoja)
    por_estudio = defaultdict(lambda: np.zeros(18, dtype=float))
    for r in datos:
        # Regla validada contra el Anuario 2024: sumar todas las filas exportadas
        # por INRAM en Tendencia por Horas, sin filtrar la columna BANDA.
        por_estudio[r["estudio"]] += r["valores"]
    return dict(por_estudio)


def calcular_curvas_plaza(ruta_ods: str | Path, plaza_codigo: str):
    plaza_codigo = plaza_codigo.upper()
    if plaza_codigo not in PLAZA_HOJAS:
        raise ValueError(f"Plaza desconocida: {plaza_codigo}")
    hojas = leer_ods(ruta_ods)
    universos = _leer_universos(hojas)
    resultado = {}
    estudios_ref = None

    for target, hoja in PLAZA_HOJAS[plaza_codigo].items():
        mensuales = _curvas_mensuales(hojas, hoja)
        estudios = sorted(mensuales, key=_orden_estudio)
        if estudios_ref is None:
            estudios_ref = estudios
        elif estudios != estudios_ref:
            raise ValueError(f"Los meses de {hoja} no coinciden con los demás targets de {plaza_codigo}.")

        numerador = np.zeros(18, dtype=float)
        denominador = 0.0
        for estudio in estudios:
            clave = (PLAZA_NOMBRE[plaza_codigo], target, estudio)
            if clave not in universos:
                raise ValueError(f"Falta universo para {clave}.")
            u = universos[clave]
            numerador += mensuales[estudio] * u
            denominador += u
        if denominador <= 0:
            raise ValueError(f"Universo inválido para {plaza_codigo}/{target}.")
        resultado[target] = numerador / denominador

    return resultado, estudios_ref


def calcular_curvas_h11(ruta_ods: str | Path):
    hojas = leer_ods(ruta_ods)
    universos = _leer_universos(hojas)
    resultado = {}
    todos_estudios = None

    for target in ("TOTAL", "HOMBRES", "MUJERES"):
        numerador = np.zeros(18, dtype=float)
        denominador = 0.0
        estudios_target = None
        for plaza_codigo in ("CDMX", "GDL", "MTY"):
            hoja = PLAZA_HOJAS[plaza_codigo][target]
            mensuales = _curvas_mensuales(hojas, hoja)
            estudios = sorted(mensuales, key=_orden_estudio)
            if estudios_target is None:
                estudios_target = estudios
            elif estudios != estudios_target:
                raise ValueError("Las tres plazas no contienen el mismo conjunto de meses.")
            for estudio in estudios:
                clave = (PLAZA_NOMBRE[plaza_codigo], target, estudio)
                if clave not in universos:
                    raise ValueError(f"Falta universo para {clave}.")
                u = universos[clave]
                numerador += mensuales[estudio] * u
                denominador += u
        resultado[target] = numerador / denominador
        if todos_estudios is None:
            todos_estudios = estudios_target
        elif estudios_target != todos_estudios:
            raise ValueError("Los targets no contienen el mismo conjunto de meses.")
    return resultado, todos_estudios


def calcular_figura(ruta_ods: str | Path, figura: str):
    figura = figura.upper().replace(".", "")
    if figura == "H11":
        return calcular_curvas_h11(ruta_ods)
    plaza = {"H12": "CDMX", "H13": "GDL", "H14": "MTY"}.get(figura)
    if not plaza:
        raise ValueError("Figura válida: H11, H12, H13 o H14.")
    return calcular_curvas_plaza(ruta_ods, plaza)


def resumen(curvas):
    out = {}
    for target, arr in curvas.items():
        arr = np.asarray(arr, dtype=float)
        imax = int(np.argmax(arr))
        out[target] = {
            "promedio": float(arr.mean()),
            "maximo": float(arr[imax]),
            "hora_maximo": HORAS[imax],
        }
    return out


def validar_2024(figura: str, curvas, estudios):
    figura = figura.upper().replace(".", "")
    referencia = REFERENCIA_2024.get(figura)
    if referencia is None:
        return False
    # Sólo activa la prueba si el periodo es exactamente julio 2023-junio 2024.
    esperado = [
        'Julio 2023','Agosto 2023','Septiembre 2023','Octubre 2023','Noviembre 2023','Diciembre 2023',
        'Enero 2024','Febrero 2024','Marzo 2024','Abril 2024','Mayo 2024','Junio 2024'
    ]
    if list(estudios) != esperado:
        return False
    res = resumen(curvas)
    errores=[]
    for target, (p_ref, m_ref, h_ref) in referencia.items():
        r=res[target]
        if round(r['promedio'] + 1e-12, 2) != p_ref:
            errores.append(f"{target}: promedio {r['promedio']:.6f} != {p_ref:.2f}")
        if round(r['maximo'] + 1e-12, 2) != m_ref:
            errores.append(f"{target}: máximo {r['maximo']:.6f} != {m_ref:.2f}")
        if r['hora_maximo'] != h_ref:
            errores.append(f"{target}: hora {r['hora_maximo']} != {h_ref}")
    if errores:
        raise RuntimeError("La validación 2024 no coincide:\n- " + "\n- ".join(errores))
    return True


def imprimir_resumen(figura: str, curvas, estudios):
    val = validar_2024(figura, curvas, estudios)
    print(f"Figura {figura.upper().replace('.', '')} | periodo: {estudios[0]} a {estudios[-1]}")
    for target in ("TOTAL", "HOMBRES", "MUJERES"):
        r = resumen(curvas)[target]
        print(f"  {TARGET_ETIQUETA[target]:15s} promedio={r['promedio']:.6f}%  máximo={r['maximo']:.6f}%  hora={r['hora_maximo']}")
    if val:
        print("  Validación histórica 2024: OK (coincide con el Anuario al redondear a 2 decimales).")


def graficar_radio(curvas, figura: str, salida: str | Path, ylim_max: float, ystep: float):
    """Conserva el lenguaje visual de la plantilla figura_h1.py; no reutiliza su lógica."""
    plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']

    fig, ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    plt.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.22)

    color_total = '#978bc4'
    color_mujeres = '#b35aba'
    color_hombres = '#ed8945'
    text_color = '#3c3c3b'

    x = np.arange(len(HORAS), dtype=float)
    x_smooth = np.linspace(x.min(), x.max(), 300)

    series = [
        ("TOTAL", color_total, "Total personas"),
        ("HOMBRES", color_hombres, "Hombres"),
        ("MUJERES", color_mujeres, "Mujeres"),
    ]
    for target, color, label in series:
        y = np.asarray(curvas[target], dtype=float)
        if len(y) >= 4:
            y_plot = make_interp_spline(x, y, k=3)(x_smooth)
            ax.plot(x_smooth, y_plot, color=color, label=label, linewidth=2.5, zorder=4)
        else:
            ax.plot(x, y, color=color, label=label, linewidth=2.5, zorder=4)

    ax.set_ylim(0, ylim_max)
    yticks = np.arange(0, ylim_max + 0.001, ystep)
    ax.set_yticks(yticks)
    ax.set_yticklabels(
        ["0.0" if abs(v) < 1e-12 else f"{v:.2f}" for v in yticks],
        color=text_color, size=10,
    )
    for label in ax.get_yticklabels():
        label.set_fontweight('medium')

    ax.set_xticks(x)
    ax.set_xticklabels([f"{h}:00" for h in range(6,24)], rotation=90,
                       color=text_color, size=10, weight='bold')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#7c7c7c')
    ax.spines['bottom'].set_linewidth(1)
    ax.tick_params(axis='x', length=3, pad=8, color=text_color)
    ax.tick_params(axis='y', length=0, pad=10)

    ax.set_ylabel('Proporción de personas escuchando la radio (%)',
                  labelpad=15, fontsize=10, color=text_color, fontweight='medium')
    ax.set_xlabel('Horario', labelpad=15, fontsize=10, color=text_color, fontweight='bold')

    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.26), ncol=3,
              frameon=False, prop={'weight': 'bold', 'size': 10},
              labelcolor=text_color, handlelength=2.5)

    numero = figura.upper().replace('H', 'H.')
    ax.annotate(' ', xy=(0, 1), xycoords='axes fraction', xytext=(0, 34),
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2',
                          facecolor='#4a7d75', edgecolor='none'), fontsize=2)
    ax.annotate(f'Figura {numero}.', xy=(0, 1), xycoords='axes fraction', xytext=(15, 30),
                textcoords='offset points', fontsize=14, fontweight='bold', color=text_color)
    ax.annotate('Proporción de personas que escucharon la radio por hora (%)',
                xy=(0, 1), xycoords='axes fraction', xytext=(120, 30),
                textcoords='offset points', fontsize=14, fontweight='medium', color=text_color)

    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(salida, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    return salida


def argumentos_base(figura: str):
    parser = argparse.ArgumentParser(description=f"Genera la Figura {figura} desde datos crudos INRAM consolidados.")
    base = Path(__file__).resolve().parent
    parser.add_argument('--datos', type=Path, default=base/'datos_inram_h11_h14_2024.ods',
                        help='ODS consolidado con hojas INRAM y UNIVERSOS.')
    parser.add_argument('--salida', type=Path, default=base/'output'/f"figura_{figura.lower()}.png",
                        help='PNG de salida.')
    return parser
