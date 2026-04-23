"""Test the One-Time Password (OTP) config flow."""

from __future__ import annotations

import binascii
from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.otp.const import CONF_NEW_TOKEN, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_CODE, CONF_NAME, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import mock_pyotp as mock_pyotp_fx, mock_setup_entry as mock_setup_fx

TEST_DATA = {
    CONF_NAME: "OTP Sensor",
    CONF_TOKEN: "2FX5 FBSY RE6V EC2F SHBQ CRKO 2GND VZ52",
}
TEST_DATA_RESULT = {
    CONF_NAME: "OTP Sensor",
    CONF_TOKEN: "2FX5FBSYRE6VEC2FSHBQCRKO2GNDVZ52",
}

TEST_DATA_2 = {
    CONF_NAME: "OTP Sensor",
    CONF_NEW_TOKEN: True,
}

TEST_DATA_3 = {
    CONF_NAME: "OTP Sensor",
    CONF_TOKEN: "",
}


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _pyotp: MagicMock = Depends(mock_pyotp_fx),
) -> None:
    """Wire mock_network and mock_pyotp for every test."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_fx),
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
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_token", binascii.Error, "invalid_token"),
    test.case("unknown", IndexError, "unknown"),
)
async def errors_and_recover(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_fx),
    mock_pyotp: MagicMock = Depends(mock_pyotp_fx),
) -> None:
    """Test errors and recover."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mock_pyotp.TOTP().now.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_DATA,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_pyotp.TOTP().now.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_DATA,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OTP Sensor")
    expect(result["data"]).to_equal(TEST_DATA_RESULT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def generate_new_token(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_fx),
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
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def generate_new_token_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_fx),
    mock_pyotp: MagicMock = Depends(mock_pyotp_fx),
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
    mock_pyotp.TOTP().verify.return_value = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: "123456"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_code"})

    mock_pyotp.TOTP().verify.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: "123456"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OTP Sensor")
    expect(result["data"]).to_equal(TEST_DATA_RESULT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
