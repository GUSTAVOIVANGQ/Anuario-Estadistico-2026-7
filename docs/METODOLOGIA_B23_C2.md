# Metodología de B.23, B.24, B.25, C.1 y C.2

Cada figura tiene un único script que adquiere o reutiliza el dato crudo,
selecciona el corte más reciente, calcula los resultados, genera el texto,
registra la auditoría y escribe el PNG.

## Fuentes y cortes

- B.23: `TD_ACC_TVRES_ITE_VA.csv`, dentro de `CRT_BIT_TODO.zip`; diciembre de 2024.
- B.24: `TD_MARKET_SHARE_TVRES_ITE_VA.csv`, dentro del mismo ZIP; diciembre de 2024.
- B.25: `TD_IHH_TVRES_ITE_VA.csv`, dentro del mismo ZIP; diciembre de 2024.
- C.1: `TD_DIST_ESPECTRO_VA.csv`, descarga individual del CRT; agosto de 2024.
- C.2: `TD_ESPECTRO_BANDA_VA.csv` y la tabla anterior; agosto de 2024.

El ZIP general se reutiliza sin volver a descargarlo. Los CSV individuales de
espectro también quedan en caché después de la primera descarga y se prefieren
porque son posteriores a las copias incluidas en el ZIP general.

## Cálculos

- B.23 suma accesos por segmento y tecnología; cada participación es la suma
  de la tecnología entre el total del segmento por 100.
- B.24 normaliza los nombres de agentes, los agrupa como en el Anuario 2024 y
  suma la participación de mercado de cada grupo.
- B.25 conserva el IHH publicado por BIT para diciembre de cada año.
- C.1 suma los MHz asignados de las ocho bandas y representa su área de manera
  proporcional.
- C.2 convierte las fracciones publicadas a porcentaje y exige que los
  operadores de cada banda sumen aproximadamente 100%.

Los CSV de datos usados y de cálculos se producen exclusivamente durante la
corrida dentro de `reportes/<corrida>/`.
