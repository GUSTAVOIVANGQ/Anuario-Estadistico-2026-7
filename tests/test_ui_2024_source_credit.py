from anuario2026.ui_2024 import format_source_credit


def test_format_source_credit_replaces_ift_and_crt_prefixes() -> None:
    assert format_source_credit("IFT con datos del INEGI.") == (
        "Elaborado por CRT con datos del INEGI."
    )
    assert format_source_credit("CRT con datos de operadores.") == (
        "Elaborado por CRT con datos de operadores."
    )
    assert format_source_credit("IFT, Encuesta 2024.") == (
        "Elaborado por CRT, Encuesta 2024."
    )


def test_format_source_credit_is_idempotent_and_preserves_other_text() -> None:
    credit = "Elaborado por CRT con datos del INEGI."
    assert format_source_credit(credit) == credit
    assert format_source_credit("Nota: cifras preliminares.") == "Nota: cifras preliminares."
    assert format_source_credit(None) is None
