"""Tests for Glances config flow."""

from unittest.mock import MagicMock

from glances_api.exceptions import (
    GlancesApiAuthorizationError,
    GlancesApiConnectionError,
    GlancesApiNoDataAvailable,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.glances.const import DOMAIN
from homeassistant.const import CONF_NAME, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import glances_setup, mock_api

from . import HA_SENSOR_DATA, MOCK_USER_INPUT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(glances_setup),
    _api: MagicMock = Depends(mock_api),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config entry configured successfully."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("0.0.0.0:61208")
    expect(result["data"]).to_equal(MOCK_USER_INPUT)


@test.cases(
    test.case(
        "auth_error",
        error=GlancesApiAuthorizationError,
        message="invalid_auth",
    ),
    test.case(
        "connection_error",
        error=GlancesApiConnectionError,
        message="cannot_connect",
    ),
    test.case(
        "no_data_available",
        error=GlancesApiNoDataAvailable,
        message="cannot_connect",
    ),
)
async def form_fails(
    error: type[Exception],
    message: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test flow fails when api exception is raised."""
    api.return_value.get_ha_sensor_data.side_effect = error
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": message})


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test host is already configured."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_INPUT
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can reauth."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT)
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            CONF_NAME: "Mock Title",
            CONF_USERNAME: "username",
        }
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "password": "new-password",
        },
    )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")


@test.cases(
    test.case(
        "auth_error",
        error=GlancesApiAuthorizationError,
        message="invalid_auth",
    ),
    test.case(
        "connection_error",
        error=GlancesApiConnectionError,
        message="cannot_connect",
    ),
)
async def reauth_fails(
    error: type[Exception],
    message: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test we can reauth."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT)
    entry.add_to_hass(hass)

    api.return_value.get_ha_sensor_data.side_effect = [error, HA_SENSOR_DATA]
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            CONF_NAME: "Mock Title",
            CONF_USERNAME: "username",
        }
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "password": "new-password",
        },
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": message})

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "password": "new-password",
        },
    )

    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")
