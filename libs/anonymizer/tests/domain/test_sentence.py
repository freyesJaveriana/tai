"""Paso 7: la definición única de «abre oración» (PD-2, CG-U10-02)."""

import pytest

from veridicus_anonymizer.domain.sentence import opens_sentence

NBSP = chr(0xA0)  # espacio de no separación


def _index(text: str, word: str) -> int:
    return text.index(word)


@pytest.mark.parametrize(
    "text",
    [
        "Casilda llegó.",
        "Eso pasó. Casilda llegó.",
        "¿Quién? Casilda llegó.",
        "¿Casilda llegó?",
        "¡Corran! Casilda gritó.",
        "¡Casilda corrió!",
        "Lo dijo así: Casilda llegaba tarde.",
        "Salió temprano; Casilda no estaba.",
        "Primera línea\nCasilda entró.",
        "Primera línea\r\nCasilda entró.",
        "Dijo «Casilda» y calló.",
        'Escribió "Casilda" en el cuaderno.',
        "Contó que “Casilda” vendía fruta.",
        "—Casilda vino —dijo.",
        "Eso pasó.   Casilda llegó.",
        f"Eso pasó.{NBSP}Casilda llegó.",
        "Eso pasó.\tCasilda llegó.",
    ],
    ids=[
        "inicio_de_valor",
        "punto",
        "interrogacion_de_cierre",
        "interrogacion_de_apertura",
        "exclamacion_de_cierre",
        "exclamacion_de_apertura",
        "dos_puntos",
        "punto_y_coma",
        "salto_de_linea",
        "retorno_y_salto",
        "comilla_angular",
        "comilla_recta",
        "comilla_curva",
        "raya",
        "varios_espacios",
        "espacio_de_no_separacion",
        "tabulador",
    ],
)
def test_every_opening_position_of_pd2_opens_a_sentence(text: str) -> None:
    assert opens_sentence(text, _index(text, "Casilda"))


@pytest.mark.parametrize(
    "text",
    [
        "Después vieron a Casilda en la plaza.",
        "Vio a Casilda, que llegó tarde.",
        "Habló con (Casilda) ayer.",
        "El hijo de Casilda se fue.",
    ],
    ids=["mitad_de_oracion", "tras_coma", "tras_parentesis", "tras_preposicion"],
)
def test_a_word_in_the_middle_of_a_sentence_does_not_open_one(text: str) -> None:
    assert not opens_sentence(text, _index(text, "Casilda"))


def test_a_sign_glued_to_the_word_still_opens_the_sentence() -> None:
    text = "Eso pasó.Casilda llegó."

    assert opens_sentence(text, _index(text, "Casilda"))
