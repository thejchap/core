"""The sensor tests for the nexia platform."""

from http import HTTPStatus

from tryke import expect, test

from homeassistant.components.nexia import util


@test
async def is_invalid_auth_code() -> None:
    """Test for invalid auth."""

    expect(util.is_invalid_auth_code(HTTPStatus.UNAUTHORIZED)).to_be(True)
    expect(util.is_invalid_auth_code(HTTPStatus.FORBIDDEN)).to_be(True)
    expect(util.is_invalid_auth_code(HTTPStatus.NOT_FOUND)).to_be(False)


@test
async def percent_conv() -> None:
    """Test percentage conversion."""

    expect(util.percent_conv(0.12)).to_equal(12.0)
    expect(util.percent_conv(0.123)).to_equal(12.3)
