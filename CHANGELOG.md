# Historial de cambios

Todos los cambios importantes del proyecto se documentarán aquí.

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
