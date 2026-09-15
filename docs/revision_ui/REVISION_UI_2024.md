# Revisión visual 2024 aplicada al Anuario Estadístico 2026

## Alcance

Esta revisión modifica únicamente la presentación de las figuras existentes del proyecto 2026. No cambia fuentes de datos, periodos, adquisición, fórmulas, agregaciones, ponderadores ni metadatos de cálculo.

Se compararon las figuras y scripts del proyecto `Anuario-Estadistico-2024-1-main` con los identificadores equivalentes del proyecto 2026. Cuando la correspondencia fue verificable, se trasladó el lenguaje visual de la figura 2024 al script 2026, conservando los datos y textos sustantivos de 2026.

## Elementos visuales replicados

- paletas propias de cada figura, evitando una paleta global genérica;
- tipografía y color de texto institucionales;
- fondo de ejes `#F8F8FA`, neutros de ejes/rejilla y fondo blanco;
- cuadrado verde pequeño junto al encabezado de figura;
- barras rectangulares cuando el referente 2024 las usa;
- colores de líneas, áreas, dispersión, pastel y categorías según figura;
- chips numéricos únicamente donde el diseño correspondiente los utiliza o donde ya eran un elemento de la figura 2026;
- eliminación de tarjetas/paneles redondeados genéricos de 2026 cuando no existen en la figura 2024;
- leyendas sincronizadas con los colores finales de las series.

La capa común de compatibilidad está en `src/anuario2026/ui_2024.py`; los ajustes particulares que requerían geometría distinta se mantienen en el script de cada figura.

## Cobertura

Se aplicó corrección visual automática/verificada a **87 de 90** scripts de figuras existentes:

- A: A.1–A.10 (10/10)
- B: B.1–B.7 y B.9–B.25 (24/25)
- C: C.1–C.16 (16/16)
- D: D.1–D.11 (11/11)
- E: E.1–E.9 (9/9)
- F: F.1.1–F.1.3, F.2, F.4–F.16 (17/19)

## Revisión humana requerida

Estos tres scripts se dejaron **sin cambios** deliberadamente:

| Figura | Motivo |
|---|---|
| B.8 | El script de referencia 2024 `figura_b8.py` se rotula internamente como **Figura B.18** y contiene además una referencia a A.9. No es seguro asumir que corresponda visualmente a B.8. |
| F.1.4 | El script de referencia 2024 `figura_f1.4.py` se rotula como **Figura F.4**. Se evita copiar un estilo posiblemente perteneciente a otra figura. |
| F.3 | El proyecto 2024 no contiene un PNG de referencia verificable de F.3 para contrastar el script y su salida. |

Los archivos 2026 de B.8, F.1.4 y F.3 son byte a byte los originales del ZIP recibido.

## Validación

- `python -m compileall` sobre los scripts de figuras y el paquete de apoyo: correcto.
- Pruebas del proyecto corregido: **72 aprobadas, 4 fallidas**.
- Pruebas del proyecto 2026 original recibido: **72 aprobadas, 4 fallidas**.
- Las cuatro fallas son las mismas en ambos proyectos y se deben a archivos de datos crudos que no están incluidos en el ZIP (`ift_ecsi_2024_base`, `ift_tercera_encuesta_usuarios_2023_base`, `ift_mipymes_impexp_2022_base` y bases `ift_mipymes_2022/2023/2024_base`). No son regresiones de esta revisión visual.

`build/figures` venía vacío en el proyecto recibido; por ello la entrega corrige los scripts que generan las figuras y no incorpora PNG pre-renderizados que pudieran quedar desactualizados.
