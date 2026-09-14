Actualización E.3-E.8 — Anuario Estadístico 2026
================================================

Versión sin generación de gráficas
----------------------------------
Los scripts figura_e3.py a figura_e8.py conservan los cálculos y validaciones,
pero se eliminó todo el código de matplotlib y la creación de archivos PNG.
La salida final de cada script es una tabla impresa en consola con los valores
que antes se utilizaban para construir la gráfica correspondiente.

Fuente cruda oficial
--------------------
Cuarta Encuesta a MiPymes del IFT:
2022: https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/bd4taencuesta2022.zip
2023: https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/bd4taencuesta2023.zip
2024: https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/basededatoscuartaencuesta2024mipymes.zip

Los scripts descargan los ZIP si no existen en data/raw/ift_mipymes/. Si la descarga HTTP falla,
usan Playwright como fallback y localizan el enlace de "Base de Datos" en la página oficial del IFT.

Validaciones incluidas
----------------------
E.3: reconstruye 2022 y 2023 y valida la actualización 2024 contra el reporte oficial.
E.4: valida 2023 y 2024. En 2024 la categoría separada "Datos móviles" ya no se publica en el
     gráfico comparable; la salida usa las cuatro categorías comunes.
E.5: valida toda la tabla 2023 del Anuario 2024 y aplica el mismo promedio ponderado a 2024.
E.6: valida los porcentajes 2024 contra el gráfico 2.2 oficial.
E.7: valida 2023 y 2024 contra los gráficos publicados.
E.8: valida 2023 y 2024 contra los gráficos publicados.

Salida
------
Solo consola: los valores numéricos que alimentaban cada figura.
No se generan PNG ni CSV de auditoría desde figura_e3.py a figura_e8.py.

Ejecución desde PowerShell
--------------------------
3..8 | ForEach-Object {
    python "C:\Users\gustavo.garcia\Documents\GitHub\Anuario-estadistico-2026\legacy\scripts\E\figura_e$_.py"
}

Dependencias
------------
pip install pandas openpyxl requests

Solo si se requiere el fallback de descarga:
pip install playwright
playwright install chromium
