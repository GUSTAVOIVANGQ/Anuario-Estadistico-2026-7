# Metodología de la figura F.2

## Fuente y corte

La figura utiliza los microdatos trimestrales de la Encuesta Nacional de
Ocupación y Empleo (ENOE) del INEGI. El corte actual es el segundo trimestre de
2026, último trimestre publicado al preparar esta versión. El segundo trimestre
de 2024 se conserva exclusivamente como referencia de validación.

Los archivos ZIP se solicitan mediante el catálogo de fuentes del proyecto. Si
la copia local existe y supera la verificación de integridad, no se descarga de
nuevo.

## Universo y cálculo

1. Se leen las tablas SDEM y COE1 de cada ZIP.
2. Las personas se cruzan uno a uno con las doce llaves completas de vivienda,
   hogar, entrevista, periodo y renglón.
3. Se conserva la población ocupada con `CLASE1 = 1`, `CLASE2 = 1` y factor
   trimestral positivo.
4. `P4A` identifica Radiodifusión con SCIAN 515 y Telecomunicaciones con SCIAN
   517.
5. El total por sexo es la suma de `FAC_TRI`. El porcentaje divide la suma del
   sexo entre la suma de mujeres y hombres del mismo sector y multiplica por
   cien.

## Prueba de comparabilidad

Antes de calcular 2026, el script procesa los microdatos 2024-T2 y exige
reproducir exactamente los totales publicados: 54,694 personas en
radiodifusión y 247,172 en telecomunicaciones. Los porcentajes redondeados deben
ser 45% mujeres y 55% hombres en radiodifusión, y 32% mujeres y 68% hombres en
telecomunicaciones. Si falla cualquiera de esas seis comprobaciones, la figura
no se genera.
