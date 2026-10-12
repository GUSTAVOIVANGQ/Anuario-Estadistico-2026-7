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

import hashlib
import json
import math
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

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
    # El valor numérico almacenado prevalece sobre su presentación redondeada.
    if celda.attrib.get(f"{{{NS['office']}}}value-type") == 'float':
        return celda.attrib.get(f"{{{NS['office']}}}value", '').strip()
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
            # Sólo se necesitan las primeras 26 columnas; no truncar filas con datos.
            valores.extend([_texto_celda(celda)] * min(rep, max(0, 26 - len(valores))))
        while valores and valores[-1] == "":
            valores.pop()
        if not valores:
            continue
        for _ in range(rep_fila):
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
        raise ValueError(f"Estudio/mes no reconocido: {estudio!r}")
    if not partes[1].isdigit() or not 2000 <= int(partes[1]) <= 2100:
        raise ValueError(f"Año no válido en {estudio!r}")
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
            raise ValueError(f"Fila incompleta en UNIVERSOS: {r}")
        try:
            pop = float(str(r[3]).replace(",", ""))
        except ValueError as exc:
            raise ValueError(f"Población no numérica en UNIVERSOS: {r}") from exc
        clave = (r[0].strip(), r[1].strip().upper(), r[2].strip())
        if clave in universos:
            raise ValueError(f"Universo duplicado: {clave}")
        if not math.isfinite(pop) or pop <= 0:
            raise ValueError(f"Universo inválido para {clave}: {pop}")
        _orden_estudio(clave[2])
        universos[clave] = pop
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
        if not r or not r[0].startswith("Mediómetro"):
            continue
        if len(r) != 26:
            raise ValueError(f"Registro incompleto en {hoja}: se requieren 18 horas")
        _orden_estudio(r[3])
        plaza = hoja.split('_')[0]
        if r[2].strip() != PLAZA_NOMBRE[plaza]:
            raise ValueError(f"Plaza incorrecta en {hoja}: {r[2]!r}")
        vals = []
        for x in r[8:26]:
            try:
                vals.append(float(str(x).replace(",", "")))
            except ValueError:
                raise ValueError(f"Valor horario no numérico en {hoja}: {x!r}")
        if not np.isfinite(vals).all() or min(vals) < 0:
            raise ValueError(f"Ratings inválidos en {hoja}/{r[3]}")
        datos.append({
            "tipo": r[0], "medio": r[1], "plaza": r[2], "estudio": r[3],
            "grupo": r[4], "emisora": r[5], "siglas": r[6], "banda": r[7],
            "valores": np.asarray(vals, dtype=float),
        })
    if not datos:
        raise ValueError(f"La hoja {hoja} no contiene registros de INRAM.")
    return datos


def _curvas_mensuales(hojas, hoja):
    if hoja not in hojas:
        raise ValueError(f"Falta la hoja {hoja} en el ODS manual")
    datos = _leer_datos_hoja(hojas[hoja], hoja)
    por_estudio = defaultdict(lambda: np.zeros(18, dtype=float))
    for r in datos:
        # Regla validada contra el Anuario 2024: sumar todas las filas exportadas
        # por INRAM en Tendencia por Horas, sin filtrar la columna BANDA.
        por_estudio[r["estudio"]] += r["valores"]
    if any((arr > 100).any() for arr in por_estudio.values()):
        raise ValueError(f"Suma de ratings mayor de 100% en {hoja}")
    return dict(por_estudio)


def calcular_curvas_plaza(ruta_ods: str | Path, plaza_codigo: str):
    figure_id = {'CDMX': 'H.12', 'GDL': 'H.13', 'MTY': 'H.14'}.get(plaza_codigo.upper())
    if figure_id is None:
        raise ValueError(f'Plaza desconocida: {plaza_codigo}')
    curves, studies, _ = calculate_data(Path(ruta_ods), figure_id)
    return curves, studies


def calcular_curvas_h11(ruta_ods: str | Path):
    curves, studies, _ = calculate_data(Path(ruta_ods), 'H.11')
    return curves, studies


def calcular_figura(ruta_ods: str | Path, figura: str):
    number = figura.upper().replace('.', '').removeprefix('H')
    if number not in ('11', '12', '13', '14'):
        raise ValueError('Figura válida: H11, H12, H13 o H14')
    curves, studies, _ = calculate_data(Path(ruta_ods), f'H.{number}')
    return curves, studies


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


def calculate_data(path: Path, figure_id: str):
    """Aplica el método del ZIP; conserva ratings y ponderadores sin redondear."""
    number = int(figure_id.split('.')[-1])
    plazas = {11: ('CDMX', 'GDL', 'MTY'), 12: ('CDMX',),
              13: ('GDL',), 14: ('MTY',)}[number]
    hojas = leer_ods(path)
    universos = _leer_universos(hojas)
    curvas, details, period = {}, [], None
    for target in TARGET_ETIQUETA:
        numerator = np.zeros(18, dtype=float)
        denominator = 0.0
        for plaza in plazas:
            sheet = PLAZA_HOJAS[plaza][target]
            monthly = _curvas_mensuales(hojas, sheet)
            studies = sorted(monthly, key=_orden_estudio)
            if period is None:
                period = studies
                months = [12 * _orden_estudio(s)[0] + _orden_estudio(s)[1] for s in studies]
                if any(b != a + 1 for a, b in zip(months, months[1:])):
                    raise ValueError(f"Faltan meses en el periodo de {sheet}")
            elif studies != period:
                raise ValueError(f"Los meses de {sheet} no coinciden con las demás series")
            for study in studies:
                key = (PLAZA_NOMBRE[plaza], target, study)
                if key not in universos:
                    raise ValueError(f"Falta universo para {key}")
                population = universos[key]
                numerator += monthly[study] * population
                denominator += population
                for hour, rating in zip(HORAS, monthly[study]):
                    details.append({'hoja': sheet, 'plaza': key[0], 'target': target,
                                    'estudio': study, 'hora': hour,
                                    'rating_mensual': float(rating), 'poblacion': population,
                                    'rating_por_poblacion': float(rating * population)})
        curvas[target] = numerator / denominator
    validar_2024(figure_id, curvas, period)
    return curvas, period, details


def narrative_text(root: Path, figure_id: str, curvas, estudios) -> str:
    """Modifica sólo cifras, horarios y periodo en los párrafos originales."""
    registry = json.loads((root / 'assets/presentation/narrativas_figuras_2026.json')
                          .read_text(encoding='utf-8'))
    item = next(x for x in registry['entries'] if x['figure_id'] == figure_id)
    text = item['baseline_text_2024']
    stats = resumen(curvas)
    values = iter([stats[t][k] for t in TARGET_ETIQUETA for k in ('promedio', 'maximo')])
    if len(re.findall(r'\d+\.\d+%', text)) != 6:
        raise ValueError(f"La redacción base de {figure_id} no contiene las seis cifras esperadas")
    text = re.sub(r'\d+\.\d+%', lambda m: f'{next(values):.2f}%', text)
    if figure_id == 'H.11':
        hour = stats['TOTAL']['hora_maximo']
        end = f"{int(hour[:2])+1:02d}:00"
        text = text.replace('entre las 09:00 y 10:00 horas', f'entre las {hour} y {end} horas')
    else:
        text = re.sub(r'(alcanzó su máximo a las )\d{2}:00',
                      lambda m: m[1] + stats['TOTAL']['hora_maximo'], text)
    text = re.sub(r'(su horario más alto (?:fue|ocurrió) a las )\d{2}:00',
                  lambda m: m[1] + stats['HOMBRES']['hora_maximo'], text)
    text = re.sub(r'(su principal horario fue a las |su máximo lo alcanzaron a las )\d{2}:00',
                  lambda m: m[1] + stats['MUJERES']['hora_maximo'], text)
    period = f'{estudios[0].lower()} a {estudios[-1].lower()}'
    text = text.replace('julio 2023 a junio 2024', period)
    if not validar_2024(figure_id, curvas, estudios):
        text = text.replace('muestra analizada por el IFT10', 'muestra analizada por la CRT')
    return text


def graficar_radio(curvas, figure_id: str, output: Path, estudios):
    """Conserva composición y series del ZIP, con los puntos horarios reales."""
    plt.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    fig.subplots_adjust(left=.08, right=.96, top=.85, bottom=.32)
    text_color = '#3c3c3b'
    x = np.arange(len(HORAS))
    for target, color in [('TOTAL', '#978bc4'), ('HOMBRES', '#ed8945'),
                          ('MUJERES', '#b35aba')]:
        # Segmentos entre las 18 observaciones, como en el referente 2024.
        ax.plot(x, curvas[target], color=color, label=TARGET_ETIQUETA[target], linewidth=2.5)
    number = int(figure_id.split('.')[-1])
    step = 5 if number in (11, 12) else 2
    base_limit = {11: 20, 12: 25, 13: 18, 14: 18}[number]
    limit = max(base_limit, math.ceil(max(max(a) for a in curvas.values()) / step) * step)
    ticks = np.arange(0, limit + .001, step)
    ax.set_ylim(0, limit)
    ax.set_yticks(ticks, ['0.0' if v == 0 else f'{v:.2f}' for v in ticks])
    ax.set_xticks(x, [f'{h}:00' for h in range(6, 24)], rotation=90)
    ax.tick_params(axis='x', length=3, pad=8, colors=text_color, labelsize=10)
    ax.tick_params(axis='y', length=0, pad=10, colors=text_color, labelsize=10)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color('#7c7c7c')
    ax.set_ylabel('Proporción de personas escuchando la radio (%)',
                  labelpad=15, fontsize=10, color=text_color)
    ax.set_xlabel('Horario', labelpad=15, fontsize=10, color=text_color, fontweight='bold')
    ax.legend(loc='lower center', bbox_to_anchor=(.5, -.33), ncol=3, frameon=False,
              prop={'weight': 'bold', 'size': 10}, labelcolor=text_color, handlelength=2.5)
    fig.text(.06, .92, f'Figura {figure_id}.', fontsize=14, fontweight='bold', color=text_color)
    fig.text(.16, .92, 'Proporción de personas que escucharon la radio por hora (%)',
             fontsize=14, color=text_color)
    period = f'{estudios[0].lower()} a {estudios[-1].lower()}'
    region = {11: 'Las regiones consideradas son Ciudad de México, Guadalajara y Monterrey.',
              12: 'La región considerada es Ciudad de México.',
              13: 'La región considerada es Guadalajara.',
              14: 'La región considerada es Monterrey.'}[number]
    fig.text(.06, .10, 'Fuente:', fontsize=9, fontweight='bold', color=text_color)
    fig.text(.107, .10, 'Base de Datos de INRA a través del software INRAM.',
             fontsize=9, color=text_color)
    fig.text(.06, .068, 'Nota:', fontsize=9, fontweight='bold', color=text_color)
    note = (f'Datos obtenidos de {period}. La variable de consulta es el porcentaje de encendidos (tvr%).\n'
            f'Se suman las estaciones exportadas por INRAM. {region}\n'
            'El target utilizado es hombres y mujeres de 8 años en adelante, todos los niveles socioeconómicos.\n'
            'Horario de consulta de 06:00 a 24:00 horas de lunes a domingo.')
    fig.text(.097, .068, note, fontsize=9, color=text_color, va='top', linespacing=1.3)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200, facecolor='white', edgecolor='none')
    plt.close(fig)


def generate_radio(context):
    figure_id = context.figure.figure_id
    files = context.manual_files
    if len(files) != 1:
        directory = context.project_root / 'data/manual/H/datos_inram_h11_h14_2024.ods'
        raise FileNotFoundError(f'Coloca el archivo manual en {directory}')
    path = files[0]
    print(f'  {figure_id} | Lectura del ODS manual: {path}')
    curvas, estudios, details = calculate_data(path, figure_id)
    period = f'{estudios[0].lower()} a {estudios[-1].lower()}'
    context.record_source_period('inra_radio', period, 'ULTIMO_ARCHIVO_MANUAL')
    context.write_data_used(details, 'ponderacion_mensual')
    rows = [{'target': target, 'hora': hour, 'porcentaje': float(value),
             'periodo_inicio': estudios[0], 'periodo_fin': estudios[-1]}
            for target, values in curvas.items() for hour, value in zip(HORAS, values)]
    data_path = context.write_data_used(rows)
    stats = resumen(curvas)
    context.write_data_used([{'target': t, **v} for t, v in stats.items()], 'resumen')
    historical = validar_2024(figure_id, curvas, estudios)
    if historical:
        reference = REFERENCIA_2024[figure_id.replace('.', '')]
        context.write_data_used([
            {'target': t, 'promedio_calculado': stats[t]['promedio'],
             'promedio_2024': reference[t][0], 'maximo_calculado': stats[t]['maximo'],
             'maximo_2024': reference[t][1], 'hora_calculada': stats[t]['hora_maximo'],
             'hora_2024': reference[t][2], 'coincide_a_dos_decimales': True}
            for t in TARGET_ETIQUETA], 'control_anuario_2024')
    context.record_calculation('rating_mensual',
                               'R(p,t,m,h) = suma de todas las filas INRAM de plaza, target, mes y hora; sin filtro BANDA',
                               {'archivo': path.name, 'horas': HORAS}, 'Ver ponderacion_mensual.csv', '%')
    for row in rows:
        selected = [r for r in details if r['target'] == row['target'] and r['hora'] == row['hora']]
        context.record_calculation(f"rating_{row['target']}_{row['hora']}",
                                   'sum(R(p,t,m,h) * U(p,t,m)) / sum(U(p,t,m))',
                                   {'numerador': sum(r['rating_por_poblacion'] for r in selected),
                                    'denominador': sum(r['poblacion'] for r in selected)},
                                   row['porcentaje'], '%')
    for target, values in stats.items():
        for key, value in values.items():
            context.record_calculation(f'{target}_{key}',
                                       {'promedio': 'sum(R_h) / 18', 'maximo': 'max(R_h)',
                                        'hora_maximo': 'hora del primer argmax(R_h)'}[key],
                                       {'ratings_horarios': curvas[target].tolist()}, value,
                                       'hora' if key == 'hora_maximo' else '%',
                                       None if key == 'hora_maximo' else 2)
    text = narrative_text(context.project_root, figure_id, curvas, estudios)
    text_path = context.render_text('narrativa_inram.md.j2', {'texto': text})
    graficar_radio(curvas, figure_id, context.expected_figure_path, estudios)
    imprimir_resumen(figure_id, curvas, estudios)
    return {'figure_path': str(context.expected_figure_path), 'text_path': str(text_path),
            'source_latest_period': period, 'rows_used': len(rows),
            'historical_validation_2024': historical, 'data_path': str(data_path),
            'data_sha256': hashlib.sha256(data_path.read_bytes()).hexdigest(),
            'text_sha256': hashlib.sha256(text_path.read_bytes()).hexdigest(),
            'manual_path': str(path.relative_to(context.project_root)),
            'manual_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'narrative_mode': 'manual_inram_records_only'}


