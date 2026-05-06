"""Tests for the Tami4 config flow."""

from unittest.mock import AsyncMock, patch

from Tami4EdgeAPI import exceptions
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.tami4.const import CONF_PHONE, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock__get_devices_metadata,
    mock__get_devices_metadata_no_name,
    mock_setup_entry,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def step_user_valid_number(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _devices_metadata: None = Depends(mock__get_devices_metadata),
) -> None:
    """Test user step with valid phone number."""
    with patch(
        "homeassistant.components.tami4.config_flow.Tami4EdgeAPI.request_otp",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PHONE: "+972555555555"},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("otp")
        expect(result["errors"]).to_equal({})


@test
async def step_user_invalid_number(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _devices_metadata: None = Depends(mock__get_devices_metadata),
) -> None:
    """Test user step with invalid phone number."""
    with patch(
        "homeassistant.components.tami4.config_flow.Tami4EdgeAPI.request_otp",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PHONE: "+275123"},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": "invalid_phone"})


@test.cases(
    test.case("unknown", side_effect=Exception, expected_error="unknown"),
    test.case(
        "cannot_connect",
        side_effect=exceptions.OTPFailedException,
        expected_error="cannot_connect",
    ),
)
async def step_user_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _devices_metadata: None = Depends(mock__get_devices_metadata),
    *,
    side_effect: type[Exception],
    expected_error: str,
) -> None:
    """Test user step with exception."""
    with patch(
        "homeassistant.components.tami4.config_flow.Tami4EdgeAPI.request_otp",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PHONE: "+972555555555"},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": expected_error})


@test
async def step_otp_valid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _devices_metadata: None = Depends(mock__get_devices_metadata),
) -> None:
    """Test user step with valid phone number."""
    with (
        patch(
            "homeassistant.components.tami4.config_flow.Tami4EdgeAPI.request_otp",
            return_value=None,
        ),
        patch(
            "homeassistant.components.tami4.config_flow.Tami4EdgeAPI.submit_otp",
            return_value="refresh_token",
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PHONE: "+972555555555"},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("otp")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"otp": "123456"},
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("Drink Water")
        expect("refresh_token" in result["data"]).to_be(True)


@test
async def step_otp_valid_device_no_name(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _devices_metadata: None = Depends(mock__get_devices_metadata_no_name),
) -> None:
    """Test user step with valid phone number."""
    with (
        patch(
            "homeassistant.components.tami4.config_flow.Tami4EdgeAPI.request_otp",
            return_value=None,
        ),
        patch(
            "homeassistant.components.tami4.config_flow.Tami4EdgeAPI.submit_otp",
            return_value="refresh_token",
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PHONE: "+972555555555"},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("otp")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"otp": "123456"},
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("Tami4")
        expect("refresh_token" in result["data"]).to_be(True)


@test.cases(
    test.case("unknown", side_effect=Exception, expected_error="unknown"),
    test.case(
        "cannot_connect",
        side_effect=exceptions.Tami4EdgeAPIException,
        expected_error="cannot_connect",
    ),
    test.case(
        "invalid_auth",
        side_effect=exceptions.OTPFailedException,
        expected_error="invalid_auth",
    ),
)
async def step_otp_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _devices_metadata: None = Depends(mock__get_devices_metadata),
    *,
    side_effect: type[Exception],
    expected_error: str,
) -> None:
    """Test user step with valid phone number."""
    with (
        patch(
            "homeassistant.components.tami4.config_flow.Tami4EdgeAPI.request_otp",
            return_value=None,
        ),
        patch(
            "homeassistant.components.tami4.config_flow.Tami4EdgeAPI.submit_otp",
            side_effect=side_effect,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PHONE: "+972555555555"},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("otp")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"otp": "123456"},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("otp")
        expect(result["errors"]).to_equal({"base": expected_error})
