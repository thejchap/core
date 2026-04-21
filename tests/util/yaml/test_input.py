"""Test inputs."""

from tryke import expect, test

from homeassistant.util.yaml import (
    Input,
    UndefinedSubstitution,
    extract_inputs as _extract_inputs,
    substitute as _substitute,
)


@test
def extract_inputs() -> None:
    """Test extracting inputs from data."""
    expect(_extract_inputs(Input("hello"))).to_equal({"hello"})
    expect(_extract_inputs({"info": [1, Input("hello"), 2, Input("world")]})).to_equal(
        {"hello", "world"}
    )


@test
def substitute() -> None:
    """Test we can substitute."""
    expect(_substitute(Input("hello"), {"hello": 5})).to_equal(5)

    expect(lambda: _substitute(Input("hello"), {})).to_raise(UndefinedSubstitution)

    expect(
        _substitute(
            {"info": [1, Input("hello"), 2, Input("world")]},
            {"hello": 5, "world": 10},
        )
    ).to_equal({"info": [1, 5, 2, 10]})
