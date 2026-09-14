# Metodología de las figuras D.5 a D.11

## Fuente y periodo

Las siete figuras usan la base abierta de la Encuesta de Confianza en el
Servicio de Internet (ECSI) 2024 del Instituto Federal de Telecomunicaciones.
La página oficial fue publicada el 16 de junio de 2025 y presenta ECSI 2024
como la edición vigente. La base contiene 4,275 entrevistas y los factores de
expansión `fac_per`, `fac_hog` y sus variantes normalizadas.

- Página oficial: <https://www.ift.org.mx/node/27269>
- Base CSV: <https://www.ift.org.mx/sites/default/files/contenidogeneral/publicaciones/baseconfianzadigital.csv>
- Fuente del repositorio: `ift_ecsi_2024_base`

La primera ejecución guarda el CSV por su huella SHA-256 en
`data/raw/ift_ecsi_2024_base/objects/`. Las siguientes figuras reutilizan esa
copia verificada y no vuelven a descargarla, salvo que se active
`ANUARIO_FORCE_DOWNLOAD=1`.

## Universo y ponderación

D.5, D.6, D.7, D.9, D.10 y D.11 restringen el universo a registros con
`rescate_internet = 1`. D.8 conserva la población completa, como lo hace la
tabla publicada. Todos los porcentajes se obtienen con:

`100 × suma(fac_per de la categoría) / suma(fac_per del universo)`

D.6 separa `sexo = 2` (hombres), `sexo = 1` (mujeres) y total. D.7, D.9 y
D.10 usan `edad_gpos` de 1 a 5: 18–24, 25–34, 35–44, 45–54 y 55 años o más.

## Variables

- D.5: `apren_uso_int_1` a `_6`, `_8` y `_9`.
- D.6 y D.7: `expp_mensnd`, `expp_pubipi`, `expp_datpre` y `expp_robcon`.
- D.8: `conf_int`, códigos 1 a 5 y 9.
- D.9: `seg_comp`, códigos 1 a 4 y 9.
- D.10: `seg_banca`, códigos 1 a 4 y 9.
- D.11: `seg_redes`, códigos 1 a 4 y 9.

En D.9 a D.11, las respuestas vacías se integran en NS/NR, tal como requiere
la reproducción de la publicación. Cada script compara sus cifras redondeadas
a un decimal con el anuario y detiene la ejecución si la diferencia supera
0.1 puntos porcentuales.

## Evidencia generada

Cada ejecución registra el CSV crudo y su huella, la tabla exacta usada, los
numeradores y denominadores ponderados, los resultados sin redondear, el texto
automático y el PNG. La consola imprime la tabla completa de cada figura.
