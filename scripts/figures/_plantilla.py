"""Plantilla de una figura. Copiar y renombrar, no ejecutar directamente."""

from pathlib import Path

FIGURE_ID = "X.0"


def generate(context) -> dict[str, str]:
    # 1. Adquirir y verificar datos crudos.
    # source_path = context.acquire_source("source_id")

    # 2. Calcular y registrar los valores usados en la gráfica.
    datos_usados = [
        {"periodo": "ejemplo", "valor": 0.0},
    ]
    context.write_data_used(datos_usados)
    context.record_calculation(
        calculation_id="calculo_principal",
        formula="describir la fórmula exacta",
        inputs={"entrada": 0.0},
        result=0.0,
        unit="unidad",
        decimals=1,
    )

    # 3. Renderizar el texto cuando corresponda.
    context.render_text(
        "parrafo_figura.md.j2",
        variables={
            "periodo": "",
            "descripcion": "",
            "variacion": None,
            "mayor": None,
            "menor": None,
            "unidad": "",
            "decimales": 1,
        },
    )

    # 4. Generar la gráfica conservando el diseño original.
    output = context.expected_figure_path
    output.parent.mkdir(parents=True, exist_ok=True)
    raise NotImplementedError("Sustituir este marcador por la gráfica original actualizada")

    return {"figure_path": str(Path(output))}

