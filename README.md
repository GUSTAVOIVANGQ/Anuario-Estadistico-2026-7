# Anuario Estadístico 2026

Proyecto reproducible para actualizar, calcular, documentar y ensamblar las 105
figuras del Anuario Estadístico 2026. El anuario 2024 es el referente visual y
metodológico. Los códigos originales permanecen intactos en la carpeta padre.

Esta versión entrega la base operativa, las figuras A.1 a A.10, B.1 a B.25,
C.1 a C.16, D.2 a D.11 y F.1.1 a F.16 actualizadas. Los demás scripts se incorporarán uno por
uno cuando el responsable del proyecto lo autorice. El pipeline sólo ejecuta
los scripts de `scripts/figures/`; la carpeta `scripts/legacy/` fue eliminada.

## Inicio rápido

```powershell
.\preparar_entorno.ps1
.\ejecutar.ps1 doctor
.\ejecutar.ps1 run --dry-run
```

Si `python` apunta a una distribución reducida sin `venv`, indica una
instalación completa: `./preparar_entorno.ps1 -PythonEjecutable C:\ruta\python.exe`.

La simulación crea desde el inicio una carpeta en `reportes/` con el inventario
de fuentes, pendientes, estados y archivos CSV preparados para cálculos y
referencias.

## Ejecución normal

```powershell
# Todas las figuras, en orden A.1, A.2, ... H.14
.\ejecutar.ps1 run

# Una figura
.\ejecutar.ps1 run --only A.1

# Un tramo
.\ejecutar.ps1 run --from A.1 --until A.10

# Ensamblar el PPTX al terminar
.\ejecutar.ps1 run --assemble
```

La corrida continúa cuando encuentra una figura aún pendiente y registra su
estado. Use `--stop-on-error` durante una investigación puntual.

## Insumos especiales

- A.5: `data/manual/A.5/`
- A.2: adquisición automática de microdatos ENOE; reutiliza ZIP verificados,
  intenta los enlaces oficiales directos y usa Playwright sólo como respaldo.

El programa muestra esta ruta al iniciar. No descarga ni modifica los archivos
manuales de A.5. B.22 descubre y descarga automáticamente los 25 ZIP CSV por
actividad económica de la edición DENUE más reciente.

A.3 integra la descarga del portal dinámico del INEGI dentro de su propio
script. La primera ejecución sin caché requiere preparar Chromium con
`.\preparar_entorno.ps1 -ConPlaywright`; las siguientes reutilizan el CSV
verificado. `ANUARIO_PLAYWRIGHT_HEADED=1` permite mostrar el navegador si el
portal requiere supervisión.

## Figura A.1

```powershell
.\ejecutar.ps1 run --only A.1
```

El script obtiene el tabulado oficial `PIBT_2.xlsx`, verifica
que sea un libro Office válido, localiza por nombre el bloque a precios de 2018,
calcula la contribución conjunta de telecomunicaciones y radiodifusión, imprime
los datos usados y produce el PNG. Si el archivo ya está en la caché y pasa la
verificación, no se vuelve a descargar. `ANUARIO_FORCE_DOWNLOAD=1` fuerza una
actualización y `ANUARIO_OFFLINE=1` exige trabajar sólo con archivos existentes.

## Figura A.2

```powershell
.\ejecutar.ps1 run --only A.2
```

El script reúne los 27 cortes ENOE necesarios entre 2013-II y 2026-II. Importa
las copias históricas existentes sin volver a bajarlas y descarga únicamente
los ZIP faltantes. Después verifica SDEM/COE1, cruza cada persona con las llaves
completas, aplica el factor trimestral, calcula los sectores SCIAN 517 y 515,
imprime la tabla usada y genera la gráfica PNG.

## Figura A.3

```powershell
.\ejecutar.ps1 run --only A.3
```

El script reutiliza primero los descargables verificados. Si falta el CSV
histórico, automatiza la exportación con Playwright; además obtiene el conjunto
mensual vigente del INPC, calcula la variación anual, imprime la tabla usada y
genera el PNG. La serie comparable `08 Comunicaciones` del portal anterior sólo
está publicada hasta julio de 2024, por lo que IPCOM termina en ese punto sin
unirla artificialmente con la clasificación nueva.

## Figura A.4

```powershell
.\ejecutar.ps1 run --only A.4
```

El script adquiere `TODO.zip`, el archivo global oficial de BIT, y lo conserva
como caché compartida. Si ya existe una copia verificada no vuelve a
descargarla. A.4 abre directamente dentro del ZIP únicamente
`TD_INVERSION_TELECOM_ITE_VA.csv`, calcula los totales y participaciones de
2013 a 2024, imprime los datos usados y genera la gráfica PNG. Las siguientes
figuras basadas en BIT deben solicitar esta misma fuente para reutilizarla.

## Figura A.5

```powershell
.\ejecutar.ps1 run --only A.5
```

A.5 usa exclusivamente los dos libros colocados en `data/manual/A.5/`; no los
descarga ni los reemplaza. Si falta alguno, la corrida indica el nombre y esa
ruta. El script verifica los archivos, lee la IED total actualizada y el renglón
517 Telecomunicaciones, detecta el último trimestre numérico común de ambas
fuentes, imprime los datos usados y genera el PNG. Con los libros actuales, la
serie llega a 2026-T1 y utiliza 2025 completo.

## Figura A.6

```powershell
.\ejecutar.ps1 run --only A.6
```

A.6 reutiliza el mismo `TODO.zip` y abre únicamente
`TD_INGRESOS_TELECOM_ITE_VA.csv`. La gráfica llega al último dato de la tabla,
2024-T4. BIT no incluye el desglose de egresos y margen para 2024, por lo que
esos cuatro trimestres muestran el ingreso total con contorno y el indicador
`n.d.`; el desglose histórico termina en 2023-T4 sin estimar valores.

## Figuras A.7 a A.10

```powershell
.\ejecutar.ps1 run --from A.7 --until A.10
```

Cada script adquiere por sí mismo la fuente `inegi_enigh_2024`. La primera
figura descarga y verifica el ZIP integral de microdatos; las siguientes lo
reutilizan desde la caché. A.7 y A.8 procesan servicios fijos. A.9 y A.10 usan
las claves CCIF 2018 de recarga, plan celular y cuádruple play. Los cuatro
scripts forman deciles con el factor de expansión, imprimen su tabla de datos,
registran los cálculos y generan su propio PNG con periodo 2024.

## Figuras B.1 a B.3, C.3, C.4 y D.2 a D.4

```powershell
.\ejecutar.ps1 run --from B.1 --until B.3
.\ejecutar.ps1 run --from C.3 --until C.4
.\ejecutar.ps1 run --from D.2 --until D.4
```

Las ocho figuras comparten el ZIP oficial de datos abiertos ENDUTIH 2025. La
primera ejecución lo descarga y verifica; las siguientes reutilizan la misma
copia sin descargarla nuevamente. B.1 a B.3 calculan las ocho combinaciones de
Internet fijo, televisión restringida y telefonía fija con `FAC_HOG`. C.3 y
C.4 identifican a las personas de 6 años o más con celular tipo smartphone y
calculan los porcentajes nacional, urbano y rural con `FAC_PER`. D.2 cruza
las tablas de usuarios para identificar smartphone e Internet; D.3 calcula
horas promedio ponderadas; D.4 calcula cada dispositivo respecto de las
personas que usaron al menos uno. Cada script imprime y registra sus resultados.

## Figuras D.5 a D.11

```powershell
.\ejecutar.ps1 run --from D.5 --until D.11
```

Cada figura dispone de un script autónomo con descarga o reutilización de la
base abierta de la Encuesta de Confianza en el Servicio de Internet (ECSI)
2024, validación del CSV, cálculo ponderado con `fac_per`, contraste contra el
resultado publicado, impresión, auditoría, texto y PNG. La base se descarga
una sola vez y las siguientes figuras usan la copia verificada.

ECSI 2024 es la edición más reciente publicada por el IFT y fue difundida el
16 de junio de 2025. D.5 calcula formas de aprendizaje; D.6 y D.7 experiencias
negativas por sexo y edad; D.8 influencia de la confianza; D.9, D.10 y D.11
niveles de seguridad en compras, banca y redes sociales. Las diferencias
máximas frente a las cifras del anuario son de 0.1 puntos porcentuales y se
explican por redondeo.

## Figuras B.4 a B.20

```powershell
.\ejecutar.ps1 run --from B.4 --until B.20
```

Cada figura cuenta con un único script ejecutable y autónomo: el archivo de la
figura contiene adquisición o reutilización de fuentes, lectura, cálculo,
auditoría, texto y PNG, sin depender de un motor compartido entre B.4 y B.20.
Los 17 scripts reutilizan el mismo `CRT_BIT_TODO.zip`, abren únicamente las
tablas que necesitan y seleccionan el último diciembre completo. Con la
descarga actual, todas las tablas BIT llegan a diciembre de 2024.

El diseño conserva la familia visual del anuario (tipografías, paleta, tipos de
gráfica, etiquetas, notas y fuentes). Las ilustraciones externas —casas,
televisores, teléfonos, computadoras o personas— no forman parte del PNG; su
espacio se asigna al área útil de las series, mapas y comparaciones.

B.13 divide los accesos residenciales de BIT entre los hogares expandidos de
ENDUTIH 2025. B.14 divide los accesos no residenciales entre las unidades
económicas del desglose estatal DENUE disponible en el repositorio, cuya
edición es noviembre de 2023. El periodo de cada numerador y denominador queda
registrado en el reporte de la corrida.

## Figuras C.5 a C.16

```powershell
.\ejecutar.ps1 run --from C.5 --until C.16
```

Cada figura cuenta con su propio script y reutiliza la copia verificada de
`CRT_BIT_TODO.zip`; si ya existe no vuelve a descargarla. Los scripts abren
solamente las tablas móviles necesarias, seleccionan el último dato publicado,
imprimen los resultados, registran cada cálculo y generan un PNG. Con el
archivo actual, las doce figuras utilizan diciembre de 2024.

## Figuras F.1.1 a F.1.4

```powershell
.\ejecutar.ps1 run --from F.1.1 --until F.1.4
```

Las cuatro láminas que el anuario rotula de manera inconsistente como F.1 se
registran como F.1.1, F.1.2, F.1.3 y F.1.4. Cada una tiene un solo script con
adquisición o reutilización de ENDUTIH, selección de tabla, cálculo ponderado
con `FAC_PER`, impresión, auditoría, texto y PNG.

F.1.1, F.1.2 y F.1.4 usan ENDUTIH 2025. F.1.3 usa ENDUTIH 2024 porque es el
último corte que conserva las nueve variables de habilidades informáticas; el
script también inspecciona 2025 y registra las variables que desaparecieron.
ENDUTIH 2023 se usa para contrastar el modelo contra las cifras del anuario.
La metodología detallada está en `docs/METODOLOGIA_F1.md`.

## Figura F.2

```powershell
.\ejecutar.ps1 run --only F.2
```

F.2 reutiliza los ZIP oficiales ENOE 2024-T2 y 2026-T2 si ya están verificados.
Antes de calcular el corte actual, cruza SDEM y COE1 con la llave completa y
exige reproducir exactamente los totales y porcentajes de la figura publicada
en 2024. Después aplica el mismo universo, códigos SCIAN y factor trimestral al
segundo trimestre de 2026, imprime la tabla usada y genera el PNG. La metodología
detallada está en `docs/METODOLOGIA_F2.md`.

## Figuras F.3 a F.9

```powershell
.\ejecutar.ps1 run --from F.3 --until F.9
```

Cada figura tiene un único script con adquisición, cálculo, impresión en
terminal, auditoría, texto y PNG. Los siete scripts reutilizan la misma copia
verificada de los microdatos MOCIBA. Procesan primero la edición 2024 para
validar el modelo y después aplican las mismas variables y el factor de
expansión a MOCIBA 2025, la edición anual más reciente publicada.

F.3 y F.4 calculan la distribución de las víctimas entre las 32 entidades; F.5
la distribución por edad y sexo; F.6 las situaciones experimentadas; F.7 las
medidas de seguridad; F.8 los medios digitales y F.9 las medidas tomadas. La
metodología completa está en `docs/METODOLOGIA_F3_F9.md`.

## Figuras F.10 a F.16

```powershell
.\ejecutar.ps1 run --from F.10 --until F.16
```

Las figuras revisan las bases de las encuestas a personas usuarias en orden de
actualidad. Las publicaciones 2025 no contienen la batería comparable de
violencia digital; por ello se utiliza la Tercera Encuesta 2023, que es la
última fuente compatible. Cada script reutiliza el ZIP o PDF ya verificado,
calcula porcentajes ponderados desde microdatos, imprime los resultados y
genera su PNG. F.14 conserva el carácter cualitativo de la fuente.

C.7 y C.13 también reutilizan la geometría estatal. Las tablas estatales sólo
publican el corte de 2024 en esta descarga, mientras que C.6, C.7 y C.13 toman
sus indicadores nacionales de las series nacionales correspondientes. No se
construyen observaciones históricas ficticias.

## Figura B.21

```powershell
.\ejecutar.ps1 run --only B.21
```

B.21 reutiliza `CRT_BIT_TODO.zip` y el ZIP ENDUTIH 2025. Abre únicamente la
tabla de accesos residenciales de televisión restringida, detecta el último
corte disponible, suma los operadores por entidad y divide entre los hogares
expandidos con `FAC_HOG`. Con los archivos actuales utiliza diciembre de 2024
y ENDUTIH 2025. Imprime las 32 observaciones, registra numeradores,
denominadores y resultados, y genera el mapa con los rangos del referente.

## Figura B.22

```powershell
.\ejecutar.ps1 run --only B.22
```

B.22 reutiliza `CRT_BIT_TODO.zip`, consulta el catálogo oficial de descarga
masiva de INEGI y conserva en caché los 25 ZIP CSV por actividad de la edición
DENUE más reciente. Cuenta directamente cada establecimiento por entidad,
detecta el último corte BIT y calcula el indicador estatal y nacional, además
de la variación anual de los accesos. Con las fuentes actuales usa BIT
diciembre de 2024 y DENUE mayo de 2026. La gráfica, los datos usados y los
reportes se generan sin cifras pegadas manualmente.

## Salidas por figura

- Gráfica: `build/figures/<sección>/`
- Página completa opcional: `build/slides/`
- Texto: registrado dentro de la carpeta de corrida
- Tabla usada: `reportes/<corrida>/datos_usados/`
- Referencias y cálculos: CSV dentro de `reportes/<corrida>/`

El ensamblador PowerPoint usa lienzo de 1600 × 900, igual que el PDF de 2024.
Prefiere una página completa si el script la produce; en caso contrario inserta
la gráfica sin añadir rótulos editoriales.

El ensamblador usa `@oai/artifact-tool`. En Codex se resuelve con el runtime
incluido. En otra máquina, `ANUARIO_NODE_MODULES` debe apuntar a una carpeta
`node_modules` que contenga ese paquete; `ANUARIO_NODE` puede indicar la ruta de
Node.js. En Codex, `ANUARIO_RUNTIME_PYTHON` y `ANUARIO_RUNTIME_BIN_DIR` permiten
activar la validación avanzada con el runtime incluido.

## Reglas de diseño

Cada figura parte de su código original. Se conservan colores, tipografía,
proporciones, leyendas y formatos numéricos. Sólo se actualizan datos, periodos y
el contenido mínimo de `Fuente:`, `Nota:` o `Notas:`. Esas etiquetas permanecen
en negritas y el texto posterior en peso normal. No se agregan etiquetas como
`revisión` o `control editorial`.

## Documentación

- [Arquitectura](docs/ARQUITECTURA.md)
- [Contrato de cada figura](docs/CONTRATO_FIGURA.md)
- [Evidencia para defensa](docs/DEFENSA_SINODALES.md)
- [Insumos manuales](docs/INSUMOS_MANUALES.md)
- [Metodología ENDUTIH para B.1-B.3, C.3-C.4 y D.2-D.4](docs/METODOLOGIA_ENDUTIH.md)
- [Metodología ECSI para D.5-D.11](docs/METODOLOGIA_D5_D11.md)
- [Metodología de B.21](docs/METODOLOGIA_B21.md)
- [Metodología de B.22](docs/METODOLOGIA_B22.md)
- [Metodología de B.23 a C.2](docs/METODOLOGIA_B23_C2.md)
- [Metodología de B.4 a B.20](docs/METODOLOGIA_B4_B20.md)
- [Metodología de C.5 a C.16](docs/METODOLOGIA_C5_C16.md)
- [Metodología de F.10 a F.16](docs/METODOLOGIA_F10_F16.md)

## Licencia

El código nuevo usa licencia MIT. Los datos, logotipos, ilustraciones y
publicaciones de referencia conservan los términos de sus titulares.
