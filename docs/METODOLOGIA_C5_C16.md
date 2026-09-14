# Metodología de C.5 a C.16

Las doce figuras leen tablas oficiales directamente dentro de la descarga
global `CRT_BIT_TODO.zip`. Cada script solicita la fuente al catálogo; una copia
local verificada se reutiliza y sólo se descarga cuando no existe. Ningún script
depende de otro script de figura.

El último corte disponible en las tablas usadas es diciembre de 2024. C.5 y
C.11 suman líneas por modalidad y contrastan el total con `L_TOTAL_E`; C.8 suma
los cuatro trimestres de cada año; C.9 y C.15 agrupan las participaciones
publicadas; C.10 y C.16 emplean directamente el IHH publicado. C.12 usa la serie
nacional de líneas de Internet móvil por cada 100 habitantes. C.14 suma el
tráfico por tecnología y calcula cada participación respecto de `TOTAL_TB_E`.

C.7 y C.13 toman las 32 observaciones del último corte y las vinculan por nombre
con la geometría estatal. C.6 usa la serie nacional `T_H_TELMOVIL_E`; C.7 usa
esa misma serie para el recuadro y la variación anual. C.13 obtiene su indicador
nacional y variación anual de `T_H_INTMOVIL_E`. No se imputan años históricos
ausentes en los cortes estatales.

En cada ejecución se conserva la tabla usada, el periodo detectado, la fuente,
la fórmula y el resultado de cada cálculo. Los mismos valores se imprimen en la
terminal antes de generar el PNG.
