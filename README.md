# Anuario Estadístico 2026

Proyecto reproducible para actualizar, calcular, documentar y ensamblar las 105
figuras del Anuario Estadístico 2026. El anuario 2024 es el referente visual y
metodológico. Los códigos originales permanecen intactos en la carpeta padre.

Esta versión entrega la base operativa y las figuras A.1, A.2, A.3, A.4 y A.5 actualizadas. Los demás
scripts se incorporarán uno por uno cuando el responsable del proyecto lo
autorice. Una copia de consulta de los códigos 2024 vive en
`scripts/legacy/original_2024/`; el pipeline sólo ejecuta los scripts migrados a
`scripts/figures/`.

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
- B.22: `data/manual/B.22/`
- A.2: adquisición automática de microdatos ENOE; reutiliza ZIP verificados,
  intenta los enlaces oficiales directos y usa Playwright sólo como respaldo.

El programa muestra estas rutas al iniciar. No descarga ni modifica estos
archivos manuales.

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
517 Telecomunicaciones, conserva el corte comparable 2013–2024 definido por la
lógica validada (2024 acumulado a junio), imprime los datos usados y genera el
PNG.

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

## Licencia

El código nuevo usa licencia MIT. Los datos, logotipos, ilustraciones y
publicaciones de referencia conservan los términos de sus titulares.
