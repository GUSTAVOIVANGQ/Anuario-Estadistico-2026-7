# Metodología de las figuras B.4 a B.20

## Fuentes

Las 17 figuras reutilizan la fuente `crt_bit_todo_2025_q2`. El programa abre
directamente cada CSV dentro de `CRT_BIT_TODO.zip`; no extrae todo el paquete y
no vuelve a descargarlo cuando la copia verificada ya existe.

Cada figura está implementada íntegramente en su propio archivo de
`scripts/figures/`: adquisición, lectura del dato crudo, cálculo, registros de
auditoría, texto y render PNG. No existe una dependencia de ejecución común
para B.4 a B.20.

B.13 añade el archivo de microdatos ENDUTIH 2025 para obtener hogares
expandidos con `FAC_HOG`. B.14 añade el desglose estatal DENUE disponible en el
repositorio, edición noviembre de 2023. B.6, B.7, B.13 y B.14 reutilizan la
geometría estatal del proyecto heredado únicamente para dibujar el mapa.

## Operaciones

| Figura | Tabla BIT principal | Operación |
|---|---|---|
| B.4 | `TD_LINEAS_HIST_TELFIJA_ITE_VA.csv` | Suma de `L_TOTAL_E` en diciembre por año. |
| B.5 | `TD_PENETRACION_H_TELFIJA_ITE_VA.csv` | Serie publicada `P_H_TELFIJA_E`. |
| B.6 | `TD_PENETRACIONES_TELFIJA_ITE_VA.csv` | `P_RES_H_TELFIJA_E` por entidad. |
| B.7 | `TD_PENETRACIONES_TELFIJA_ITE_VA.csv` | `P_NRES_H_TELFIJA_E` por entidad. |
| B.8 | `TD_TRAF_HIST_TELFIJA_ITE_VA.csv` | Suma de `TRAF_E` en diciembre y conversión a millones de minutos. |
| B.9 | `TD_MARKET_SHARE_TELFIJA_ITE_VA.csv` | Suma de participación por grupo y año. |
| B.10 | `TD_IHH_TELFIJA_ITE_VA.csv` | Serie publicada `IHH_TELFIJA_E`. |
| B.11 | `TD_ACC_INTER_HIS_ITE_VA.csv` | Suma de `A_TOTAL_E` en diciembre por año. |
| B.12 | `TD_PENETRACION_H_BAF_ITE_VA.csv` | Serie publicada `P_BAF_E`. |
| B.13 | `TD_ACC_BAF_XT_XC_VA.csv` | Accesos residenciales / hogares ENDUTIH × 100. |
| B.14 | `TD_ACC_BAF_XT_XC_VA.csv` | Accesos no residenciales / unidades DENUE × 100. |
| B.15 | `TD_ACC_BAFXV_ITE_VA.csv` | Cada rango de velocidad / total validado × 100. |
| B.16 | `TD_ACC_BAF_XT_XC_VA.csv` | Suma por tecnología y segmento; participación y variación anual. |
| B.17 | `TD_MARKET_SHARE_BAF_ITE_VA.csv` | Suma de participación por grupo y año. |
| B.18 | `TD_IHH_BAF_ITE_VA.csv` | Serie publicada `IHH_BAF_E`. |
| B.19 | `TD_ACC_TVRES_HIS_ITE_VA.csv` | Suma de `A_TOTAL_E` en diciembre por año. |
| B.20 | `TD_PENETRACION_H_TVRES_ITE_VA.csv` | Serie publicada `P_H_TVRES_E`. |

Todas las figuras seleccionan el último diciembre disponible. En el ZIP actual
ese corte es diciembre de 2024. Las cifras históricas se recalculan siempre a
partir de la versión completa de la base descargada, por lo que incorporan las
revisiones que la fuente haya aplicado a periodos anteriores.

## Criterio visual

El PDF del anuario se usa como referencia de composición. Se conservan la
paleta, la jerarquía del título, el tipo de gráfica, las etiquetas y los pies de
figura. Los dibujos editoriales externos a los datos no se reproducen; el
espacio liberado amplía la gráfica sin introducir elementos nuevos.
