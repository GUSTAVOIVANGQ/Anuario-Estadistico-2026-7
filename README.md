 

# Anuario Estadístico 2026

Proyecto reproducible que descarga o reutiliza datos oficiales, calcula cada
indicador, imprime los resultados, genera las gráficas y conserva evidencia de
cada corrida.

La entrega automatizada de las secciones **A a G está completa: 91 figuras**.
La sección H permanece en el inventario porque requiere bases de audiencias de
Nielsen IBOPE e INRA que no están disponibles en el proyecto.

## Ejecutar

```powershell
# Preparar el ambiente una sola vez
.\preparar_entorno.ps1

# Revisar el proyecto
.\ejecutar.ps1 doctor

# Ejecutar todas las figuras disponibles y crear el PowerPoint
.\ejecutar.ps1 run --assemble

# Ejecutar sólo una figura
.\ejecutar.ps1 run --only G.1

# Ejecutar un tramo
.\ejecutar.ps1 run --from A.1 --until G.1
```

Si Windows bloquea los archivos `.ps1`, se puede ejecutar directamente:

```powershell
.\.venv\Scripts\python.exe scripts\figures\figura_g_1.py
```

En macOS o Linux se usa el mismo proyecto con Python 3.11 o superior y Node.js
20 o superior, sin instalar Office ni LibreOffice:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
(cd web && npm install --no-audit --no-fund && npm run build)
.venv/bin/python -m anuario2026 doctor
.venv/bin/python -m anuario2026 web
```

## Interfaz web React

La versión 0.27.0 incorpora una interfaz local inspirada en un flujo de edición/escaneo:
una pantalla central grande muestra cada figura conforme termina de generarse, mientras el
panel lateral permite ejecutar la figura actual, una selección o una corrida completa.

```powershell
# Una sola vez: instala Python y compila el frontend React
.\preparar_entorno.ps1

# Abre http://127.0.0.1:8765 en el navegador
.\ejecutar.ps1 web
```

La UI recibe eventos de avance del pipeline en tiempo real y, al concluir la corrida, abre
automáticamente un panel de exportación con estas opciones:

- PDF portátil de la presentación completa, sin requerir Office.
- PPTX editable de la presentación.
- ZIP con compendio de figuras JPG.
- ZIP con compendio de figuras PNG.
- ZIP con compendio de figuras SVG.

El PDF se construye directamente en Python con portada, contenido, introducción,
separadores por sección, figuras verificadas y cierre. Funciona igual en Windows, macOS y
Linux: no requiere Microsoft PowerPoint, LibreOffice ni servicios externos.
Cada script genera en una misma ejecución su PNG, JPG de alta calidad y SVG nativo. El SVG
conserva el texto como elementos `<text>` seleccionables y copiables, con posiciones
explícitas (`x`/`y` o `transform`), en vez de convertir las letras a curvas o incrustar el
PNG completo. Las capas que por su naturaleza ya son raster (por ejemplo, ciertos mapas)
pueden permanecer incrustadas sin afectar la editabilidad del resto.

Los ZIP incluyen `MANIFIESTO_EXPORTACION.csv` con el script de origen, ruta generada,
huella SHA-256 y métricas del SVG. El compendio SVG añade `TEXTOS_Y_POSICIONES.csv` para
localizar y auditar el contenido textual sin abrir cada archivo, así como las fuentes Noto
Sans del proyecto y su licencia para evitar sustituciones tipográficas al editar.

El frontend vive en `web/` y el servidor/API en `src/anuario2026/web.py`. Si se modifica
el frontend, recompílalo con `cd web; npm run build`.

## Resultados

- Gráficas reproducibles PNG, JPG y SVG editable: `build/figures/<sección>/`
- Textos automáticos: `build/text/`
- PDF portátil y PowerPoint: `entrega/`
- Datos usados, fuentes, cálculos y estado: `reportes/<corrida>/`
- Catálogo figura-fuente por corrida: `reportes/<corrida>/referencias_fuentes_figuras.csv`
- Datos descargados y reutilizables: `data/raw/`

Cada figura tiene un solo script dentro de `scripts/figures/`. Si un archivo
crudo ya existe y está verificado, el programa lo reutiliza sin descargarlo de
nuevo. A.5 es la única figura con insumos manuales en `data/manual/A.5/`.

## Capturas

### Figura G.1 - Concesiones de radiodifusión

![Figura G.1](build/figures/G/figura_g_1.png)

### Figura D.1 - Disponibilidad de TIC en los hogares

![Figura D.1](build/figures/D/figura_d_1.png)

### Figura E.2 - Inteligencia Artificial y ChatGPT

![Figura E.2](build/figures/E/figura_e_2.png)

## Evidencia para la defensa

En cada corrida se guardan automáticamente:

- referencia y fecha de cada fuente;
- huella y tamaño del archivo crudo;
- periodo detectado;
- tabla exacta usada por la gráfica;
- fórmula y resultado de cada cálculo;
- estado final de cada figura;
- catálogo consolidado `referencias_fuentes_figuras.csv` con archivo descargado, tabla real y portal de origen.

La metodología y la arquitectura permanecen disponibles en `docs/`.

## Licencia

El código nuevo usa licencia MIT. Los datos y publicaciones conservan los
términos de sus titulares.
