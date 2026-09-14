# Metodología ENDUTIH: B.1-B.3, C.3-C.4 y D.2-D.4

## Fuente común

Las ocho figuras leen directamente el ZIP oficial de datos abiertos de la
ENDUTIH 2025 publicado por el INEGI. El archivo se conserva sin transformar en
`data/raw/inegi_endutih_2025/objects/<sha256>/` y se verifica como ZIP antes de
usarse. Las corridas posteriores reutilizan esa copia salvo que se establezca
`ANUARIO_FORCE_DOWNLOAD=1`.

## Reconstrucción del anuario 2024

Antes de usar 2025 se ejecutaron las fórmulas sobre los microdatos ENDUTIH 2023
del proyecto original. D.3 reproduce los ocho promedios publicados al ponderar
`P7_4` con `FAC_PER`. D.4 reproduce los diez porcentajes al usar como denominador
la suma de `FAC_PER` de quienes contestaron 1 en al menos una variable
`P9_1_1` a `P9_1_10`.

D.2 se reproduce a una decimal con dos indicadores: Internet es `P7_1=1` y
smartphone es la conjunción `P8_1=1` y `P8_4_2=1`. Para 2023 esta última fórmula
da 35.8%, 83.5%, 95.9%, 93.8%, 90.0%, 84.8% y 60.5%, exactamente los siete
valores publicados. El código heredado usaba variables de frecuencia de
computadora e Internet y, por ello, no representaba el título de la figura.

C.3 y C.4 se reconstruyeron con la misma conjunción de smartphone: `P8_1=1`
y `P8_4_2=1`, universo de personas de 6 años o más y ponderador `FAC_PER`.
Aplicada a ENDUTIH 2023 produce 77.8917% nacional, 82.1206% urbano y 63.0242%
rural; al redondear sin decimales reproduce exactamente 78%, 82% y 63% del
anuario 2024. La lógica alternativa del archivo de apoyo —unión de llamadas e
Internet móvil— arroja 86.5124%, 89.5580% y 75.8049%, respectivamente, por lo
que no concilia con el referente. Además, en 2025 la pregunta de conexión se
separó en `P7_5_1` y `P7_5_2`; ya no existe el campo único `P7_5`.

En B.1-B.3, Internet fijo se define como `P4_4=1` y `P4_5` igual a 1 o 3;
televisión restringida como `P5_1=1`; y telefonía fija como `P5_5=1`. Las ocho
combinaciones son mutuamente excluyentes y se ponderan con `FAC_HOG`. Los
microdatos 2023 no reproducen todos los rótulos editoriales del PDF de 2024; el
propio análisis heredado ya registraba esas diferencias. Por esta razón, las
nuevas figuras muestran el resultado calculado y auditable de los microdatos,
sin forzar cifras para imitar rótulos no conciliables.

## Estimadores aplicados a 2025

- B.1: universo nacional de hogares.
- B.2: hogares con `DOMINIO=R`.
- B.3: hogares con `DOMINIO=U`.
- C.3: `sum(FAC_PER si P8_1=1 y P8_4_2=1) / sum(FAC_PER)` en población de
  6 años o más a nivel nacional.
- C.4: el mismo estimador de C.3, separado por `DOMINIO=U` y `DOMINIO=R`.
- D.2: suma ponderada del indicador entre la población ponderada del grupo.
- D.3: `sum(P7_4 * FAC_PER) / sum(FAC_PER)` entre respuestas válidas.
- D.4: `sum(FAC_PER del dispositivo) / sum(FAC_PER de cualquier dispositivo)`.

Los valores sin redondear se guardan en `datos_usados`; la gráfica aplica sólo
el redondeo visual del referente.
