# Ajustes de gráficas 2026

Fecha de revisión: 17 de septiembre de 2026.

## Cambios aplicados

1. Los pies de fuente que comenzaban con `IFT` o `CRT` se normalizan a `Elaborado por CRT` desde el flujo central de generación.
2. A.6 incorpora los ingresos trimestrales disponibles de 2024. Como la tabla fuente no contiene egresos ni margen para ese año, las cuatro barras se muestran como ingreso total sin desglose, en gris, y no se imputan datos inexistentes.
3. B.1 coloca el total de hogares debajo de la gráfica circular, siguiendo la composición de B.2.
4. B.5 incluye correctamente la etiqueta 2024 en la última barra.
5. B.8 adopta la gama cromática institucional usada por B.11.
6. B.9, B.15, B.17, B.24, C.14 y G.1 colocan valores fuera de las barras mediante líneas guía rectas.
7. B.15 recupera el encabezado del total nacional y la tasa de crecimiento anual. La tasa de 27.0% se obtiene con 22,652,027 accesos en 2023, publicados en la página 35 del Anuario 2024, y 28,764,249 accesos en 2024.
8. B.16 incluye la leyenda completa en cada panel.
9. B.19 eleva la etiqueta de 2024 y la conecta al último punto mediante una línea recta.
10. B.23 mantiene todas las etiquetas y líneas guía dentro del recuadro de su panel.
11. B.24 y C.14 usan la paleta categórica de B.17.
12. C.3 y C.4 agregan líneas guía para cada región circular.
13. C.6 incorpora la leyenda `Líneas por cada 100 habitantes`.
14. C.8 incorpora `Millones de minutos` y deja etiquetas numéricas únicamente en el primer y último año.
15. C.12 incorpora la leyenda `Líneas móviles de acceso a Internet por cada 100 habitantes`.
16. E.5 usa la gama cromática de E.1.
17. F.3 adopta el tratamiento visual de D.4.
18. F.5 adopta el tratamiento visual de F.8.

## Verificación

- Los 21 PNG afectados se regeneraron desde los datos usados de la última corrida disponible.
- El PPTX ajustado conserva 119 diapositivas y reemplaza las 21 figuras afectadas.
- La validación estructural del PPTX no encontró errores de paquete, tamaño de diapositiva, tipografías aprobadas ni geometría.
- La compilación de los módulos Python terminó sin errores.
- La suite obtuvo 81 pruebas aprobadas. Cuatro pruebas históricas no pudieron ejecutarse porque el archivo entregado no incluye sus bases crudas de ECSI y MiPymes.

## Revisión 0.26.0 — ajustes solicitados

19. El marcador junto a `Figura ...` se normaliza desde el flujo central con el patrón de A.1: verde `#4a7d75`, ancho `0.007`, alto `0.018`, esquinas redondeadas y posición relativa uniforme. La regla cubre marcadores heredados implementados como parche, glifo o caja de texto.
20. Cada corrida genera el reporte adicional `reportes/<corrida>/referencias_fuentes_figuras.csv`, con las seis columnas del archivo de referencia entregado: figura, `source_id`, propietario, archivo descargado, archivo/tabla real y portal de origen.
21. Se sustituyeron íntegramente los scripts `figura_e_4.py`, `figura_f_14.py`, `figura_f_1_1.py`, `figura_f_1_2.py`, `figura_f_1_3.py` y `figura_f_1_4.py` por las versiones CRT/sinodales suministradas para esta revisión.

### Verificación 0.26.0

- Los 91 PNG existentes de A a G se normalizaron también en disco para que el ensamblaje con imágenes ya generadas use el marcador estándar sin exigir una nueva descarga de datos.
- Los seis scripts sustituidos son byte a byte iguales a los archivos entregados (renombrados a los nombres esperados por el proyecto) y compilan sin errores.
- Una corrida `--dry-run` generó `referencias_fuentes_figuras.csv` con 130 registros y contenido equivalente al CSV de referencia entregado.
- Las pruebas nuevas del marcador y del reporte pasan correctamente.
- La suite completa obtuvo 83 pruebas aprobadas; cuatro pruebas históricas no pudieron ejecutarse porque esta copia del proyecto no incluye las bases crudas ECSI/MiPymes/encuestas que esas pruebas buscan en `data/raw/`.
