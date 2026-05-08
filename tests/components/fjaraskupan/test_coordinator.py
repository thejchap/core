"""Test the Fjäråskupan coordinator module."""

from fjaraskupan import (
    FjaraskupanConnectionError,
    FjaraskupanError,
    FjaraskupanReadError,
    FjaraskupanWriteError,
)
from tryke import expect, test

from homeassistant.components.fjaraskupan.const import DOMAIN
from homeassistant.components.fjaraskupan.coordinator import exception_converter
from homeassistant.exceptions import HomeAssistantError


@test.cases(
    test.case(
        "read",
        exception=FjaraskupanReadError(),
        translation_key="read_error",
        translation_placeholder=None,
    ),
    test.case(
        "write",
        exception=FjaraskupanWriteError(),
        translation_key="write_error",
        translation_placeholder=None,
    ),
    test.case(
        "connection",
        exception=FjaraskupanConnectionError(),
        translation_key="connection_error",
        translation_placeholder=None,
    ),
    test.case(
        "unexpected",
        exception=FjaraskupanError("Some error"),
        translation_key="unexpected_error",
        translation_placeholder={"msg": "Some error"},
    ),
)
def exeception_wrapper(
    *,
    exception: Exception,
    translation_key: str,
    translation_placeholder: dict[str, str] | None,
) -> None:
    """Test our exception conversion."""
    raised: HomeAssistantError | None = None
    try:
        with exception_converter():
            raise exception
    except HomeAssistantError as err:
        raised = err

    expect(raised).not_.to_be(None)
    expect(isinstance(raised, HomeAssistantError)).to_be(True)
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal(translation_key)
    expect(raised.translation_placeholders).to_equal(translation_placeholder)
