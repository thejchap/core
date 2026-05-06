"""Test Dremel 3D Printer config flow."""

from unittest.mock import patch

from requests.exceptions import ConnectTimeout
from tryke import Depends, expect, fixture, test

from homeassistant.components.dremel_3d_printer.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    CONF_DATA,
    config_entry,
    connection,
    patch_async_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK = "homeassistant.components.dremel_3d_printer.config_flow.Dremel3DPrinter"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _connection: None = Depends(connection),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch_async_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONF_DATA
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("DREMEL 3D45")
    expect(result["data"]).to_equal(CONF_DATA)


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _connection: None = Depends(connection),
    _entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test we abort if the device is already configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=CONF_DATA
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _connection: None = Depends(connection),
) -> None:
    """Test we show user form on connection error."""
    with patch(MOCK, side_effect=ConnectTimeout):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=CONF_DATA
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch_async_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONF_DATA
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(CONF_DATA)


@test
async def unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _connection: None = Depends(connection),
) -> None:
    """Test we show user form on unknown error."""
    with patch(MOCK, side_effect=Exception):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=CONF_DATA
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "unknown"})

    with patch_async_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONF_DATA
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("DREMEL 3D45")
    expect(result["data"]).to_equal(CONF_DATA)
