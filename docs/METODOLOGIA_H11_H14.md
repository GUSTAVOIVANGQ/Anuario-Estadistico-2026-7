# Figuras H.11 a H.14: audiencias de radio

La integración procede de `h11_h14_inram_scripts.zip` suministrado por el
usuario. Conserva el método de `inram_radio_core.py`; las cuatro entradas del
pipeline comparten `src/anuario2026/inram_radio.py`. La fuente se coloca en
`data/manual/H/datos_inram_h11_h14_2024.ods`. No se consulta internet.

El ODS conserva las hojas `CDMX_TOTAL`, `CDMX_HOMBRES`, `CDMX_MUJERES`,
`GDL_TOTAL`, `GDL_HOMBRES`, `GDL_MUJERES`, `MTY_TOTAL`, `MTY_HOMBRES`,
`MTY_MUJERES` y `UNIVERSOS`. Los campos iniciales de los ratings son
`TIPO DE ESTUDIO`, `MEDIO`, `PLAZA`, `ESTUDIO`, `GRUPO`, `EMISORA`, `SIGLAS`
y `BANDA`, seguidos de las 18 horas `06:00` a `23:00`. `UNIVERSOS` contiene
`PLAZA`, `TARGET`, `ESTUDIO` y `POBLACION`. Se conserva el valor numérico
almacenado en ODS, incluso si el texto visible tiene menos decimales.

Para plaza p, target t, mes m y hora h:

- `R(p,t,m,h) = suma de los ratings de todas las filas exportadas por INRAM`.
  Se conserva la regla del ZIP: no se filtra `BANDA`.
- `R(t,h) = sum(R(p,t,m,h) * U(p,t,m)) / sum(U(p,t,m))`.
  H.11 combina las tres plazas; H.12, H.13 y H.14 usan sólo CDMX,
  Guadalajara y Monterrey, respectivamente.
- `Promedio(t) = sum(R(t,h)) / 18`. El máximo y su horario se obtienen de
  las observaciones horarias, sin redondeo intermedio. Si empatan, se conserva
  la primera hora, como en el script proporcionado.

Se usa el periodo completo presente en el ODS, en orden cronológico. No se
impone 2026 ni se recorta silenciosamente a doce meses. Las series que
participan deben compartir meses consecutivos y sus universos. Un archivo
incompleto, un universo ausente, duplicado, no finito o no positivo, o un rating
no numérico, no finito o negativo detiene esa figura con un diagnóstico.

Cuando el periodo es exactamente julio de 2023 a junio de 2024 se exige
coincidencia con los promedios, máximos y horarios de las páginas 112 a 115
del Anuario Estadístico 2024, a sus dos decimales publicados. Estas cifras
sólo controlan el cálculo; no sustituyen los ratings del ODS.

| Figura | Promedios total / hombres / mujeres (%) | Máximos (%) | Horarios |
| --- | --- | --- | --- |
| H.11 | 9.67 / 11.09 / 8.54 | 16.91 / 19.00 / 16.10 | 09:00 / 08:00 / 10:00 |
| H.12 | 10.76 / 12.24 / 9.59 | 18.73 / 20.62 / 18.48 | 09:00 / 08:00 / 10:00 |
| H.13 | 7.83 / 9.49 / 6.51 | 13.06 / 15.99 / 10.74 | 10:00 / 10:00 / 10:00 |
| H.14 | 7.15 / 8.15 / 6.32 | 14.43 / 16.06 / 13.09 | 08:00 / 08:00 / 08:00 |

Cada corrida guarda el ODS identificado por SHA-256, la suma mensual y sus
ponderadores (`ponderacion_mensual.csv`), los 54 valores horarios finales,
el resumen y el control histórico cuando aplica. Registra las fórmulas y
genera PNG, JPG y SVG con texto editable.

La gráfica conserva las series, colores y estructura del script recibido.
Une las observaciones horarias con segmentos como en el PDF 2024; se elimina
la interpolación cúbica del ZIP para evitar aparentar observaciones o máximos
entre horas. El eje vertical conserva su escala salvo que datos nuevos la
superen. Se agregan la fuente y la nota con el periodo observado.

La narrativa parte de los párrafos 2024 y cambia únicamente porcentajes,
horarios y periodo. El ensamblaje verifica sus huellas de datos, texto y ODS;
`assemble --strict` rechaza resultados desactualizados tras sustituir el archivo
manual. H.11-H.14 se insertan como SVG calculados, sin recurrir a recortes
históricos si falta su generación. H.1-H.10 mantienen el tratamiento existente.

```powershell
.\ejecutar.ps1 run --from H.11 --until H.14 --assemble
```

El archivo incluido contiene observaciones de 2023-2024. La edición se llama
2026, pero no se atribuye ese año a los datos de radio. Su procedencia es el
archivo entregado por el usuario; esta integración no certifica una descarga
web ni que existan observaciones más recientes fuera de ese archivo.
