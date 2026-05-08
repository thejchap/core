"""Tests for the diagnostics data provided by the Nut integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.components.nut.diagnostics import TO_REDACT
from homeassistant.core import HomeAssistant

from .util import async_init_integration

from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def diagnostics(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test diagnostics."""
    list_commands: set[str] = ["beeper.enable"]
    list_commands_return_value = {
        supported_command: supported_command for supported_command in list_commands
    }

    mock_config_entry = await async_init_integration(
        hass,
        username="someuser",
        password="somepassword",
        list_vars={"ups.status": "OL"},
        list_ups={"ups1": "UPS 1"},
        list_commands_return_value=list_commands_return_value,
    )

    entry_dict = async_redact_data(mock_config_entry.as_dict(), TO_REDACT)
    nut_data_dict = {
        "ups_list": {"ups1": "UPS 1"},
        "status": {"ups.status": "OL"},
        "commands": list_commands,
    }

    result = await get_diagnostics_for_config_entry(
        hass, hass_client, mock_config_entry
    )
    expect(result["entry"]).to_equal(entry_dict | {"discovery_keys": {}})
    expect(result["nut_data"]).to_equal(nut_data_dict)
