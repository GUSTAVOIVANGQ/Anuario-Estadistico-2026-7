# Scripts de figuras

Cada figura vive en un archivo independiente y expone una función
`generate(context)`. El orquestador descubre el script esperado por su nombre y
lo ejecuta en el orden del anuario 2024.

Ejemplos de nombres:

- `figura_a_1.py`
- `figura_b_22.py`
- `figura_f_1_1.py`

Usa `_plantilla.py` como punto de partida. No modifiques el diseño por medio del
orquestador: la figura debe conservar directamente sus colores, tamaños,
tipografía, títulos y pies. En el pie, `Fuente:`, `Nota:` o `Notas:` van en
negritas; el texto posterior usa peso normal. No agregues leyendas editoriales.

Los scripts continúan guardando su ruta canónica `.png` con `fig.savefig`. El
pipeline captura esa misma figura antes de cerrarla y crea también `.jpg` y
`.svg`. En el SVG el texto se conserva como texto (`svg.fonttype=none`), por lo
que no se deben convertir manualmente las etiquetas a trazados ni sustituir la
figura completa por una imagen raster.
