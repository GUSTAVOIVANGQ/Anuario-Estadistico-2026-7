# Metodología de las figuras D.1 y E.2

## Figura D.1. Disponibilidad de las TIC en los hogares

### Fuentes y periodos

- Tabulados nacionales ENDUTIH 2023 `hnal110`, `hnal111` y `hnal130`, usados
  para reconstruir la serie histórica de 2010 a 2023.
- Microdatos de hogares ENDUTIH 2023, usados como control contra la figura del
  Anuario Estadístico 2024.
- Microdatos de hogares ENDUTIH 2024 y 2025, usados para actualizar la serie.

El periodo final es 2025, último año disponible en la fuente oficial al cierre
de esta versión. Los archivos se descargan una sola vez, se verifican y se
reutilizan desde la caché en las corridas siguientes.

### Universo y factor

El universo son los hogares nacionales contenidos en la tabla anual de
hogares. Todas las proporciones calculadas desde microdatos usan `FAC_HOG`:

`porcentaje = 100 × suma(FAC_HOG de hogares que cumplen) / suma(FAC_HOG válido)`

Las reglas son:

- Equipo de cómputo: en 2023 y 2024, al menos una de `P4_2_1_1`, `P4_2_2_1` o
  `P4_2_3_1` es igual a 1. En 2025 se usan las variables padre `P4_2_1`,
  `P4_2_2` o `P4_2_3`, debido al cambio de estructura del cuestionario.
- Aparatos de radio: `P4_1_1 = 1`.
- Televisor analógico: `P4_1_2 = 1`.
- Televisor digital: `P4_1_4 = 1`.
- Teléfono celular: `P4_1_6 = 1`.

### Reproducción y actualización

Antes de aceptar el corte actual, el script exige que ENDUTIH 2023 reproduzca,
al redondear al entero más cercano, los valores publicados de 44%, 43%, 19%,
82% y 95%. Los resultados calculados para 2025 son, respectivamente, 44.70%,
34.73%, 11.26%, 85.34% y 94.93%.

Para 2010 a 2023 se mantienen en la gráfica las etiquetas enteras publicadas,
lo que evita alterar retrospectivamente el redondeo editorial. Los porcentajes
sin redondear y su procedencia quedan en `datos_usados`. El tabulado vigente no
expone el desglose celular MODUTIH comparable de 2010 a 2014; para esos cinco
años se conservan los valores de la figura de referencia. Desde 2015 se usa el
tabulado nacional de telefonía por tipo.

## Figura E.2. Hallazgos sobre Inteligencia Artificial y ChatGPT

### Fuente y alcance

La fuente es el *Estudio Cualitativo Conocimiento y Percepción sobre la
Inteligencia Artificial (IA) y ChatGPT 2023* del Instituto Federal de
Telecomunicaciones. El script descarga o reutiliza el PDF oficial, comprueba su
firma de archivo y registra siete hallazgos organizados en dos temas:
Inteligencia Artificial y ChatGPT.

### Tratamiento

E.2 no calcula porcentajes. Los resultados provienen de grupos de enfoque y se
presentan exclusivamente como hallazgos cualitativos; no son estimaciones
poblacionales. La salida registra el texto, tema, orden, año del estudio y tipo
de resultado, además de imprimirlos en la terminal y generar la infografía.

## Evidencia generada

Ambas figuras producen una imagen PNG, la tabla exacta de datos o hallazgos
usados, referencias por fuente, cálculos o clasificaciones y el estado final de
la ejecución dentro de la carpeta de corrida en `reportes/`.
