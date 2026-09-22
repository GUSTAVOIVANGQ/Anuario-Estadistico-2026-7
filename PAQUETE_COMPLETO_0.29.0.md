# Paquete completo 0.29.0

Este paquete contiene el proyecto actualizado con:

- generación de figuras SVG vectoriales y transparentes;
- ensamblaje PPTX usando SVG directo;
- texto copiable/editable;
- narrativas de las figuras A-G insertadas como texto nativo de PowerPoint;
- registro y validación de narrativas por huella de datos;
- PDF 2024 de referencia usado para las narrativas;
- presentación final y reportes de auditoría en `entrega/final_0.29.0/`;
- código fuente, pruebas, configuración, datos, plantillas y documentación.

Para mantener el paquete portable no se incluyen dependencias reconstruibles (`web/node_modules`), cachés de Python/Pytest ni archivos binarios de fuentes. Las dependencias se reinstalan con `requirements.txt`/`pyproject.toml` y `web/package-lock.json`.
