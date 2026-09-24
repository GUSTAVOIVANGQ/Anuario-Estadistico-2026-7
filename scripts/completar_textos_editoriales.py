"""Completa los campos editoriales con fuente y periodo explícitos.

El PDF de 2024 aporta definiciones y método; las tablas A-G se generan de los
datos usados por la corrida documentada en el registro de narrativas.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "anuarioestadistico2024vf_0.pdf"
NARRATIVES = ROOT / "assets/presentation/narrativas_figuras_2026.json"
TARGET = ROOT / "assets/presentation/textos_editoriales_2026.json"
MANIFEST = ROOT / "assets/presentation/anuario_estadistico_2026_manifest.json"


def clean(text: str) -> str:
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl").replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def blocks(pdf, number: int, *, x_min=0, x_max=1600, y_min=80, y_max=800):
    selected = [
        block for block in pdf[number - 1].get_text("blocks")
        if block[6] == 0 and x_min <= block[0] < x_max and y_min <= block[1] < y_max
    ]
    return sorted(selected, key=lambda block: (block[0] // 700, block[1]))


def block_paragraphs(pdf, number: int, **limits) -> str:
    return "\n\n".join(clean(block[4]) for block in blocks(pdf, number, **limits))


def figure_data_root() -> Path:
    registry = json.loads(NARRATIVES.read_text(encoding="utf-8"))
    return ROOT / Path(registry["reference_run"]) / "datos_usados"


def keyed_rows(data_root: Path, figure: str) -> dict[int, dict[str, str]]:
    path = data_root / (figure + "_datos_usados.csv")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return {int(row["K_ENTIDAD"]): row for row in csv.DictReader(stream)}


def tabular(headers: list[str], rows: list[list[str]]) -> str:
    return "\n".join("\t".join(row) for row in [headers, *rows])


def summary_tables(data_root: Path) -> dict[str, str]:
    b6, b7, b13, b14, b21, b22, c7, c13 = (
        keyed_rows(data_root, key)
        for key in ("b_6", "b_7", "b_13", "b_14", "b_21", "b_22", "c_7", "c_13")
    )
    states = sorted(set(b6) & set(b7) & set(b13) & set(b14) & set(b21) & set(b22) & set(c7) & set(c13))
    if len(states) != 32:
        raise ValueError(f"El anexo estatal requiere 32 entidades; hay {len(states)}")
    names = {key: b13[key]["ENTIDAD"] for key in states}
    t1 = [
        [names[k], f'{int(float(b13[k]["FAC_HOG"])):,}', str(round(float(b6[k]["valor"]))),
         str(round(float(b13[k]["valor"])))] for k in states
    ]
    t2 = [
        [names[k], str(round(float(b7[k]["valor"]))), str(round(float(b14[k]["valor"]))),
         str(round(float(b21[k]["penetracion"]))), str(round(float(b22[k]["penetracion"])))]
        for k in states
    ]
    t3 = [
        [names[k], str(round(float(c7[k]["valor"]))), str(round(float(c13[k]["valor"])))]
        for k in states
    ]
    g1_path = data_root / "g_1_datos_usados.csv"
    with g1_path.open(encoding="utf-8-sig", newline="") as stream:
        g1 = list(csv.DictReader(stream))
    t4 = [
        [row["servicio"], row["categoria"], row["concesiones"], row["anio"]]
        for row in sorted(g1, key=lambda row: ("AM FM TDT".split().index(row["servicio"]), int(row["orden"])))
    ]
    return {
        "ANEXO_I_1": tabular(
            ["Entidad", "Hogares 2025", "Tel. fija /100", "Internet /100"], t1,
        ),
        "ANEXO_I_2": tabular(
            ["Entidad", "Tel. fija no res.", "Internet no res.", "TV residencial", "TV no res."], t2,
        ),
        "ANEXO_I_3": tabular(
            ["Entidad", "Telefonía /100 hab.", "Internet /100 hab."], t3,
        ),
        "ANEXO_I_4": tabular(
            ["Servicio", "Tipo de concesión", "Concesiones", "Corte"], t4,
        ),
    }


def editorial_text(pdf) -> dict[str, str]:
    narratives = {
        row["figure_id"]: row["updated_text"]
        for row in json.loads(NARRATIVES.read_text(encoding="utf-8"))["entries"]
    }
    slots: dict[str, str] = {}
    slots["LEGALES_1"] = (
        "El Anuario Estadístico 2026 conserva la estructura del Anuario Estadístico 2024 "
        "publicado por el Instituto Federal de Telecomunicaciones (IFT). Las cifras nuevas se "
        "atribuyen a la fuente y al periodo indicados en cada figura. Se utilizaron series del "
        "Banco de Información de Telecomunicaciones (BIT) de la Comisión Reguladora de "
        "Telecomunicaciones (CRT), datos del Instituto Nacional de Estadística y Geografía "
        "(INEGI) y otras fuentes identificadas en las notas. Las cifras reportadas por los "
        "operadores pueden ser revisadas por la autoridad que las publica.\n\n"
        "Las encuestas de personas usuarias y MiPymes se citan con su año original cuando "
        "no hay una edición comparable verificada. Las figuras de TIC y perspectiva de género "
        "emplean, según el indicador, ENDUTIH 2025, MOCIBA 2025, ENOE y encuestas previas. "
        "No se extrapola una encuesta de 2023 o 2024 al año 2026.\n\n"
        "La sección H reproduce la redacción y los resultados de julio de 2023 a junio de "
        "2024 del anuario de referencia. Para televisión se conserva la mención de Nielsen "
        "IBOPE México y el software MSS TV; para radio, la de INRA y el software INRAM. "
        "No se tuvo acceso a las bases licenciadas para recalcular esas 14 figuras. Esta "
        "conservación de texto histórico permite actualizarlas cuando exista acceso."
    )
    legal2 = [clean(block[4]) for block in blocks(pdf, 4, x_min=470, y_min=120, y_max=400)]
    legal2[-1] = re.sub(r" que puede descargar descargar en https?://.*", ".", legal2[-1])
    slots["LEGALES_2"] = (
        "Nota metodológica histórica de audiencias (Anuario Estadístico 2024):\n\n"
        + "\n\n".join(legal2)
        + "\n\nLos datos de esta nota corresponden al periodo original y no constituyen una medición nueva de 2026."
    )

    for page, left, right in [(5, "GLOSARIO_1_A", "GLOSARIO_1_B"), (6, "GLOSARIO_2_A", "GLOSARIO_2_B")]:
        start = 205 if page == 5 else 85
        slots[left] = "\n".join(clean(b[4]) for b in blocks(pdf, page, x_min=470, x_max=1000, y_min=start, y_max=815))
        slots[right] = "\n".join(clean(b[4]) for b in blocks(pdf, page, x_min=1000, x_max=1550, y_min=start, y_max=815))
    slots["GLOSARIO_1_A"] = slots["GLOSARIO_1_A"].replace(
        "BIT: Banco de Información de Telecomunicaciones",
        "BIT: Banco de Información de Telecomunicaciones\nCRT: Comisión Reguladora de Telecomunicaciones",
    )
    slots["GLOSARIO_1_B"] = slots["GLOSARIO_1_B"].replace(
        "IFT: Instituto Federal de Telecomunicaciones",
        "IFT: Instituto Federal de Telecomunicaciones (autor histórico de la edición 2024)",
    )

    slots["INTRODUCCION_1"] = (
        "El Anuario Estadístico 2026 actualiza los indicadores del Anuario 2024 y conserva sus "
        "ocho secciones. Presenta resultados nacionales y, cuando la fuente lo permite, por "
        "entidad federativa. Cada gráfica registra el periodo observado, la fuente, los datos "
        "empleados y el cálculo reproducible.\n\n"
        "1. Indicadores económicos de las TyR. Incluye PIB, empleo, precios, inversión, "
        "ingresos y gasto de los hogares en servicios fijos y móviles.\n\n"
        "2. Servicios fijos de telecomunicaciones. Presenta accesos y líneas, penetración "
        "por hogares o unidades económicas, tecnologías de acceso, tráfico y concentración "
        "de telefonía fija, Internet fijo y televisión restringida.\n\n"
        "3. Servicios móviles de telecomunicaciones. Comprende espectro, uso, líneas por "
        "habitante, tráfico, participación y concentración de los mercados móviles.\n\n"
        "4. Tecnologías de la información y comunicación. Utiliza la ENDUTIH 2025 para "
        "disponibilidad y uso de TIC; conserva el año original de otras encuestas cuando "
        "no hay una actualización comparable."
    )
    slots["INTRODUCCION_2"] = (
        "5. Personas usuarias de servicios de telecomunicaciones. Reúne satisfacción, "
        "servicios contratados por MiPymes y resultados de estudios sobre inteligencia "
        "artificial, con el año de cada encuesta visible.\n\n"
        "6. Indicadores con perspectiva de género. Desagrega actividades digitales, empleo "
        "y ciberacoso por sexo con datos de ENDUTIH, ENOE, MOCIBA y encuestas de personas usuarias.\n\n"
        "7. Indicadores de radiodifusión. Presenta concesiones AM, FM y TDT según el corte "
        "verificado en la fuente.\n\n"
        "8. Consumo de radio y televisión. Reproduce el análisis de julio de 2023 a junio "
        "de 2024 del Anuario 2024 mientras no se disponga de las bases de Nielsen IBOPE / "
        "MSS TV e INRA / INRAM.\n\n"
        "Los anexos contienen resumen de indicadores por entidad federativa, definiciones, "
        "metodologías y métodos de cálculo. Las observaciones no tienen un corte único: "
        "el año de edición no sustituye el año de referencia de cada indicador. Las series "
        "del BIT y las encuestas del INEGI se consultan mediante sus canales oficiales "
        "actuales. El BIT estatal y la calculadora de probabilidades citados en 2024 no se "
        "presentan como enlaces operativos de esta edición."
    )

    slots.update({
        "PUNTOS_CLAVE_ECONOMICOS": (
            "En el segundo trimestre de 2026, las TyR aportaron 1.7% del PIB de México "
            "(INEGI, figura A.1). La ENOE registró 279,069 personas empleadas en TyR, "
            "87% en telecomunicaciones (figura A.2). Los cortes de inversión e ingresos "
            "son anteriores y se identifican en sus respectivas figuras."
        ),
        "PUNTOS_CLAVE_ESPECTRO": "A agosto de 2024 se registraron 645 MHz de espectro asignado a servicios móviles en México (figura C.1, BIT).",
        "PUNTOS_CLAVE_MOVILES": (
            "Al cierre de 2024 había 115 líneas de telefonía móvil y 102 líneas de Internet "
            "móvil por cada 100 habitantes a nivel nacional (figuras C.6 y C.12, BIT e INEGI)."
        ),
        "PUNTOS_CLAVE_AUDIENCIAS": (
            "Las cifras de exposición a radio y televisión corresponden a julio de 2023-junio "
            "de 2024. Se conserva la redacción del Anuario 2024 y la referencia a INRA / "
            "INRAM y Nielsen IBOPE / MSS TV hasta contar con sus bases licenciadas."
        ),
        "PUNTOS_CLAVE_FIJOS": (
            "A diciembre de 2024 se estimaron 56 líneas residenciales de telefonía fija y "
            "64 accesos residenciales de Internet fijo por cada 100 hogares a nivel nacional "
            "(figuras B.6 y B.13, BIT con denominadores de INEGI)."
        ),
        "PUNTOS_CLAVE_GENERO": (
            "La ENDUTIH 2025 registró uso de Internet de 86% de las mujeres y 87% de los "
            "hombres de 6 años o más (figura F.1.2). El MOCIBA 2025 proporciona el corte "
            "actualizado de ciberacoso (figura F.3)."
        ),
        "PUNTOS_CLAVE_TIC": (
            "Según la ENDUTIH 2025, 95% de los hogares disponía de teléfono celular y 85% "
            "de televisor digital (figura D.1, INEGI)."
        ),
        "PUNTOS_CLAVE_USUARIOS": (
            "El índice de satisfacción de personas usuarias utiliza la Encuesta 2024; "
            "los resultados de MiPymes conservan el año de la encuesta original donde "
            "no existe una actualización comparable verificada (sección E)."
        ),
    })

    for index, key in enumerate(("SMARTPHONE", "INTERNET", "COMPUTADORA", "REDES"), 1):
        raw = narratives[f"F.1.{index}"]
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚ])", raw)
        slots[f"F_OVERVIEW_{key}"] = " ".join(sentences[:2]).strip()

    slots.update({
        "HERRAMIENTA_1": "BIT de la CRT: consulta estadísticas de telecomunicaciones, radiodifusión y TIC. https://bit.crt.gob.mx/BitWebApp/",
        "HERRAMIENTA_2": "Descarga de datos del BIT: tablas y metadatos para reproducir indicadores por servicio y entidad. https://bit.crt.gob.mx/BitWebApp/descargaDatos.xhtml",
        "HERRAMIENTA_3": "Información estadística del BIT: tableros nacionales, estatales y municipales disponibles en el portal vigente. https://bit.crt.gob.mx/BitWebApp/informacionEstadistica.xhtml",
        "HERRAMIENTA_4": "Acervo histórico del IFT y notas metodológicas: consultar desde el portal de herramientas de la CRT. La antigua calculadora de probabilidades no se cita aquí como servicio activo. https://portal.crt.gob.mx/herramientas",
    })

    for page in range(121, 126):
        index = page - 120
        limits = {"y_min": 250 if page == 121 else 85, "y_max": 795}
        slots[f"ANEXO_II_{index}_A"] = "\n\n".join(
            clean(b[4]) for b in blocks(pdf, page, x_min=65, x_max=800, **limits)
        )
        if page == 125:
            slots[f"ANEXO_II_{index}_B"] = (
                "Universos históricos de la medición de audiencias (julio de 2023 a junio de 2024): "
                "televisión, personas de 4 años o más con televisor funcional en el hogar; radio, "
                "personas de 8 años o más. La cobertura de televisión fue de 28 ciudades y la "
                "de radio, Ciudad de México, Guadalajara y Monterrey. La fuente original es el "
                "Anuario Estadístico 2024, con datos de Nielsen IBOPE e INRA."
            )
        else:
            slots[f"ANEXO_II_{index}_B"] = "\n\n".join(
                clean(b[4]) for b in blocks(pdf, page, x_min=800, x_max=1550, **limits)
            )
    slots["ANEXO_II_4_A"] = slots["ANEXO_II_4_A"].replace(
        "precios constantes de 2013", "precios constantes de 2018 en la serie actual de la figura A.1"
    )
    slots["ANEXO_II_1_B"] = slots["ANEXO_II_1_B"].replace(
        "https://www.inegi.org.mx/app/mapa/denue/default. aspx",
        "https://www.inegi.org.mx/app/mapa/denue/",
    )
    slots["ANEXO_II_2_A"] = (
        slots["ANEXO_II_2_A"]
        .replace("https://www.inegi.org.mx/programas/ dutih/2022/", "https://www.inegi.org.mx/programas/endutih/2025/")
        .replace("https:// www.inegi.org.mx/programas/enigh/nc/2022/", "https://www.inegi.org.mx/programas/enigh/nc/2024/")
        .replace("Gobierno: La LFTR ordena", "Gobierno (definición histórica de 2024): La LFTR ordenaba")
    )
    slots["ANEXO_II_2_B"] = slots["ANEXO_II_2_B"].replace(
        "https://www.dof.gob. mx/nota_detalle.php?codigo=5645045&fecha=09/03/2022#gsc.tab=0",
        "https://www.dof.gob.mx/nota_detalle.php?codigo=5645045&fecha=09/03/2022",
    )
    slots["ANEXO_II_2_B"] = slots["ANEXO_II_2_B"].replace(
        "El INPC se presenta en este estudio con precios en base diciembre de 2013.",
        "La base de la serie del INPC se indica en la fuente del INEGI usada para la figura A.3.",
    )

    slots["ANEXO_III_1"] = (
        "Servicios de telecomunicaciones e índices de precios. "
        "Las series actuales provienen del BIT de la CRT, del INEGI y de los registros "
        "documentados por figura. Para tasas por cada 100 hogares o habitantes se divide "
        "el número de accesos o líneas entre el denominador compatible con el corte y se "
        "multiplica por 100. Para tasas no residenciales se utilizan las unidades económicas "
        "del DENUE. Los servicios móviles pueden tener más líneas que habitantes. "
        "El INPC y el índice de Comunicaciones se calculan con las series publicadas por el "
        "INEGI; se indica por separado el último periodo disponible de cada una."
    )
    slots["ANEXO_III_2"] = (
        "Ingreso y gasto de los hogares en telecomunicaciones fijas y móviles. "
        "Se conserva el método del Anuario 2024 y se actualiza a la ENIGH 2024: los hogares "
        "se ordenan por ingreso corriente trimestral y se agrupan en diez deciles; se "
        "identifican los gastos en servicios fijos y móviles de cada hogar; el gasto promedio "
        "se obtiene dividiendo el gasto total entre los hogares del decil, y su proporción "
        "respecto al ingreso se expresa en porcentaje. Los valores y archivos usados por "
        "las figuras A.7 a A.10 quedan registrados por corrida."
    )
    slots["ANEXO_III_3"] = (
        "Consumo de radio y televisión. Se conservan sin recálculo las particularidades "
        "metodológicas del Anuario 2024 para el periodo julio de 2023-junio de 2024. "
        "Las audiencias de televisión proceden de Nielsen IBOPE México y MSS TV; las de "
        "radio, de INRA e INRAM. La exposición y el rating tienen definiciones distintas; "
        "las series anteriores al cambio de bases de 2017-2018 no se comparan linealmente. "
        "No se dispone de las bases licenciadas para una estimación de 2026.\n\n"
        "ENDUTIH. Las figuras actualizadas usan la edición 2025 del INEGI con sus factores "
        "de expansión y universo de personas de 6 años o más. Las encuestas de otros años "
        "se identifican expresamente en cada figura."
    )
    slots["ANEXO_III_4"] = (
        "ENOE. El empleo de telecomunicaciones y radiodifusión se obtiene de la Encuesta "
        "Nacional de Ocupación y Empleo del INEGI, con el trimestre y la clasificación "
        "económica señalados en las figuras A.2 y F.2.\n\n"
        "PIB. Se usa la serie del INEGI a precios constantes de 2018 para el PIB nacional y "
        "los subsectores de telecomunicaciones y radiodifusión. La participación de las TyR "
        "es la suma de ambos subsectores dividida entre el PIB nacional del mismo trimestre, "
        "multiplicada por 100. El último corte validado consta en la figura A.1."
    )
    slots["ANEXO_IV_METODOS_CALCULO"] = tabular(
        ["Indicador", "Método de cálculo"],
        [
            ["Concentración de mercado (IHH)", "Suma de (participación de cada grupo económico en %)^2"],
            ["Accesos residenciales por 100 hogares", "Accesos residenciales / hogares ENDUTIH del corte × 100"],
            ["Accesos no residenciales por 100 UE", "Accesos no residenciales / unidades económicas DENUE × 100"],
            ["Líneas móviles por 100 habitantes", "Líneas móviles / población compatible con el corte × 100"],
            ["Minutos de uso promedio mensual", "Suma de minutos mensuales / líneas promedio del periodo"],
            ["Tráfico promedio de Internet móvil", "Suma de GB mensuales / líneas promedio del periodo"],
            ["Margen del sector", "Ingresos brutos − egresos operativos"],
        ],
    )
    slots["CONTACTO_INSTITUCIONAL"] = (
        "Fuentes, periodos y métodos de cálculo se indican en cada figura. "
        "BIT: https://bit.crt.gob.mx/BitWebApp/"
    )
    slots.update(summary_tables(figure_data_root()))
    return slots


def main() -> None:
    with fitz.open(SOURCE) as pdf:
        slots = editorial_text(pdf)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = {item["key"] for item in manifest["editorial_slots"]}
    if set(slots) != expected:
        raise ValueError(f"Campos faltantes: {sorted(expected-set(slots))}; extras: {sorted(set(slots)-expected)}")
    source_notes = {
        "ANEXO_I_1": "Fuente: BIT, diciembre de 2024; hogares ENDUTIH 2025 (INEGI).",
        "ANEXO_I_2": "Fuente: BIT, diciembre de 2024; denominadores ENDUTIH 2025 y DENUE (INEGI). Tasas por 100 hogares o UE.",
        "ANEXO_I_3": "Fuente: BIT, diciembre de 2024; población utilizada en las figuras C.7 y C.13.",
        "ANEXO_I_4": "Fuente: datos usados en la figura G.1; corte diciembre de 2023. No representa una actualización de 2026.",
        "ANEXO_IV_METODOS_CALCULO": "Cada figura identifica el corte y denominador exactos aplicados en la corrida.",
    }
    TARGET.write_text(
        json.dumps({"schema_version": 2, "reference_pdf": SOURCE.name, "slots": slots, "source_notes": source_notes}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Campos editoriales completos: {len(slots)}")


if __name__ == "__main__":
    main()
