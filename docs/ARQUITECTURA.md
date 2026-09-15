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
- `assets/presentation/`: plantilla PPTX automatizable y manifest de 105 figuras.
- `reportes/<corrida>/`: evidencia para revisión y defensa.
- `entrega/`: PowerPoint final y reporte JSON de ensamblaje.

## Principio de aislamiento

Una falla no borra resultados previos. Cada figura registra su estado y la
corrida continúa por defecto. `--stop-on-error` permite detenerse en la primera
falla cuando se investiga una figura concreta.


## Ensamblaje de presentación

`anuario2026.presentation` abre la plantilla completa del Anuario 2026 y usa el
manifest para localizar cada marcador por nombre interno (`ANUARIO_FIGURE_*`).
La figura se inserta encima de la tarjeta, centrada y sin deformación. Los
marcadores de figuras que aún no existen se conservan, de modo que una entrega
parcial sigue siendo auditable. El modo `assemble --strict` exige las 105
figuras antes de producir la salida.
