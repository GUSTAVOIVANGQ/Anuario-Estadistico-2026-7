# Insumos manuales

Antes de cada corrida, el programa muestra el estado y la ruta exacta de las
figuras que no pueden descargar sus datos de forma confiable.

| Figura | Carpeta | Contenido |
| --- | --- | --- |
| A.5 | `data/manual/A.5/` | `Datos_originales_y_actualizacion__1_.xlsx` y `2026_2T_Flujos_TI_AC_3.xlsx` |
| H.11 a H.14 | `data/manual/H/` | `datos_inram_h11_h14_2024.ods`, con nueve hojas de ratings horarios y `UNIVERSOS` |

Los archivos deben conservar su nombre, estructura, hojas y columnas. El
pipeline calcula su SHA-256 y los registra en la corrida.

H.11 a H.14 no descargan ni validan una página web. Se incluye el ODS del ZIP
proporcionado por el usuario, con periodo julio de 2023 a junio de 2024. Para
actualizarlo, sustituye ese archivo conservando el nombre y la estructura; el
periodo se detecta desde `ESTUDIO`. El programa valida hojas, las 18 horas,
ratings, universos positivos y meses coincidentes antes de calcular. Si falta
el archivo, muestra su nombre y la ruta exacta donde colocarlo. Véase
[la metodología H.11-H.14](METODOLOGIA_H11_H14.md).

A.5 es deliberadamente manual: su script no realiza solicitudes de red. Si
falta uno de los dos libros requeridos, la ejecución muestra el nombre y la
ruta exactos donde debe colocarse.

Las figuras A.2 y A.3 ya no requieren colocación manual. A.2 integra su
descargador ENOE y A.3 automatiza desde su propio script la exportación del CSV
histórico INPC/IPCOM. Ambas reutilizan primero sus copias verificadas.

B.22 tampoco requiere colocación manual: consulta el catálogo oficial de INEGI,
descubre la edición DENUE más reciente y descarga sus ZIP CSV por actividad.
Después de la primera corrida reutiliza esa colección verificada.

A partir de A.4, las figuras que requieren información BIT deben adquirir la
misma fuente `TODO.zip`. El archivo se descarga una sola vez y cada script abre
únicamente las tablas que necesita.
