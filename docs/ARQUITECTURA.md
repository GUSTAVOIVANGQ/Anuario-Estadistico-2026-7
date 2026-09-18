# Arquitectura del proyecto

La unidad de trabajo es una figura. El orquestador nunca modifica el diseño de
una gráfica: sólo decide el orden, prepara la trazabilidad y verifica la salida.

```text
inventarios y configuración
          |
          v
orquestador secuencial
          |
          +-- adquisición y verificación de datos crudos
          +-- cálculo y tabla exacta usada en la gráfica
          +-- texto por plantilla
          +-- gráfica y, cuando aplique, página completa
          |
          v
reportes de corrida + PPTX
```

## Carpetas

- `config/`: orden, reglas de diseño y excepciones de adquisición.
- `data/raw/`: descargas automáticas, organizadas por fuente y SHA-256.
- `data/manual/`: insumos que una persona debe colocar antes de la corrida.
- `scripts/figures/`: un script por figura.
- `scripts/downloaders/`: automatizaciones especiales, como A.2.
- `templates/text/`: párrafos Jinja2 con cálculos automáticos.
- `build/figures/`: gráficas generadas.
- `build/slides/`: páginas completas opcionales, 1600 × 900.
- `reportes/<corrida>/`: evidencia para revisión y defensa.
- `entrega/`: PowerPoint final.

## Principio de aislamiento

Una falla no borra resultados previos. Cada figura registra su estado y la
corrida continúa por defecto. `--stop-on-error` permite detenerse en la primera
falla cuando se investiga una figura concreta.

