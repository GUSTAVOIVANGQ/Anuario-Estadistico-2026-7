# Metodología de las figuras E.1 y E.9

## Figura E.1

E.1 usa dos bases oficiales del Instituto Federal de Telecomunicaciones:

- Tercera Encuesta 2023 a Personas Usuarias de Servicios de
  Telecomunicaciones, como control de reproducción del Anuario 2024.
- Segunda Encuesta 2025 a Personas Usuarias de Servicios de
  Telecomunicaciones, cuyos resultados proceden de entrevistas aplicadas
  durante 2024 y constituyen el último corte anual compatible localizado.

Para cada servicio se selecciona la pregunta directa de satisfacción general
en los últimos 12 meses y su variable recodificada de 0 a 100. El resultado es:

`IGS = suma(valor recodificado × factor final) / suma(factor final)`

En la base 2024 se utiliza el factor o calibrador **anual**, no el trimestral.
Internet fijo y televisión de paga usan el factor de expansión final; telefonía
fija y móvil usan el calibrador final correspondiente a las líneas del
servicio. Se eliminan únicamente valores sin IGS, factores vacíos y factores no
positivos.

La aplicación del mismo procedimiento reproduce exactamente, a una décima,
los cuatro valores del anuario para 2023 y los cuatro resultados oficiales del
corte 2024.

- Página 2025: <https://www.ift.org.mx/usuarios-y-audiencias/segunda-encuesta-2025-usuarios-de-servicios-de-telecomunicaciones>
- Base 2025: <https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/basesdedatossegundaencuesta2025.zip>
- Base histórica 2023: <https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/bd3erencuesta2023.zip>

## Figura E.9

E.9 requiere un universo diferente: micro, pequeñas y medianas empresas que
realizan actividades de importación y/o exportación. La Cuarta Encuesta MiPymes
2024 no contiene esa misma pregunta y no se mezcla con este estudio.

El último conjunto directamente comparable localizado es la base identificada
como 2022, difundida por el IFT junto con su reporte en 2023. El denominador es
la suma del `Factor de Expansión Final` de todas las respuestas no vacías a la
pregunta sobre el servicio más importante, incluido NS/NC. El numerador es la
suma del factor de cada servicio mostrado:

`porcentaje = 100 × suma(factor de la categoría) / suma(factor de respuestas válidas)`

NS/NC permanece en el denominador pero no se presenta como barra; por ello las
cinco categorías visibles suman 97.8% y no 100%. Los resultados reconstruidos
son 63.4%, 20.8%, 6.6%, 6.3% y 0.7%, sin usar cifras pegadas.

- Página oficial: <https://www.ift.org.mx/usuarios-y-audiencias/contratacion-percepcion-y-uso-del-internet-fijo-y-telefonia-fija-en-las-micro-pequenas-y-medianas>
- Base: <https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/bdmipymesimpexp2022.zip>

## Evidencia generada

Cada script descarga o reutiliza su fuente, verifica el ZIP, imprime los datos
usados, registra numeradores, denominadores, variables y factores, genera el
texto automático y produce el PNG final. Las siguientes corridas reutilizan la
copia verificada salvo que se active `ANUARIO_FORCE_DOWNLOAD=1`.
