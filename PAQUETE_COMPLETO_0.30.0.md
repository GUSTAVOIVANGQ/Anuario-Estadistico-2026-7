# Paquete completo 0.30.0

Esta revisión conserva el PPTX de 0.29.0 y cambia únicamente la ruta de exportación PDF de las figuras.

- PPTX: SVG nativo original + capa auxiliar de texto, sin cambios funcionales.
- PDF: base del PPTX sin figuras + superposición directa de los SVG originales de `build/figures`.
- No se genera un segundo SVG por figura.
- No se usa PNG/JPG como respaldo de las figuras en el PDF.
- CairoSVG convierte el SVG original directamente a contenido PDF vectorial y pypdf lo posiciona.
- El reporte `*_pdf.json` registra las huellas y confirma el modo `pptx_base_plus_original_svg_overlay`.
