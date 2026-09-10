# Evidencia para defensa ante sinodales

Cada corrida crea una carpeta fechada en `reportes/`. Los archivos permiten
reconstruir qué ocurrió sin depender de la memoria del equipo.

- `pipeline.log`: avance, advertencias y errores completos.
- `estado_figuras.csv`: orden y resultado de las 105 figuras.
- `fuentes_configuradas.csv`: fuente prevista para cada indicador.
- `fuentes_pendientes.csv`: fuentes que aún deben confirmarse.
- `referencias_por_figura.csv`: URL, periodo y archivo realmente utilizados.
- `calculos_por_figura.csv`: fórmula, entradas, resultado, unidad y decimales.
- `datos_usados/`: tabla final que alimentó cada gráfica.
- `manifiesto_archivos.csv`: huella SHA-256, tamaño y fecha de cada archivo.
- `resumen_ejecucion.json`: resumen estructurado para auditoría.
- `resumen_ejecucion.md`: lectura rápida de la corrida.

La carpeta de una corrida no se reutiliza. Esto evita mezclar evidencias de dos
fechas o dos versiones de datos.

