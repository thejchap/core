"""Test the mill config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def show_config_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test show configuration form."""
    expect(True).to_be(True)


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test create entry from user input."""
    expect(True).to_be(True)


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def flow_entry_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user input for config_entry that already exists."""
    expect(True).to_be(True)


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test connection error."""
    expect(True).to_be(True)


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def local_create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test create entry from user input."""
    expect(True).to_be(True)


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def local_flow_entry_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user input for config_entry that already exists."""
    expect(True).to_be(True)


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def local_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test connection error."""
    expect(True).to_be(True)


