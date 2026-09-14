# Metodología de las figuras F.3 a F.9

## Fuente y actualidad

Las siete figuras usan los microdatos CSV del Módulo sobre Ciberacoso
(MOCIBA) del INEGI. MOCIBA 2025 es la edición anual más reciente publicada al
preparar esta versión. MOCIBA 2024 se procesa primero como control metodológico;
la página del Anuario 2024, basada en MOCIBA 2023, se conserva como referente
visual y editorial.

Los dos ZIP se almacenan en la caché verificada del proyecto. Cada script
solicita las fuentes por sí mismo: si ya existen no las descarga de nuevo.

## Universo común

La población objetivo son personas de 12 años y más que usaron Internet en los
tres meses anteriores. Una persona se clasifica como víctima si respondió sí a
al menos una de las trece situaciones `P4_01` a `P4_13`. Todos los resultados
usan el factor de expansión `FACTOR`.

## Operaciones

- F.3 divide las víctimas expandidas de cada entidad entre las víctimas
  expandidas del país.
- F.4 repite esa distribución dentro de hombres y mujeres por separado.
- F.5 distribuye las víctimas de cada sexo en seis grupos de edad exhaustivos.
- F.6 calcula, dentro de las víctimas de cada sexo, el porcentaje que reportó
  cada situación `P4`.
- F.7 calcula las medidas de seguridad `P2` dentro de la población elegible de
  cada sexo (`P1 = 1`).
- F.8 detecta los medios digitales declarados en `P11`; es una pregunta de
  respuesta múltiple.
- F.9 calcula las medidas `P12` dentro de las víctimas; las opciones de denuncia
  ante el Ministerio Público y ante el proveedor se presentan juntas, como en
  el referente.

## Validación

F.3 a F.5 comprueban totales, cobertura de 32 entidades y sumas exhaustivas.
F.6 a F.9 contrastan los microdatos 2024 contra 41 cifras oficiales incluidas
en la lógica entregada, con tolerancia máxima de 0.25 puntos porcentuales. Una
falla detiene la generación para impedir aplicar a 2025 un modelo no comparable.
