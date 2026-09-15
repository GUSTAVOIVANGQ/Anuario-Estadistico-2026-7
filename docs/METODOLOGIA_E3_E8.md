# Metodología de las figuras E.3 a E.8

## Fuente y periodo

Las seis figuras usan las bases abiertas de la Cuarta Encuesta a micro,
pequeñas y medianas empresas del Instituto Federal de Telecomunicaciones
(IFT). El último conjunto localizado y compatible es la edición 2024,
publicada el 17 de enero de 2025; el levantamiento se realizó del 6 de julio al
18 de agosto de 2024.

- Página oficial 2024: <https://www.ift.org.mx/node/26777>
- Base 2024: <https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/basededatoscuartaencuesta2024mipymes.zip>
- Base 2023: <https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/bd4taencuesta2023.zip>
- Base 2022: <https://www.ift.org.mx/sites/default/files/contenidogeneral/usuarios-y-audiencias/bd4taencuesta2022.zip>

Los archivos se guardan por su huella SHA-256 bajo `data/raw/`. Si la copia
verificada ya existe, los scripts no vuelven a descargarla, salvo que se active
`ANUARIO_FORCE_DOWNLOAD=1`.

## Ponderación y universos

Todos los cálculos usan `Factor de expansión final`. General incluye todas las
empresas; Micro, Pequeña y Mediana se identifican con la clasificación de
tamaño incluida en cada edición.

- E.3: promedio ponderado del Índice General de Satisfacción recodificado para
  Internet fijo y telefonía fija. Se validan 2022, 2023 y 2024 y se muestran
  2023-2024. La escala es de 0 a 100 puntos.
- E.4: `100 × suma(factor con respuesta Sí) / suma(factor con respuesta
  válida)` para la pregunta principal de contratación de cada servicio. Se
  muestran 2023-2024.
- E.5: `suma(calificación × factor) / suma(factor)` para cada beneficio,
  servicio y tamaño. Se excluyen respuestas no numéricas y se muestra 2024 en
  escala de 0 a 10; 2023 funciona como control de reproducción.
- E.6: se restringe a empresas que declararon vender productos o servicios por
  Internet fijo. Cada porcentaje divide el factor de la categoría del
  beneficio principal entre el factor total de ese universo.
- E.7: porcentaje ponderado de empresas que respondieron Sí a cada dispositivo,
  sobre las empresas con respuesta válida. Se muestran 2023-2024.
- E.8: porcentaje ponderado de respuestas Sí a cada beneficio de contar con una
  aplicación móvil, sobre las respuestas válidas. Es respuesta múltiple y se
  muestra 2024.

## Controles editoriales

La celda general de Internet fijo 2023 de E.4 aparece como 84.4% en la lámina
del anuario anterior, pero la base oficial produce 89.4%. Ese 89.4% también
coincide con el texto narrativo y es coherente con los tres tamaños, que están
entre 89.3% y 99.5%. El proyecto conserva el valor calculado desde los datos
crudos y documenta la diferencia sin alterar la fórmula.

E.7 selecciona expresamente la pregunta principal de dispositivos. Esto evita
confundir la opción de servidores con otra pregunta posterior sobre el medio
usado para almacenar información, cuyos universos son distintos.

## Evidencia generada

Cada ejecución registra las fuentes y periodos, la tabla exacta usada, los
numeradores y denominadores ponderados, los resultados sin redondear, el texto
automático y el PNG. La consola imprime los valores usados en la figura.
