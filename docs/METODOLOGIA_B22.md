# Metodología de la figura B.22

## Fuentes crudas

- `TD_ACC_TVRES_ITE_VA.csv`, leída directamente dentro de la caché compartida
  `CRT_BIT_TODO.zip`. Se usan `K_ENTIDAD`, `ANIO`, `MES` y
  `A_NO_RESIDENCIAL_E`.
- Los 25 ZIP CSV nacionales por actividad económica de la edición DENUE más
  reciente. El script consulta el catálogo oficial de descarga masiva de INEGI,
  descarga sólo los archivos CSV y cuenta las filas del conjunto de datos por
  `cve_ent`. Una fila representa un establecimiento.
- El GeoJSON estatal se usa solamente para dibujar el mapa; no interviene en
  los cálculos.

Los archivos terminados se conservan en caché. Una corrida posterior valida su
estructura ZIP y los reutiliza sin descargarlos otra vez.

## Reconstrucción del anuario 2024

La operación original se comprobó con diciembre de 2023 en BIT y el desglose
estatal DENUE noviembre de 2023. La suma nacional fue de 455,717 accesos no
residenciales y 5,541,076 unidades económicas:

```text
455,717 / 5,541,076 * 100 = 8.2243412651
```

El redondeo a entero produce 8, exactamente el valor de la burbuja del anuario
2024. Esto confirma que el estimador es el cociente de los totales nacionales,
no el promedio simple de los indicadores estatales.

## Estimador actualizado

El script selecciona el último par `ANIO` y `MES` con accesos válidos y suma los
registros de los operadores por entidad. Para el DENUE cuenta los registros de
los 25 archivos de actividad, que son mutuamente excluyentes:

```text
indicador estatal = suma(accesos no residenciales de la entidad)
                    / establecimientos DENUE de la entidad * 100

indicador nacional = suma(accesos no residenciales de las 32 entidades)
                     / suma(establecimientos DENUE de las 32 entidades) * 100

crecimiento anual = (accesos del último corte
                     / accesos del mismo mes del año previo - 1) * 100
```

Con los descargables actuales, BIT termina en diciembre de 2024 y el DENUE
corresponde a mayo de 2026. El conteo nacional DENUE es 6,138,075. El indicador
nacional calculado es 2,065,503 / 6,138,075 × 100 = 33.6506640926, mostrado
como 34. La tasa anual de los accesos es 353.2%.

Los valores exactos se conservan en `datos_usados` y en el reporte de cálculos.
El redondeo entero sólo se aplica a la burbuja y a la clasificación visual del
mapa.
