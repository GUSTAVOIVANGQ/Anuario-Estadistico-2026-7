# Metodología de las figuras F.1.1 a F.1.4

## Separación de las láminas

El anuario 2024 repite o omite el identificador F.1 en las páginas 82 a 85.
Para que el pipeline sea determinista, cada página se registra como una figura
independiente:

- F.1.1: aplicaciones instaladas mediante Smartphone.
- F.1.2: actividades realizadas en Internet.
- F.1.3: habilidades en la computadora.
- F.1.4: uso de redes sociales.

## Fuentes y periodos

Los scripts descargan o reutilizan los ZIP CSV oficiales de ENDUTIH. ENDUTIH
2023 sirve para validar el modelo publicado. F.1.1, F.1.2 y F.1.4 aplican las
variables equivalentes a ENDUTIH 2025. F.1.3 usa ENDUTIH 2024 porque la edición
2025 cambió la pregunta 6.8 y ya no contiene `P6_8_7`, `P6_8_8`, `P6_8_9` ni
el resto de la batería comparable de habilidades.

## Universo y ponderación

Todos los cálculos restringen la población a personas de seis años o más y
usan `FAC_PER` como factor de expansión. Los resultados por sexo se calculan
con `SEXO=2` para mujeres y `SEXO=1` para hombres.

- F.1.1 lee `tr_endutih_usuarios2_anual`. El universo es `P8_11=1`; la
  instalación general usa `P8_14=1` y los tipos de aplicaciones usan
  `P8_16_1` a `P8_16_8` según su descripción oficial.
- F.1.2 lee `tr_endutih_usuarios_anual`. El universo es `P7_1=1`; las
  actividades se calculan con P7.13, P7.19, P7.21, P7.28, P7.33 y la unión de
  P7.35.1 a P7.35.5.
- F.1.3 usa `P6_1=1` y las habilidades `P6_8_1` a `P6_8_9` de ENDUTIH 2024.
- F.1.4 usa `P7_15=1` y las redes declaradas en `P7_16_1` a `P7_16_10`.

Cada porcentaje de actividad es:

`100 × suma(FAC_PER con indicador=1) / suma(FAC_PER del universo por sexo)`.

La participación del resumen es:

`100 × suma(FAC_PER del universo por sexo) / suma(FAC_PER de personas de 6+ por sexo)`.

## Control contra 2023

F.1.3 y F.1.4 reproducen exactamente las cifras publicadas. F.1.2 reproduce
el resumen y los indicadores, salvo la tarjeta de radio, cuya diferencia es de
un punto porcentual usando la variable que el diccionario identifica como
radio AM/FM. F.1.1 conserva las variables oficiales P8; la lámina publicada no
es totalmente consistente con esos microdatos, por lo que el reporte registra
la discrepancia en vez de seleccionar variables ajenas sólo para forzar la
coincidencia.
