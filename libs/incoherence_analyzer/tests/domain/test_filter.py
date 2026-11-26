"""Filtro determinista de candidatos y deduplicación (BR5.2 a BR5.6, BR9.3, BR4.3; AUTONOMIA-05).

Sin llamadas: el filtro decide con el texto de los turnos, y cada candidato se descarta con el motivo
del primer filtro que falla, en el orden marca alterada, campo vacío, cita_a, cita_b, vocabulario.
"""

import copy
from typing import Any

import pytest

from tests.support import T1, T2, T3, T4, default_turns, finding
from veridicus_incoherence_analyzer.domain.filter import (
    Discard,
    InvalidJudgeResponse,
    Survivor,
    Window,
    filter_candidates,
)

INVENTED = "Texto que no está en ningún turno."


def turns_by_number(turns: list[dict[str, Any]] | None = None) -> dict[int, dict[str, Any]]:
    return {turn["n"]: turn for turn in (default_turns() if turns is None else turns)}


def run(
    candidates: list[dict[str, Any]],
    *,
    markers: list[str] | None = None,
    turns: dict[int, dict[str, Any]] | None = None,
) -> tuple[tuple[Survivor, ...], tuple[Discard, ...]]:
    result = filter_candidates(
        [Window(candidates, markers or [])], turns_by_number() if turns is None else turns
    )
    return result.survivors, result.discards


def reasons(discards: tuple[Discard, ...]) -> list[str]:
    return [discard.reason for discard in discards]


def test_a_well_formed_candidate_with_verified_quotes_survives() -> None:
    survivors, discards = run([finding()])

    assert discards == ()
    assert len(survivors) == 1
    assert (survivors[0].turn_a, survivors[0].turn_b) == (2, 4)
    assert survivors[0].candidate["hecho"] == finding()["hecho"]


def test_no_candidates_give_an_empty_result() -> None:
    assert run([]) == ((), ())
    assert filter_candidates([], turns_by_number()).survivors == ()


@pytest.mark.parametrize(
    ("pointer", "discarded"),
    [
        ("/hallazgos/1/observaciones", [1]),
        ("/hallazgos/1/hecho", [1]),
        ("/hallazgos/0/cita_b/cita", [0]),
        ("/hallazgos/1", [1]),
        ("/hallazgos/0/cita_a/turno", [0]),
    ],
)
def test_an_altered_marker_discards_only_the_candidate_that_owns_the_pointer(
    pointer: str, discarded: list[int]
) -> None:
    candidates = [finding(), finding(hecho="Segundo hecho")]

    survivors, discards = run(candidates, markers=[pointer])

    assert reasons(discards) == ["marca_alterada"]
    assert [s.candidate["hecho"] for s in survivors] == [
        c["hecho"] for index, c in enumerate(candidates) if index not in discarded
    ]


def test_a_pointer_prefix_is_matched_by_segment_so_candidate_1_does_not_own_candidate_10() -> None:
    # Doce pares distintos: cada cita_a es otro tramo del turno 2, así nada se deduplica.
    candidates = [
        finding(hecho=f"Hecho {index}", a=(2, T2[index : index + 12])) for index in range(12)
    ]

    survivors, discards = run(candidates, markers=["/hallazgos/1/hecho"])

    assert reasons(discards) == ["marca_alterada"]
    assert len(survivors) == 11
    assert "Hecho 1" not in {s.candidate["hecho"] for s in survivors}
    assert "Hecho 10" in {s.candidate["hecho"] for s in survivors}


@pytest.mark.parametrize(
    "pointer",
    [
        "/hallazgos/5/observaciones",
        "/comentario",
        "/hallazgos",
        "",
        "/hallazgos/x/hecho",
        "/hallazgos/01",
    ],
)
def test_a_pointer_that_falls_in_no_candidate_invalidates_the_whole_response(pointer: str) -> None:
    with pytest.raises(InvalidJudgeResponse):
        run([finding()], markers=[pointer])


@pytest.mark.parametrize("campo", ["hecho", "observaciones", "cita_a", "cita_b"])
def test_a_field_with_only_whitespace_is_discarded_with_campo_faltante(campo: str) -> None:
    blank = finding()
    if campo in {"cita_a", "cita_b"}:
        blank[campo]["cita"] = " \t\n  "
    else:
        blank[campo] = " \t\n "

    survivors, discards = run([blank, finding(hecho="Otro")])

    assert reasons(discards) == ["campo_faltante"]
    assert [s.candidate["hecho"] for s in survivors] == ["Otro"]


def test_a_quote_altered_in_one_character_is_discarded_as_cita_no_verificada() -> None:
    altered = finding(a=(2, T2.replace("Roncancio", "Roncancia")))

    survivors, discards = run([altered])

    assert survivors == ()
    assert reasons(discards) == ["cita_no_verificada"]


def test_a_quote_that_belongs_to_another_turn_is_discarded_as_cita_en_otro_turno() -> None:
    survivors, discards = run([finding(a=(2, T4))])

    assert survivors == ()
    assert reasons(discards) == ["cita_en_otro_turno"]
    assert (discards[0].turno_a, discards[0].turno_b) == ("T2", "T4")


def test_a_quote_found_in_two_other_turns_is_not_found_rather_than_another_turn() -> None:
    turns = default_turns()
    turns[2]["texto"] = T4  # el texto de T4 aparece ahora en T3 y en T4
    survivors, discards = run([finding(a=(2, T4))], turns=turns_by_number(turns))

    assert survivors == ()
    assert reasons(discards) == ["cita_no_verificada"]


def test_a_quote_in_its_own_turn_wins_even_if_it_also_appears_in_another() -> None:
    turns = default_turns()
    turns[2]["texto"] = T2  # T2 y T3 comparten texto
    survivors, discards = run([finding(a=(2, T2))], turns=turns_by_number(turns))

    assert discards == ()
    assert len(survivors) == 1


@pytest.mark.parametrize(
    "label",
    ["T" + "9" * 5000, "T" + "9" * 10, "T" + "0" * 5000 + "2"],
    ids=["5000_digitos", "10_digitos", "ceros_a_la_izquierda_sin_limite"],
)
def test_a_turn_label_that_is_too_long_is_cita_no_verificada_and_never_raises(label: str) -> None:
    candidate = finding()
    candidate["cita_a"]["turno"] = label

    survivors, discards = run([candidate])

    assert survivors == ()
    assert reasons(discards) == ["cita_no_verificada"]
    assert discards[0].turno_a is None, "una etiqueta fuera de la forma acotada no se copia"


def test_a_nine_digit_turn_label_reaches_the_turn_lookup() -> None:
    turns = default_turns()
    turns[1]["n"] = 999_999_999
    candidate = finding(a=(999_999_999, T2))

    survivors, discards = run([candidate], turns=turns_by_number(turns))

    assert discards == ()
    assert survivors[0].turn_a == 999_999_999


@pytest.mark.parametrize("label", ["T9", "T0", "turno 2", "2", "T", "T-1", "t2", "T2x", ""])
def test_an_unknown_or_malformed_turn_is_cita_no_verificada(label: str) -> None:
    candidate = finding()
    candidate["cita_a"]["turno"] = label

    survivors, discards = run([candidate])

    assert survivors == ()
    assert reasons(discards) == ["cita_no_verificada"]


def test_a_discard_names_the_turns_as_the_judge_wrote_them_when_they_have_the_c6_form() -> None:
    candidate = finding(a=(2, INVENTED))
    candidate["cita_b"]["turno"] = "turno cuatro"

    _, discards = run([candidate])

    assert (discards[0].turno_a, discards[0].turno_b) == ("T2", None)


@pytest.mark.parametrize(
    ("a", "b", "motivo"),
    [
        ((2, T2), (4, T2), "cita_en_otro_turno"),
        ((2, T2), (4, INVENTED), "cita_no_verificada"),
        ((2, T4), (4, INVENTED), "cita_en_otro_turno"),
        ((2, INVENTED), (4, T2), "cita_no_verificada"),
    ],
)
def test_the_first_failing_quote_decides_the_reason(
    a: tuple[int, str], b: tuple[int, str], motivo: str
) -> None:
    _, discards = run([finding(a=a, b=b)])

    assert reasons(discards) == [motivo]


def test_filter_order_a_marker_wins_over_a_blank_field() -> None:
    candidate = finding()
    candidate["hecho"] = " "

    _, discards = run([candidate], markers=["/hallazgos/0/hecho"])

    assert reasons(discards) == ["marca_alterada"]


def test_filter_order_a_blank_field_wins_over_a_failing_quote() -> None:
    candidate = finding(a=(2, INVENTED))
    candidate["hecho"] = " "

    _, discards = run([candidate])

    assert reasons(discards) == ["campo_faltante"]


def test_filter_order_a_failing_quote_wins_over_forbidden_vocabulary() -> None:
    candidate = finding(a=(2, INVENTED))
    candidate["observaciones"] = "La persona miente sobre este punto."

    _, discards = run([candidate])

    assert reasons(discards) == ["cita_no_verificada"]


@pytest.mark.parametrize("campo", ["hecho", "observaciones"])
def test_forbidden_vocabulary_discards_the_candidate_and_the_others_go_on(campo: str) -> None:
    candidate = finding()
    candidate[campo] = "La persona miente sobre este punto."

    survivors, discards = run([candidate, finding(hecho="Otro hecho")])

    assert reasons(discards) == ["vocabulario_prohibido"]
    assert [s.candidate["hecho"] for s in survivors] == ["Otro hecho"]


def test_a_forbidden_term_inside_a_literal_quote_does_not_discard_the_candidate() -> None:
    turns = default_turns()
    turns[1]["texto"] = "Dijo que él miente poco y llegó a Villa Rocamora antes del mediodía."
    candidate = finding(a=(2, "él miente poco"))

    survivors, discards = run([candidate], turns=turns_by_number(turns))

    assert discards == ()
    assert len(survivors) == 1, "la cita no se escanea (BR9.3)"


@pytest.mark.parametrize("campo", ["hecho", "observaciones"])
def test_a_quoted_span_that_is_literal_in_a_turn_is_not_scanned(campo: str) -> None:
    turns = default_turns()
    turns[1]["texto"] = "Dijo que es falso que llegara antes del mediodía a Villa Rocamora."
    candidate = finding(a=(2, "es falso que llegara"))
    candidate[campo] = "El turno dice «es falso que llegara» y luego cambia."

    survivors, discards = run([candidate], turns=turns_by_number(turns))

    assert discards == ()
    assert len(survivors) == 1


@pytest.mark.parametrize("campo", ["hecho", "observaciones"])
def test_a_quoted_span_that_is_in_no_turn_is_scanned(campo: str) -> None:
    candidate = finding()
    candidate[campo] = "Se afirma «miente en todo» sin base."

    survivors, discards = run([candidate])

    assert survivors == ()
    assert reasons(discards) == ["vocabulario_prohibido"]


def test_a_repeated_pair_in_two_windows_keeps_only_the_one_of_the_lowest_window() -> None:
    first = finding(hecho="Primera ventana")
    second = finding(hecho="Segunda ventana")

    result = filter_candidates([Window([first], []), Window([second], [])], turns_by_number())

    assert [s.candidate["hecho"] for s in result.survivors] == ["Primera ventana"]
    assert result.discards == (), "los repetidos se unen sin descarte"


def test_a_repeated_pair_with_the_quotes_in_the_other_order_is_the_same_pair() -> None:
    forward = finding(hecho="Directo", a=(2, T2), b=(4, T4))
    reverse = finding(hecho="Inverso", a=(4, T4), b=(2, T2))

    survivors, discards = run([forward, reverse])

    assert [s.candidate["hecho"] for s in survivors] == ["Directo"]
    assert discards == ()


def test_the_pair_is_compared_with_the_quotes_normalized_in_whitespace() -> None:
    plain = finding(hecho="Normal")
    spaced = finding(
        hecho="Con espacios",
        a=(2, "Casilda   Roncancio llegó a Villa Rocamora antes del mediodía."),
    )

    survivors, _ = run([plain, spaced])

    assert [s.candidate["hecho"] for s in survivors] == ["Normal"]


def test_the_same_pair_twice_in_one_window_keeps_the_lowest_ordinal() -> None:
    survivors, _ = run([finding(hecho="Uno"), finding(hecho="Dos")])

    assert [s.candidate["hecho"] for s in survivors] == ["Uno"]


def test_different_pairs_are_not_deduplicated() -> None:
    other = finding(hecho="Otro par", a=(1, T1), b=(4, T4))

    survivors, discards = run([finding(), other])

    assert len(survivors) == 2
    assert discards == ()


def test_a_discarded_candidate_never_reaches_the_deduplication() -> None:
    bad_first = finding(hecho="Mal", a=(2, INVENTED))
    good = finding(hecho="Bien")

    survivors, discards = run([bad_first, good])

    assert [s.candidate["hecho"] for s in survivors] == ["Bien"]
    assert reasons(discards) == ["cita_no_verificada"]


def test_survivors_and_discards_keep_the_order_of_windows_and_ordinals() -> None:
    first = [finding(hecho="A", a=(2, INVENTED)), finding(hecho="B", a=(1, T1))]
    second = [finding(hecho="C", a=(3, T3), b=(4, T4)), finding(hecho="D", a=(2, T4))]

    result = filter_candidates([Window(first, []), Window(second, [])], turns_by_number())

    assert [s.candidate["hecho"] for s in result.survivors] == ["B", "C"]
    assert [(s.window, s.ordinal) for s in result.survivors] == [(0, 1), (1, 0)]
    assert reasons(result.discards) == ["cita_no_verificada", "cita_en_otro_turno"]


def test_the_filter_does_not_modify_the_candidates_it_receives() -> None:
    candidates = [finding(), finding(hecho="Otro", a=(1, T1))]
    before = copy.deepcopy(candidates)

    run(candidates)

    assert candidates == before


def test_the_sort_key_orders_survivors_by_first_cited_turn() -> None:
    late = finding(hecho="Tarde", a=(3, T3), b=(4, T4))
    early = finding(hecho="Temprano", a=(1, T1), b=(4, T4))

    survivors, _ = run([late, early])
    positions = {1: 0, 2: 1, 3: 2, 4: 3}

    ordered = sorted(survivors, key=lambda survivor: survivor.sort_key(positions))

    assert [s.candidate["hecho"] for s in ordered] == ["Temprano", "Tarde"]
