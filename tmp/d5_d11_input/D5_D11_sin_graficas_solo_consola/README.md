# Scripts D.5 a D.11 sin generación de gráficas

Este paquete contiene las versiones de los scripts D.5 a D.11 que **no generan gráficas ni archivos de salida de validación**.

## Comportamiento

Cada script:

- carga la base oficial ECSI 2024 del IFT;
- realiza los mismos cálculos ponderados usados por la versión gráfica;
- conserva la inferencia metodológica necesaria en D.9, D.10 y D.11;
- imprime en consola los valores que antes alimentaban la gráfica;
- no usa `matplotlib`;
- no genera PNG, JSON ni CSV de resultados.

## Archivos

- `_ecsi_d_common.py`: descarga, carga y funciones de cálculo.
- `figura_d5.py`
- `figura_d6.py`
- `figura_d7.py`
- `figura_d8.py`
- `figura_d9.py`
- `figura_d10.py`
- `figura_d11.py`

## Dependencias

```bash
pip install pandas
```

La base se descarga desde la fuente oficial del IFT si no existe localmente en `datos_ecsi/`.
