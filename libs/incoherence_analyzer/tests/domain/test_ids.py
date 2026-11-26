"""Identificadores deterministas de los hallazgos (BR8.2)."""

from hypothesis import given
from hypothesis import strategies as st

from veridicus_incoherence_analyzer.domain.ids import format_id, positions_of, sort_key


def test_ids_have_two_digits_at_least_and_grow_past_99() -> None:
    assert format_id("SINT-0001", 1) == "SINT-0001-C01"
    assert format_id("SINT-0001", 9) == "SINT-0001-C09"
    assert format_id("SINT-0001", 10) == "SINT-0001-C10"
    assert format_id("SINT-0001", 100) == "SINT-0001-C100"


def test_positions_follow_the_sorted_turn_numbers_not_their_values() -> None:
    assert positions_of([10, 3, 7]) == {3: 0, 7: 1, 10: 2}


def test_the_key_orders_by_lowest_then_highest_position_then_position_of_quote_a() -> None:
    positions = {1: 0, 2: 1, 3: 2, 4: 3}

    early = sort_key(2, 4, "a", "b", "h", positions)
    earlier = sort_key(1, 4, "a", "b", "h", positions)
    narrow = sort_key(2, 3, "a", "b", "h", positions)
    swapped = sort_key(4, 2, "a", "b", "h", positions)

    assert earlier < narrow < early
    assert early < swapped, "a igual primer y último turno, gana la cita_a más temprana"


def test_the_normalized_quote_a_breaks_the_remaining_ties() -> None:
    positions = {1: 0, 2: 1}

    assert sort_key(1, 2, "alfa", "z", "h", positions) < sort_key(1, 2, "beta", "a", "h", positions)
    assert sort_key(1, 2, "alfa", "a", "h", positions) < sort_key(1, 2, "alfa", "b", "h", positions)
    assert sort_key(1, 2, "alfa", "a", "a", positions) < sort_key(1, 2, "alfa", "a", "b", positions)


Item = tuple[int, int, str, str, str]
ITEMS = st.lists(
    st.tuples(
        st.integers(min_value=1, max_value=6),
        st.integers(min_value=1, max_value=6),
        st.text(alphabet="abc", max_size=3),
        st.text(alphabet="abc", max_size=3),
        st.text(alphabet="abc", max_size=3),
    ),
    min_size=1,
    max_size=12,
    unique=True,
)


@given(items=ITEMS, data=st.data())
def test_property_the_order_does_not_depend_on_the_order_of_the_input(
    items: list[Item], data: st.DataObject
) -> None:
    positions = positions_of(range(1, 7))
    shuffled = data.draw(st.permutations(items))

    def order(values: list[Item]) -> list[Item]:
        return sorted(
            values,
            key=lambda item: sort_key(item[0], item[1], item[2], item[3], item[4], positions),
        )

    assert order(items) == order(shuffled)
