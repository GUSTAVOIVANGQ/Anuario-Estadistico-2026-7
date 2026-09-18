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
