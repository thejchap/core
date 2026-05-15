"""Test ViCare utils."""

from tryke import expect, test

from homeassistant.components.vicare.utils import filter_state


@test.cases(
    test.case("none", state=None, expected_result=None),
    test.case("unknown", state="unknown", expected_result=None),
    test.case("nothing", state="nothing", expected_result=None),
    test.case("levelOne", state="levelOne", expected_result="levelOne"),
)
async def filter_state_cases(
    state: str | None,
    expected_result: str | None,
) -> None:
    """Test filter_state."""
    expect(filter_state(state)).to_equal(expected_result)
