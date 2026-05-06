"""Test collection extension."""

from __future__ import annotations

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError

from tests.hass_fixtures import hass
from tests.helpers.template.helpers import render


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("list", value=[1, 2, 3], expected=True),
    test.case("dict", value={"a": 1}, expected=False),
    test.case("set", value={1, 2, 3}, expected=False),
    test.case("tuple", value=(1, 2, 3), expected=False),
    test.case("str", value="abc", expected=False),
    test.case("empty_str", value="", expected=False),
    test.case("int", value=5, expected=False),
    test.case("none", value=None, expected=False),
    test.case("dict2", value={"foo": "bar", "baz": "qux"}, expected=False),
)
async def is_list(
    value: Any,
    expected: bool,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test list test."""
    expect(render(hass, "{{ value is list }}", {"value": value})).to_equal(expected)


@test.cases(
    test.case("list", value=[1, 2, 3], expected=False),
    test.case("dict", value={"a": 1}, expected=False),
    test.case("set", value={1, 2, 3}, expected=True),
    test.case("tuple", value=(1, 2, 3), expected=False),
    test.case("str", value="abc", expected=False),
    test.case("empty_str", value="", expected=False),
    test.case("int", value=5, expected=False),
    test.case("none", value=None, expected=False),
    test.case("dict2", value={"foo": "bar", "baz": "qux"}, expected=False),
)
async def is_set(
    value: Any,
    expected: bool,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test set test."""
    expect(render(hass, "{{ value is set }}", {"value": value})).to_equal(expected)


@test.cases(
    test.case("list", value=[1, 2, 3], expected=False),
    test.case("dict", value={"a": 1}, expected=False),
    test.case("set", value={1, 2, 3}, expected=False),
    test.case("tuple", value=(1, 2, 3), expected=True),
    test.case("str", value="abc", expected=False),
    test.case("empty_str", value="", expected=False),
    test.case("int", value=5, expected=False),
    test.case("none", value=None, expected=False),
    test.case("dict2", value={"foo": "bar", "baz": "qux"}, expected=False),
)
async def is_tuple(
    value: Any,
    expected: bool,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test tuple test."""
    expect(render(hass, "{{ value is tuple }}", {"value": value})).to_equal(expected)


@test.cases(
    test.case("list", value=[1, 2, 3], expected={1, 2, 3}),
    test.case("dict", value={"a": 1}, expected={"a"}),
    test.case("set", value={1, 2, 3}, expected={1, 2, 3}),
    test.case("tuple", value=(1, 2, 3), expected={1, 2, 3}),
    test.case("str", value="abc", expected={"a", "b", "c"}),
    test.case("empty_str", value="", expected=set()),
    test.case("range", value=range(3), expected={0, 1, 2}),
    test.case("dict2", value={"foo": "bar", "baz": "qux"}, expected={"foo", "baz"}),
)
async def set_conversion(
    value: Any,
    expected: set[Any],
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test set conversion."""
    expect(render(hass, "{{ set(value) }}", {"value": value})).to_equal(expected)


@test.cases(
    test.case("list", value=[1, 2, 3], expected=(1, 2, 3)),
    test.case("dict", value={"a": 1}, expected=("a",)),
    test.case("set", value={1, 2, 3}, expected=(1, 2, 3)),
    test.case("tuple", value=(1, 2, 3), expected=(1, 2, 3)),
    test.case("str", value="abc", expected=("a", "b", "c")),
    test.case("empty_str", value="", expected=()),
    test.case("range", value=range(3), expected=(0, 1, 2)),
    test.case(
        "dict2", value={"foo": "bar", "baz": "qux"}, expected=("foo", "baz")
    ),
)
async def tuple_conversion(
    value: Any,
    expected: tuple[Any, ...],
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test tuple conversion."""
    result = render(hass, "{{ tuple(value) }}", {"value": value})
    if isinstance(value, set):  # Sets don't have predictable order
        expect(set(result)).to_equal(set(expected))
    else:
        expect(result).to_equal(expected)


@test.cases(
    test.case("equal_len", cola=[1, 2], colb=[3, 4], expected=[(1, 3), (2, 4)]),
    test.case("b_longer", cola=[1, 2], colb=[3, 4, 5], expected=[(1, 3), (2, 4)]),
    test.case("a_longer", cola=[1, 2, 3, 4], colb=[3, 4], expected=[(1, 3), (2, 4)]),
)
async def zip_test(
    cola: list[int],
    colb: list[int],
    expected: list[tuple[int, int]],
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test zip."""
    for tpl in (
        "{{ zip(cola, colb) | list }}",
        "[{% for a, b in zip(cola, colb) %}({{a}}, {{b}}), {% endfor %}]",
    ):
        expect(render(hass, tpl, {"cola": cola, "colb": colb})).to_equal(expected)


@test.cases(
    test.case("ints", col=[(1, 3), (2, 4)], expected=[(1, 2), (3, 4)]),
    test.case(
        "strs", col=["ax", "by", "cz"], expected=[("a", "b", "c"), ("x", "y", "z")]
    ),
)
async def unzip(
    col: list[Any],
    expected: list[tuple[Any, ...]],
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test unzipping using zip."""
    for tpl in (
        "{{ zip(*col) | list }}",
        "{% set a, b = zip(*col) %}[{{a}}, {{b}}]",
    ):
        expect(render(hass, tpl, {"col": col})).to_equal(expected)


@test
async def shuffle(hass: HomeAssistant = Depends(hass)) -> None:
    """Test shuffle."""
    result = render(hass, "{{ shuffle([1, 2, 3, 4, 5]) }}")
    expect(len(result)).to_equal(5)
    expect(set(result)).to_equal({1, 2, 3, 4, 5})

    result1 = render(hass, "{{ shuffle([1, 2, 3, 4, 5], seed=42) }}")
    result2 = render(hass, "{{ shuffle([1, 2, 3, 4, 5], seed=42) }}")
    expect(result1).to_equal(result2)  # Same seed should give same result

    result3 = render(hass, "{{ shuffle([1, 2, 3, 4, 5], seed=123) }}")
    expect(len(result3)).to_equal(5)
    expect(set(result3)).to_equal({1, 2, 3, 4, 5})


@test
async def flatten(hass: HomeAssistant = Depends(hass)) -> None:
    """Test flatten."""
    expect(render(hass, "{{ flatten([[1, 2], [3, 4]]) }}")).to_equal([1, 2, 3, 4])

    expected = [1, 2, 3, 4, 5, 6, 7, 8]
    expect(
        render(hass, "{{ flatten([[[1, 2], [3, 4]], [[5, 6], [7, 8]]]) }}")
    ).to_equal(expected)

    expect(
        render(hass, "{{ flatten([[[1, 2], [3, 4]], [[5, 6], [7, 8]]], levels=1) }}")
    ).to_equal([[1, 2], [3, 4], [5, 6], [7, 8]])

    expect(render(hass, "{{ flatten([[1, 'a'], [2, 'b']]) }}")).to_equal(
        [1, "a", 2, "b"]
    )

    expect(render(hass, "{{ flatten([]) }}")).to_equal([])

    expect(render(hass, "{{ flatten([1, 2, 3]) }}")).to_equal([1, 2, 3])


@test
async def intersect(hass: HomeAssistant = Depends(hass)) -> None:
    """Test intersect."""
    result = render(hass, "{{ [1, 2, 3, 4] | intersect([3, 4, 5, 6]) | sort }}")
    expect(result).to_equal([3, 4])

    result = render(hass, "{{ [1, 2] | intersect([3, 4]) }}")
    expect(result).to_equal([])

    result = render(hass, "{{ ['a', 'b', 'c'] | intersect(['b', 'c', 'd']) | sort }}")
    expect(result).to_equal(["b", "c"])

    result = render(hass, "{{ [] | intersect([1, 2, 3]) }}")
    expect(result).to_equal([])


@test
async def difference(hass: HomeAssistant = Depends(hass)) -> None:
    """Test difference."""
    result = render(hass, "{{ [1, 2, 3, 4] | difference([3, 4, 5, 6]) | sort }}")
    expect(result).to_equal([1, 2])

    result = render(hass, "{{ [1, 2] | difference([1, 2, 3, 4]) }}")
    expect(result).to_equal([])

    result = render(hass, "{{ ['a', 'b', 'c'] | difference(['b', 'c', 'd']) | sort }}")
    expect(result).to_equal(["a"])

    result = render(hass, "{{ [] | difference([1, 2, 3]) }}")
    expect(result).to_equal([])


@test
async def union(hass: HomeAssistant = Depends(hass)) -> None:
    """Test union."""
    result = render(hass, "{{ [1, 2, 3] | union([3, 4, 5]) | sort }}")
    expect(result).to_equal([1, 2, 3, 4, 5])

    result = render(hass, "{{ ['a', 'b'] | union(['b', 'c']) | sort }}")
    expect(result).to_equal(["a", "b", "c"])

    result = render(hass, "{{ [] | union([1, 2, 3]) | sort }}")
    expect(result).to_equal([1, 2, 3])

    result = render(hass, "{{ [1, 1, 2, 2] | union([2, 2, 3, 3]) | sort }}")
    expect(result).to_equal([1, 2, 3])


@test
async def symmetric_difference(hass: HomeAssistant = Depends(hass)) -> None:
    """Test symmetric_difference."""
    result = render(
        hass, "{{ [1, 2, 3, 4] | symmetric_difference([3, 4, 5, 6]) | sort }}"
    )
    expect(result).to_equal([1, 2, 5, 6])

    result = render(hass, "{{ [1, 2, 3] | symmetric_difference([1, 2, 3]) }}")
    expect(result).to_equal([])

    result = render(
        hass, "{{ ['a', 'b', 'c'] | symmetric_difference(['b', 'c', 'd']) | sort }}"
    )
    expect(result).to_equal(["a", "d"])

    result = render(hass, "{{ [] | symmetric_difference([1, 2, 3]) | sort }}")
    expect(result).to_equal([1, 2, 3])


@test
async def collection_functions_as_tests(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that type checking functions work as tests."""
    expect(render(hass, "{{ [1,2,3] is list }}")).to_be(True)
    expect(render(hass, "{{ set([1,2,3]) is set }}")).to_be(True)
    expect(render(hass, "{{ (1,2,3) is tuple }}")).to_be(True)


@test
async def collection_error_handling(hass: HomeAssistant = Depends(hass)) -> None:
    """Test error handling in collection functions."""

    expect(lambda: render(hass, "{{ flatten(123) }}")).to_raise(
        TemplateError, match="flatten expected a list"
    )

    expect(lambda: render(hass, "{{ [1, 2] | intersect(123) }}")).to_raise(
        TemplateError, match="intersect expected a list"
    )

    expect(lambda: render(hass, "{{ [1, 2] | difference(123) }}")).to_raise(
        TemplateError, match="difference expected a list"
    )

    expect(lambda: render(hass, "{{ shuffle() }}")).to_raise(
        TemplateError, match="shuffle expected at least 1 argument"
    )
