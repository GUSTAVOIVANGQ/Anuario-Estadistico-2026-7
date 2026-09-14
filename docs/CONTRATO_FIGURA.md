# Contrato de una figura

Cada archivo `scripts/figures/figura_*.py` debe declarar `FIGURE_ID` y exponer
`generate(context)`.

## Secuencia obligatoria

1. Adquirir cada fuente mediante `context.acquire_source(source_id)` o validar
   los archivos de `context.verified_manual_files()`.
2. Verificar nombres de hoja, columnas, periodo, unidades y cobertura.
3. Detectar programáticamente el último periodo con datos en la fuente
   descargada y mostrarlo en la gráfica. No se debe conservar un año de corte
   fijo heredado del anuario 2024 cuando la base contenga observaciones más
   recientes.
4. Cuando el último periodo no tenga todas las variables necesarias, mostrar
   los valores efectivamente publicados y distinguir los componentes no
   disponibles sin sustituirlos por cero ni estimarlos silenciosamente.
5. Construir la tabla final usada en la gráfica.
6. Guardarla con `context.write_data_used(...)`. El método la guarda e imprime.
7. Registrar cada fórmula con `context.record_calculation(...)`.
8. Renderizar el párrafo con `context.render_text(...)` cuando corresponda.
9. Generar el PNG conservando el diseño del anuario 2024.
10. Generar `slide_path` cuando la página del referente combine narrativa y
   gráfica en una composición específica. Esto permite replicar cada página sin
   imponer un diseño genérico.
11. Devolver `{"figure_path": ruta}` y, si existe, `slide_path`.

## Reglas visuales no negociables

- Partir del código original de la figura y hacer sólo los cambios requeridos
  por los datos y periodos nuevos.
- Conservar colores, tipografías, proporciones, leyendas y formato numérico.
- Mantener `Fuente:`, `Nota:` o `Notas:` en negritas y el contenido posterior en
  peso normal.
- Actualizar únicamente el texto necesario del pie según la fuente y el corte
  realmente usados.
- No agregar `revisión`, `control editorial` ni etiquetas equivalentes.
- No corregir o reinterpretar resultados calculados si el proceso se ejecutó
  conforme al método documentado.
