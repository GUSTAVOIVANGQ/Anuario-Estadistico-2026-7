# Insumos manuales

Antes de cada corrida, el programa muestra el estado y la ruta exacta de las
figuras que no pueden descargar sus datos de forma confiable.

| Figura | Carpeta | Contenido |
| --- | --- | --- |
| A.5 | `data/manual/A.5/` | `Datos_originales_y_actualizacion__1_.xlsx` y `2026_2T_Flujos_TI_AC_3.xlsx` |

Los archivos deben conservar su nombre, estructura, hojas y columnas. El
pipeline calcula su SHA-256 y los registra en la corrida.

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
