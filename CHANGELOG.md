# 0.30.0

- Corregida la exportación PDF para que **ninguna figura SVG sea convertida por PowerPoint o LibreOffice**.
- El PPTX de entrega permanece sin cambios: sigue usando los SVG nativos originales y su capa auxiliar de texto para visores de PowerPoint.
- Para el PDF se crea una copia temporal del PPTX sin `ANUARIO_IMAGE_*` ni `ANUARIO_TEXT_LAYER_*`; Office/LibreOffice renderiza únicamente la base visual.
- Cada figura se toma directamente de su archivo SVG original en `build/figures`, se convierte a un fragmento PDF vectorial con CairoSVG y se coloca con pypdf en las coordenadas exactas de la figura del PPTX. No se crea un SVG alterno ni un raster de respaldo.
- Se compara la huella SHA-256 del SVG original con el SVG incrustado en el PPTX para impedir que una figura modificada después del ensamblaje se mezcle silenciosamente con una corrida anterior.
- La validación final comprueba páginas, dimensiones y que todos los textos `<text>` esperados de los SVG originales sean copiables, incluyendo etiquetas cortas como `II` que PowerPoint podía perder en su conversión.
- Se añade `CairoSVG` como dependencia del proyecto y se eleva el esquema de auditoría PDF a versión 6.

# 0.29.0

- Se incorporan a la presentación los párrafos narrativos asociados a las 91 figuras disponibles de las secciones A a G, usando cuadros de texto nativos de PowerPoint para que el contenido sea editable, buscable y copiable.
- La redacción base se conserva del Anuario Estadístico 2024 y se actualizan de forma prioritaria únicamente periodos, cifras, porcentajes, cantidades y registros respaldados por los `datos_usados` de cada figura; cuando cambia el sentido de una comparación o ranking se permite sólo el ajuste gramatical mínimo necesario para no producir una afirmación falsa.
- Nuevo registro `assets/presentation/narrativas_figuras_2026.json` con texto base, texto actualizado, página fuente del PDF 2024, modo de actualización, notas, archivo de datos y huella SHA-256 por figura.
- Nuevo módulo `anuario2026.narratives` que valida que cada narrativa corresponda exactamente a los datos de la corrida actual y genera auditorías JSON/CSV.
- El ensamblador PPTX rechaza en modo estricto narrativas ausentes, errores de inserción o cambios de datos no revisados (`data_changed`) y comprueba tras reabrir el PPTX que el texto narrativo quedó realmente incrustado.
- La política SVG vectorial de 0.28.0 se mantiene sin cambios: las figuras siguen insertándose como SVG directo, con transparencia y texto vectorial/copiable.

# 0.28.0

- Las figuras usadas para PPTX y PDF son ahora SVG directos, sin PNG/JPG de respaldo en el objeto de figura.
- El exportador central de Matplotlib conserva el texto como elementos `<text>`, fuerza lienzo transparente y valida que el SVG sea completamente vectorial antes de aceptar la figura.
- Se desactivan simplificaciones de trazado y composiciones raster innecesarias; cualquier artista que obligue a incrustar un bitmap hace fallar la validación en vez de degradar silenciosamente la calidad.
- El PPTX mantiene una capa nativa auxiliar para que el texto de las figuras sea localizable/copiable en visores de PowerPoint, mientras el SVG sigue siendo el recurso visual primario.
- El PDF se genera desde una copia temporal del PPTX sin esa capa auxiliar y valida que todos los textos copiables provengan directamente de los `<text>` de los SVG, evitando texto duplicado.
- Los 91 SVG existentes de las secciones A a G fueron normalizados para eliminar únicamente el fondo blanco del lienzo raíz; los fondos internos intencionales del diseño se conservan.

# 0.27.0

- Añadida interfaz web React con visualizador central de figuras, panel lateral, selección por figura/sección y animaciones de estado.
- Nuevo comando `anuario-2026 web` / `.\ejecutar.ps1 web` para iniciar la app local.
- El pipeline emite eventos de progreso por figura sin alterar el comportamiento de la CLI existente.
- Añadidos endpoints para ejecutar una figura, una selección o todas las figuras disponibles y seguir la corrida mediante Server-Sent Events.
- Al terminar se muestra un panel de exportación estilo editor con PDF, PPTX y compendios JPG, PNG y SVG.
- Los compendios se construyen sólo con figuras `OK` de la corrida; SVG usa el archivo nativo cuando existe y un wrapper compatible cuando la figura sólo tiene PNG.
- El PDF se convierte siempre desde el PPTX ensamblado: prioriza PowerPoint en Windows y
  usa LibreOffice como alternativa multiplataforma. La exportación valida páginas y tamaño,
  añade metadatos y marcadores, y registra las huellas de ambos archivos.
- Las figuras del PPTX ahora conservan el SVG nativo con PNG de respaldo compatible; el
  paquete OOXML se valida después de incrustar cada recurso.
- PPTX y PDF incorporan una capa accesible con el texto de los SVG para buscar, seleccionar
  y copiar títulos, ejes, etiquetas, leyendas y fuentes sin alterar el diseño visual.
- El PDF verifica que todas las capas de texto esperadas sobrevivan a la conversión y deja
  constancia de SVG incrustados, páginas buscables y figuras pendientes en su manifiesto JSON.

# 0.26.0

- Normalizado el marcador verde de todos los títulos de figura con el patrón exacto de A.1 (`#4a7d75`, ancho 0.007 y alto 0.018 en coordenadas de figura).
- Cada corrida genera ahora `referencias_fuentes_figuras.csv` dentro de `reportes/<corrida>/`, conservando figura, source ID, propietario, ZIP/archivo real y portal de origen.
- Sustituidos los scripts E.4, F.14 y F.1.1 a F.1.4 por las versiones CRT/sinodales suministradas para esta revisión.
- Añadidas pruebas de regresión para el marcador de título y el nuevo reporte de referencias.

# 0.25.0

- Integrada la funcionalidad 1.2: ensamblaje sobre la plantilla PPTX completa del Anuario 2026.
- Incluida la plantilla automatizable de 119 diapositivas y el manifest de 105 marcadores.
- Nuevo comando `assemble` para insertar las figuras ya generadas sin volver a ejecutar el pipeline.
- `run --assemble` ahora usa los marcadores `ANUARIO_FIGURE_*` y conserva el diseño de la plantilla.
- Se genera un reporte JSON de figuras insertadas, faltantes y errores de mapeo.
- Añadida dependencia `python-pptx`; el ensamblaje ya no depende de Node.js.

# Historial de cambios

Todos los cambios importantes del proyecto se documentarán aquí.

## [0.23.0] - 2026-09-15

### Agregado

- E.1 como script autónomo con las encuestas de personas usuarias 2023 y 2025,
  selección explícita de factores anuales, cálculo ponderado, validación,
  impresión, auditoría, texto y PNG.
- E.9 como script autónomo con la base específica de MiPymes importadoras y
  exportadoras, cálculo con factor final, validación e imagen final.
- Documentación de los universos, periodos, variables y fórmulas de ambas
  figuras.

### Validado

- E.1 reproduce los cuatro IGS de 2023 y los resultados oficiales del corte
  2024 sin desviación a una décima.
- E.9 reproduce 63.4%, 20.8%, 6.6%, 6.3% y 0.7% desde los microdatos.
- La Segunda Encuesta 2025 es el último corte anual comparable localizado para
  E.1; la base específica 2022 continúa siendo la última comparable para E.9.

### Diseño

- Barras horizontales redondeadas, chips, tipografía, paleta y pies de figura
  reconstruidos a partir de las páginas 72 y 80 del Anuario 2024.

## [0.22.0] - 2026-09-15

### Agregado

- E.3 a E.8 como seis scripts autónomos con descarga o reutilización de las
  bases oficiales MiPymes 2022, 2023 y 2024 del IFT, cálculo ponderado,
  impresión, auditoría, texto y gráfica PNG.
- Registro de las tres fuentes en el inventario y metodología de variables,
  universos, fórmulas y controles contra la edición anterior.

### Validado

- Los resultados de E.3 a E.8 se reconstruyen desde los microdatos y reproducen
  las referencias publicadas con una diferencia máxima de 0.1 puntos por
  redondeo.
- La Cuarta Encuesta 2024, difundida el 17 de enero de 2025, es el último corte
  oficial localizado y compatible con estas figuras.
- E.4 usa 89.4% para Internet fijo en 2023: coincide con la base y el texto del
  anuario; el 84.4% de la celda publicada es una inconsistencia editorial.

### Diseño

- Tablas, barras agrupadas, pequeños múltiples y tarjetas con paleta,
  tipografía, jerarquía y pies de figura de la familia visual del anuario.

## [0.21.0] - 2026-09-14

### Agregado

- D.5 a D.11 como siete scripts autónomos con adquisición o reutilización de
  la base oficial ECSI 2024, cálculo ponderado, impresión, auditoría, texto y
  gráfica PNG.
- Registro de la ECSI 2024 en el inventario de fuentes y documentación de las
  variables, universos y fórmulas aplicadas.

### Validado

- Las cifras publicadas de D.5 a D.11 se reconstruyen directamente desde los
  4,275 registros de la base; la desviación máxima es de 0.1 puntos
  porcentuales por redondeo.
- ECSI 2024, publicada el 16 de junio de 2025, es el último corte oficial
  localizado y compatible con estas siete figuras.

### Diseño

- Barras simples, agrupadas y horizontales con paleta, chips numéricos,
  tipografía y pies de figura de la familia visual del anuario, sin elementos
  ilustrativos externos.

## [0.20.0] - 2026-09-14

### Agregado

- F.1.1 a F.1.4 como cuatro scripts autónomos con microdatos ENDUTIH, cálculo
  ponderado por sexo, impresión, auditoría, texto automático y PNG.
- ENDUTIH 2023 como control metodológico y ENDUTIH 2024 como último corte
  compatible para las habilidades informáticas de F.1.3.

### Corregido

- Separación explícita de las cuatro láminas que el anuario identifica de
  manera inconsistente como F.1.
- F.1.1 ahora lee la tabla oficial `usuarios2` y las variables P8 de
  aplicaciones; no intenta inferirlas desde las variables generales P7.
- F.1.3 comprueba que ENDUTIH 2025 eliminó parte de la batería de habilidades
  y evita mezclar conceptos no comparables.

### Diseño

- Tarjetas por sexo, cifras principales, jerarquía, paleta y pies reconstruidos
  a partir de las páginas 82 a 85, sin depender de ilustraciones externas.

## [0.19.0] - 2026-09-14

### Agregado

- F.3 a F.9 como siete scripts autónomos con adquisición o reutilización de
  microdatos MOCIBA, cálculo ponderado, impresión, auditoría, texto y PNG.
- MOCIBA 2024 como control metodológico y MOCIBA 2025 como fuente actual para
  todas las figuras, con validaciones de totales, exhaustividad y 41 contrastes
  contra cifras oficiales.

### Diseño

- Barras estatales, paneles por sexo y gráficas horizontales reconstruidas con
  la paleta, tarjetas, etiquetas y pies del Anuario 2024, sin las ilustraciones
  editoriales externas.

## [0.18.0] - 2026-09-14

### Agregado

- F.2 como script autónomo con adquisición o reutilización de ENOE, cruce de
  SDEM y COE1, cálculo ponderado por sexo, salida en terminal, auditoría y PNG.
- Prueba previa obligatoria que reproduce exactamente los seis resultados de la
  Figura F.2 publicada en 2024 antes de aplicar el modelo a 2026-T2.

### Diseño

- La gráfica conserva semicírculos, tarjetas, paleta, jerarquía tipográfica y
  pie de fuente del referente, destinando el espacio de ilustraciones externas
  a mostrar los totales desagregados calculados.

## [0.17.0] - 2026-09-14

### Agregado

- F.10 a F.16 como siete scripts autónomos con adquisición o reutilización de
  fuentes oficiales, cálculo o síntesis cualitativa, salida en terminal,
  auditoría y gráfica PNG.
- Validaciones de regresión frente a los resultados de referencia de 2023 y
  documentación de fórmulas, población elegible y factores de ponderación.

### Corregido

- La última fuente compatible es la Tercera Encuesta 2023: las encuestas 2025
  fueron revisadas, pero no contienen la batería comparable de violencia
  digital y no se mezclan con indicadores distintos.
- F.16 reconoce la opción publicada «Acudir con algún familiar/amigo/pareja» y
  agrega sin doble conteo las respuestas incluidas en «otras autoridades».

### Diseño

- Las siete figuras conservan la paleta, tarjetas, jerarquía tipográfica y pies
  editoriales del Anuario 2024, sin incorporar ilustraciones externas.

## [0.16.0] - 2026-09-14

### Agregado

- C.5 a C.16 como doce scripts autónomos con adquisición o reutilización de
  `CRT_BIT_TODO.zip`, cálculo, impresión de resultados, auditoría y PNG.
- Mapas estatales para C.7 y C.13 con geometría reutilizable, cinco intervalos,
  indicador nacional y superlativos calculados a partir de la tabla cruda.
- Documentación metodológica y pruebas de regresión para las tablas móviles.

### Actualizado

- Todas las figuras C.5-C.16 seleccionan diciembre de 2024, el corte más actual
  del archivo BIT disponible, sin estimar datos posteriores.
- El diseño adopta la estructura, paleta y pies del referente 2024, reservando
  el espacio de ilustraciones externas para la visualización estadística.

## [0.15.0] - 2026-09-11

### Agregado

- B.23, B.24 y B.25 como scripts autónomos que reutilizan `CRT_BIT_TODO.zip`,
  seleccionan diciembre de 2024 y generan auditoría, texto y PNG.
- C.1 y C.2 como scripts autónomos con descarga y caché de las tablas
  individuales de espectro del CRT, con último corte en agosto de 2024.
- Pruebas de regresión para periodos, agrupaciones, participaciones, IHH y el
  total de 645 MHz.

### Corregido

- C.1 y C.2 usan los CSV individuales vigentes en lugar de las copias antiguas
  incluidas en `TODO.zip`.
- Las cinco interfaces siguen el lenguaje visual del Anuario 2024 y conservan
  el formato editorial de `Fuente:` y `Nota:`.

## [0.14.0] - 2026-09-11

### Agregado

- B.22 integra en un único script la reutilización de TODO.zip, el descubrimiento
  de la edición DENUE más reciente, la descarga y caché de sus ZIP CSV oficiales,
  el conteo de establecimientos, los cálculos auditables y el mapa PNG.
- La gráfica reproduce los cinco intervalos, la burbuja nacional, la tasa anual
  y el pie de fuente del referente, sin incorporar la ilustración editorial del
  televisor.

### Cambiado

- B.22 deja de bloquear la corrida por insumo manual; todavía acepta ZIP o CSV
  colocados en `data/manual/B.22/` cuando se desea trabajar con una copia local.

## [0.13.3] - 2026-09-11

### Corregido

- B.9 adopta columnas apiladas estrechas con extremos redondeados, etiquetas
  blancas conectadas a cada segmento y leyenda horizontal como el referente.
- Maxcom se integra en `Otros` para presentar los siete grupos de la figura del
  anuario; la serie conserva el último diciembre disponible de 2024.

## [0.13.2] - 2026-09-11

### Corregido

- B.4 adopta el panel interior blanco, la escala recortada, la leyenda superior,
  las etiquetas de extremos y la banda redondeada de años del referente 2024.
- El área de la serie se amplió hasta 2024 sin reproducir teléfono, casa u otros
  dispositivos editoriales externos a la gráfica.

## [0.13.1] - 2026-09-11

### Corregido

- Se reorganizó la interfaz de B.1 siguiendo la composición del anuario y se
  integró el mapa verde de México como fondo tenue del gráfico principal.
- Se ampliaron y alinearon el pastel, el total nacional y los paneles de uno y
  dos servicios. Las columnas se sustituyeron por barras editoriales con remate
  curvo y chips de porcentaje, sin añadir casas, televisores, dispositivos o
  personas.

## [0.13.0] - 2026-09-10

### Cambiado

- B.4 a B.20 son ahora 17 scripts autónomos: cada archivo contiene la
  adquisición o reutilización de fuentes, cálculo, auditoría, texto y PNG.
- Se eliminó el motor de ejecución compartido de B.4 a B.20 y se adaptaron las
  pruebas para validar directamente uno de los scripts entregables.
- Se amplió el área útil de las series y mapas siguiendo el referente del
  anuario, sin reproducir casas, televisores, dispositivos o personas.
- Se eliminó por solicitud la carpeta `scripts/legacy/` y sus 289 archivos.

## [0.12.0] - 2026-09-10

### Añadido

- Figuras B.4 a B.20 con un script independiente por figura y una corrida
  completa de adquisición, cálculo, reporte, texto y PNG.
- Lectura selectiva de 14 tablas dentro del ZIP global BIT, sin extraer ni
  volver a descargar el archivo de 1.1 GB.
- Cálculos estatales de B.13 con hogares ENDUTIH 2025 y de B.14 con unidades
  económicas DENUE; ambos registran numeradores y denominadores.
- Pruebas de series, participaciones, IHH y distribución por velocidades.

### Corregido

- B.8 usa tráfico de telefonía fija y B.10 usa el IHH de telefonía fija; no se
  heredan las sustituciones por indicadores de Internet presentes en algunos
  códigos 2024.

## [0.11.0] - 2026-09-10

### Añadido

- B.21 con lectura directa de `TD_ACC_TVRES_ITE_VA.csv` dentro de `TODO.zip`,
  hogares ENDUTIH 2025, cálculo estatal y nacional, texto Jinja2 y mapa PNG.
- Geometría estatal reutilizable y una prueba del corte temporal, agregación de
  operadores, ponderación y rangos de color.

### Verificado

- El estimador aplicado a diciembre de 2023 y ENDUTIH 2023 reproduce el valor
  nacional 58 y los seis extremos estatales descritos en el anuario 2024.

## [0.10.0] - 2026-09-10

### Añadido

- C.3 y C.4 con reutilización del ZIP oficial ENDUTIH 2025, cálculo nacional,
  urbano y rural con `FAC_PER`, texto Jinja2, datos auditables y gráficas PNG.
- Regresión metodológica contra los microdatos ENDUTIH 2023 y los valores
  publicados 78%, 82% y 63% del anuario 2024.

### Corregido

- El indicador de C.3/C.4 se calcula con `P8_1=1` y `P8_4_2=1`, combinación
  que reproduce el referente; la propuesta basada en llamadas e Internet móvil
  no reproduce esos rótulos y usa un campo que cambió en ENDUTIH 2025.

## [0.9.0] - 2026-09-10

### Añadido

- B.1, B.2 y B.3 con descarga y caché compartida de ENDUTIH 2025, cálculo de
  combinaciones de servicios con `FAC_HOG`, texto Jinja2 y gráficas PNG.
- D.2, D.3 y D.4 con lectura directa de las tablas oficiales, cálculos
  ponderados con `FAC_PER`, datos usados y trazabilidad de fórmulas.
- Pruebas de las fórmulas de dominio, smartphone, horas de Internet y universo
  de dispositivos inteligentes.

### Corregido

- D.2 identifica smartphone mediante `P8_1=1` y `P8_4_2=1`; esta operación
  reproduce a una decimal los valores del anuario 2024 y sustituye las
  variables cruzadas del código heredado.

## [0.8.0] - 2026-09-09

### Añadido

- A.7 a A.10 como scripts independientes con adquisición y reutilización del
  ZIP integral ENIGH 2024, cálculo ponderado por decil, texto Jinja2, datos
  usados, cálculos auditables y gráficas PNG.
- Claves CCIF 2018 para servicios fijos y móviles de la ENIGH 2024.

### Corregido

- A.9 y A.10 dejan de usar una clave heredada ajena a telefonía móvil y
  calculan el gasto con recarga, plan celular y cuádruple play.

## [0.7.1] - 2026-09-09

### Corregido

- A.6 muestra los ingresos de los cuatro trimestres de 2024, último periodo de
  la tabla BIT descargada. Los presenta sin desglose y como `n.d.` porque la
  fuente no publica egresos ni margen para esos periodos.

## [0.7.0] - 2026-09-09

### Añadido

- A.6 con reutilización de `TODO.zip`, lectura selectiva de ingresos, cálculos
  de egresos y margen, texto Jinja2 y gráfica fiel al referente.
- Registro separado del último periodo disponible en la fuente y del último
  periodo completo que puede representarse sin estimar datos faltantes.

### Corregido

- A.5 detecta el último trimestre numérico común de sus dos libros; con los
  insumos actuales muestra 2025 completo y 2026 acumulado a marzo.

## [0.6.0] - 2026-09-09

### Añadido

- A.5 con lectura manual de los libros de IED, cálculo del corte comparable
  2013–2024, texto Jinja2, registros auditables y gráfica PNG.
- Identificación de los insumos manuales por su fuente configurada dentro de
  los reportes generados por la corrida.

### Cambiado

- `TODO.zip` se conserva en la caché compartida de BIT después de mover y
  verificar la copia proporcionada por el responsable del proyecto.
- A.5 no realiza descargas y señala los nombres y la ruta de los archivos
  requeridos cuando falta alguno.

## [0.5.0] - 2026-09-09

### Añadido

- A.4 con lectura selectiva de la tabla de inversión desde el ZIP global de
  BIT, cálculos auditables, texto Jinja2 y gráfica actualizada hasta 2024.
- Caché compartida para `TODO.zip`, reutilizable por las demás figuras BIT.

### Corregido

- La verificación de archivos grandes puede reutilizar su huella registrada
  cuando tamaño y fecha de modificación no cambiaron.

## [0.4.0] - 2026-09-09

### Añadido

- A.3 con descarga Playwright integrada en el propio script, caché verificada,
  lectura del conjunto mensual vigente del INPC, cálculos auditables y gráfica.
- Preparación opcional de Playwright y Chromium mediante
  `.\preparar_entorno.ps1 -ConPlaywright`.

### Corregido

- A.3 deja de solicitar un insumo manual y registra por separado las fuentes
  histórica y vigente.
- IPCOM conserva la serie comparable oficial sólo hasta julio de 2024, sin
  concatenarla con la clasificación posterior.

## [0.3.0] - 2026-09-09

### Añadido

- A.2 con adquisición de 27 cortes ENOE, reutilización de ZIP existentes,
  respaldo Playwright, verificación SDEM/COE1, cálculo ponderado y gráfica PNG.
- Cálculos auditables de distribución, variación anual y extremos de la serie
  para el empleo en telecomunicaciones y radiodifusión.

### Corregido

- Los chips porcentuales de A.1 ahora muestran el contorno del diseño original.
- La adquisición de fuentes usa primero la caché verificada y sólo descarga si
  el archivo falta; `ANUARIO_FORCE_DOWNLOAD=1` permite forzar la actualización.

## [0.2.0] - 2026-09-09

### Añadido

- A.1 con descarga oficial de INEGI, validación estructural, detección dinámica
  del último trimestre, cálculos auditables, texto Jinja2 y gráfica PNG con el
  diseño de referencia 2024.
- Tamaño, fecha de modificación de la fuente, tipo de contenido y estado de
  caché en el reporte de referencias.
- Copia de los códigos originales 2024 dentro del nuevo repositorio como
  referencia de migración, sin habilitarlos en el pipeline.

## [0.1.0] - 2026-09-09

### Añadido

- Estructura base independiente para el Anuario Estadístico 2026.
- Orquestador secuencial de 105 figuras, de A.1 a H.14.
- Contrato único para descarga, verificación, cálculo, texto y gráfica.
- Reportes por corrida de estado, referencias, cálculos y archivos.
- Manejo explícito de insumos manuales para A.3, A.5 y B.22.
- Punto de integración para el descargador Playwright de A.2.
- Motor de texto con plantillas Jinja2 y cálculos auxiliares.
- Ensamblador PowerPoint de 1600 × 900 basado en el referente 2024.
