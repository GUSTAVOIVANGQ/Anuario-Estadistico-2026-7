# Actualización 0.27.0 - Interfaz web del Anuario Estadístico 2026

Esta actualización se aplica **encima del proyecto 0.26.0**. No reemplaza datos, figuras,
plantillas ni insumos existentes.

## Qué agrega

- Interfaz React inspirada en el flujo visual de Adobe Scan/editor de video.
- Panel lateral para:
  - ejecutar la figura actual;
  - ejecutar una selección;
  - iniciar una corrida completa de las 91 figuras disponibles A-G.
- Monitor central que cambia de figura conforme el pipeline termina cada imagen.
- Barra de progreso y miniaturas de la corrida.
- Eventos en tiempo real por Server-Sent Events (SSE).
- Modal final de descarga con:
  - PDF de la presentación completa;
  - PPTX editable;
  - ZIP de figuras JPG;
  - ZIP de figuras PNG;
  - ZIP de figuras SVG.

## Instalación

1. Copia el contenido de este paquete sobre la raíz del proyecto actual.
2. Instala/actualiza el entorno y compila React:

```powershell
.\preparar_entorno.ps1
```

3. Revisa que todo esté disponible:

```powershell
.\ejecutar.ps1 doctor
```

4. Inicia la interfaz:

```powershell
.\ejecutar.ps1 web
```

Se abrirá `http://127.0.0.1:8765`.

## Requisitos adicionales de la UI

- Node.js 20 o superior y npm para compilar `web/`.
- Para exportar PDF: Microsoft PowerPoint en Windows o LibreOffice.

## Nota sobre SVG

Si una figura ya cuenta con SVG nativo, se copia ese archivo. Si el generador actual sólo
produce PNG, el compendio crea un SVG compatible que incrusta el render PNG para mantener
exactamente la apariencia. Esto permite incorporar la opción SVG desde ahora sin modificar
los 91 scripts de figuras.

## Archivos principales

- `src/anuario2026/web.py`: API, ejecución, progreso y descargas.
- `src/anuario2026/exports.py`: PPTX, PDF y compendios.
- `src/anuario2026/pipeline.py`: eventos de progreso y selección arbitraria de figuras.
- `web/src/App.jsx`: interfaz React.
- `web/src/styles.css`: diseño y animaciones.
