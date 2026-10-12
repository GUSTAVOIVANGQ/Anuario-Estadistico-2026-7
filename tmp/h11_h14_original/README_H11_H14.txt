FIGURAS H.11-H.14 – INRAM RADIO

Archivos principales
--------------------
datos_inram_h11_h14_2024.ods
    ODS consolidado. Cada hoja de datos conserva la estructura del example.ods:
    TIPO DE ESTUDIO, MEDIO, PLAZA, ESTUDIO, GRUPO, EMISORA, SIGLAS, BANDA,
    06:00 ... 23:00.

    Hojas:
    CDMX_TOTAL, CDMX_HOMBRES, CDMX_MUJERES
    GDL_TOTAL, GDL_HOMBRES, GDL_MUJERES
    MTY_TOTAL, MTY_HOMBRES, MTY_MUJERES
    UNIVERSOS

inram_radio_core.py
    Lee directamente el ODS, suma los ratings horarios crudos por estudio,
    pondera los meses por el universo/población y combina las plazas en H.11.
    Para julio 2023-junio 2024 valida automáticamente contra el Anuario 2024.

figura_h11.py ... figura_h14.py
    Generadores de las cuatro gráficas. El estilo visual está basado en la
    plantilla figura_h1.py proporcionada; la lógica inventada de la plantilla
    no se reutiliza.

Dependencias
------------
Python 3
numpy
matplotlib
scipy

Uso
---
Coloque los .py y el ODS en la misma carpeta y ejecute, por ejemplo:

    python figura_h11.py
    python figura_h12.py
    python figura_h13.py
    python figura_h14.py

Por defecto las imágenes se guardan en ./output/.
También se puede indicar otro ODS y otra salida:

    python figura_h12.py --datos datos_inram_h11_h14_2024.ods --salida figura_h12.png

Método validado
---------------
1. Para cada plaza, target, mes y hora se suman todas las filas que exporta
   INRAM en "Tendencia por Horas". No se filtra la columna BANDA.
2. Para cada hora se combinan los meses ponderando por el universo/población
   de cada estudio.
3. H.11 combina además CDMX, Guadalajara y Monterrey ponderando por sus
   respectivos universos.
4. El promedio reportado es la media de las 18 horas (06:00-23:00).
5. Con el periodo julio 2023-junio 2024 los scripts comprueban los promedios,
   máximos y horarios publicados en H.11-H.14 antes de dibujar.
