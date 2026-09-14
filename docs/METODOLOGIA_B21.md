# Metodología de la figura B.21

## Fuentes crudas

- `TD_ACC_TVRES_ITE_VA.csv`, leída directamente dentro de la caché compartida
  `CRT_BIT_TODO.zip`. Se usan `K_ENTIDAD`, `ANIO`, `MES` y
  `A_RESIDENCIAL_E`.
- `tr_endutih_hogares_anual_2025.csv`, leída dentro del ZIP oficial de datos
  abiertos ENDUTIH 2025. Se usan `CVE_ENT` y `FAC_HOG`.
- El GeoJSON estatal heredado se usa solamente para dibujar el mapa; no
  interviene en ningún cálculo.

Los archivos ya verificados se reutilizan. Sólo se descargan cuando no existe
una copia válida, salvo que se establezca `ANUARIO_FORCE_DOWNLOAD=1`.

## Reconstrucción del anuario 2024

Para comprobar el estimador se utilizó diciembre de 2023 en BIT y los hogares
ENDUTIH 2023. La suma nacional fue de 22,489,837 accesos residenciales y
38,627,319 hogares expandidos:

```text
22,489,837 / 38,627,319 * 100 = 58.2226195921
```

El redondeo a entero produce 58, exactamente el valor del globo del anuario
2024. La misma operación por entidad reproduce los extremos descritos en esa
edición: Querétaro 94, Sonora 80, Sinaloa 76, Yucatán 42, Oaxaca 38 y Chiapas
35 accesos por cada 100 hogares.

## Estimador actualizado

El script detecta el último año y mes con `A_RESIDENCIAL_E` válido, sin superar
el año de la ENDUTIH utilizada. Después suma los registros de todos los
operadores para cada `K_ENTIDAD` y calcula:

```text
penetración estatal = suma(accesos residenciales de la entidad)
                      / suma(FAC_HOG de la entidad) * 100

penetración nacional = suma(accesos residenciales de las 32 entidades)
                       / suma(FAC_HOG de las 32 entidades) * 100
```

Con los descargables actuales, BIT termina en diciembre de 2024 y el último
denominador disponible es ENDUTIH 2025. El resultado nacional es
19,133,847 / 39,677,498 * 100 = 48.223421245, que se muestra como 48.

Los valores sin redondear se conservan en `datos_usados` y en el reporte de
cálculos. El mapa aplica redondeo entero únicamente para los rótulos y rangos
visuales del referente.
