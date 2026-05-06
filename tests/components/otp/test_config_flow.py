"""Test the One-Time Password (OTP) config flow."""

import binascii
from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.otp.const import CONF_NEW_TOKEN, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_CODE, CONF_NAME, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_pyotp, mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture

TEST_DATA = {
    CONF_NAME: "OTP Sensor",
    CONF_TOKEN: "2FX5 FBSY RE6V EC2F SHBQ CRKO 2GND VZ52",
}
TEST_DATA_RESULT = {
    CONF_NAME: "OTP Sensor",
    CONF_TOKEN: "2FX5FBSYRE6VEC2FSHBQCRKO2GNDVZ52",
}
TEST_DATA_2 = {CONF_NAME: "OTP Sensor", CONF_NEW_TOKEN: True}
TEST_DATA_3 = {CONF_NAME: "OTP Sensor", CONF_TOKEN: ""}


@fixture
def _trigger_executor(
    _setup: AsyncMock = Depends(mock_setup_entry),
    _pyotp: MagicMock = Depends(mock_pyotp),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OTP Sensor")
    expect(result["data"]).to_equal(TEST_DATA_RESULT)
    expect(len(setup.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_token", exception=binascii.Error, error="invalid_token"),
    test.case("unknown", exception=IndexError, error="unknown"),
)
async def errors_and_recover(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    pyotp: MagicMock = Depends(mock_pyotp),
) -> None:
    """Test errors and recover."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    pyotp.TOTP().now.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_DATA,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    pyotp.TOTP().now.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_DATA,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OTP Sensor")
    expect(result["data"]).to_equal(TEST_DATA_RESULT)
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def generate_new_token(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test form generate new token."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA_2,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: "123456"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OTP Sensor")
    expect(result["data"]).to_equal(TEST_DATA_RESULT)
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def generate_new_token_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    pyotp: MagicMock = Depends(mock_pyotp),
) -> None:
    """Test input validation errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA_3,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_token"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA_2,
    )
    pyotp.TOTP().verify.return_value = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: "123456"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_code"})

    pyotp.TOTP().verify.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: "123456"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OTP Sensor")
    expect(result["data"]).to_equal(TEST_DATA_RESULT)
    expect(len(setup.mock_calls)).to_equal(1)
