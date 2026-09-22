 

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

En macOS o Linux se usa el mismo proyecto con Python 3.11 o superior, Node.js
20 o superior y LibreOffice para convertir la presentación a PDF:

```bash
chmod +x preparar_entorno.sh ejecutar.sh
./preparar_entorno.sh
./ejecutar.sh doctor
./ejecutar.sh web
```

En macOS puede instalarse el convertidor con `brew install --cask libreoffice`; en
Ubuntu o Debian, con `sudo apt-get install libreoffice`. En Windows basta PowerPoint o
LibreOffice.

## Interfaz web React

La versión 0.30.0 mantiene el PPTX de 0.29.0 y corrige la exportación PDF: las figuras ya no se convierten a través de PowerPoint/LibreOffice. El PDF usa directamente los SVG originales de `build/figures`, sin generar un segundo SVG por figura. Los párrafos narrativos del PPTX continúan como texto nativo, editable, buscable y copiable. La redacción base proviene del Anuario Estadístico 2024 y sólo se actualizan los registros respaldados por la corrida actual; cada narrativa queda auditada contra la huella SHA-256 de su archivo `datos_usados`. La interfaz local incorporada en 0.27.0 continúa disponible:
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

- PDF de entrega compuesto con la presentación como base visual y con cada figura insertada directamente desde su SVG original, conservando vectores y texto de figura buscable y copiable.
- PPTX con cada figura como SVG nativo directo, sin PNG/JPG de respaldo para la figura.
- ZIP con compendio de figuras JPG.
- ZIP con compendio de figuras PNG.
- ZIP con compendio de figuras SVG.

Al presionar **PDF**, el servidor garantiza primero que exista el PPTX de la corrida. Crea una copia temporal sólo para renderizar la base visual (fondos, títulos, narrativas y elementos de plantilla), eliminando de esa copia las figuras `ANUARIO_IMAGE_*` y las capas auxiliares `ANUARIO_TEXT_LAYER_*`. PowerPoint o LibreOffice convierten únicamente esa base. Después, el exportador toma **los SVG originales existentes en `build/figures`**, verifica que coincidan con los SVG usados al ensamblar el PPTX y los compone directamente sobre las páginas con CairoSVG + pypdf, en las mismas coordenadas del PPTX. No se crea ningún SVG alterno y las figuras no pasan por el motor Office.

La descarga sólo se publica cuando el número de páginas coincide con el de diapositivas, el tamaño de todas las páginas coincide con la presentación, ninguna página está vacía y todos los textos esperados de los SVG originales siguen siendo copiables. También incorpora metadatos, marcadores por sección y figura, huellas SHA-256 del PPTX/PDF y una huella conjunta de los SVG originales. Puede fijarse el motor usado **sólo para la base visual** con `ANUARIO_PDF_CONVERTER=powerpoint` o `ANUARIO_PDF_CONVERTER=libreoffice`.

Al ensamblar la presentación, cada figura disponible se incrusta como un SVG nativo directo, sin un raster de respaldo. El exportador de Matplotlib conserva las letras como elementos `<text>`, exige un lienzo transparente y rechaza SVG que incluyan imágenes rasterizadas. Para facilitar búsqueda/copia en visores de PowerPoint, el PPTX conserva su capa auxiliar nativa. Esa decisión **no afecta al PDF**: para la exportación PDF se eliminan temporalmente tanto la figura del PPTX como su helper y se vuelve a insertar exclusivamente el SVG original de `build/figures`, conservando su contenido vectorial y texto real.

Además, cada figura disponible puede tener una narrativa revisada en
`assets/presentation/narrativas_figuras_2026.json`. El ensamblador conserva el encabezado de la
figura y reemplaza únicamente el texto de relleno por el párrafo actualizado. Al terminar genera
reportes `*_narrativas.json` y `*_narrativas.csv` que registran, por figura, el texto 2024, el texto
insertado, el modo de actualización, la página fuente, el archivo de datos y el estado de
verificación de su huella. Si los datos cambian después de revisar una narrativa, el estado pasa a
`data_changed` y el modo estricto impide publicar un PPTX con texto potencialmente desactualizado.
la descarga. El reporte `*_ensamblaje.json` registra cuántos SVG y capas de texto se
incrustaron; el manifiesto `*_pdf.json` documenta la misma verificación en el PDF final.

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
- PDF con base de presentación + SVG originales directos, y PowerPoint editable: `entrega/`
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
