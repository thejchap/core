"""Test the Saunum climate platform."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_HVAC_MODE,
    HVACMode,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from ._fixtures import init_integration, mock_saunum_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Force tryke to fully resolve hass before each test."""


@test
async def climate_set_hvac_mode_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    saunum_client: MagicMock = Depends(mock_saunum_client),
    entry: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test calling SET_HVAC_MODE with OFF stops the session."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.saunum_leil", ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )

    saunum_client.async_stop_session.assert_called_once()


@test
async def climate_set_hvac_mode_heat(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    saunum_client: MagicMock = Depends(mock_saunum_client),
    entry: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test calling SET_HVAC_MODE with HEAT starts the session."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.saunum_leil", ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )

    saunum_client.async_start_session.assert_called_once()


@test.skip("requires syrupy snapshot")
async def entities() -> None:
    """Stub for test_entities (port deferred)."""

@test.skip("indirect parametrize - port deferred")
async def climate_service_calls() -> None:
    """Stub for test_climate_service_calls (port deferred)."""

@test.skip("requires translation injection for service errors")
async def hvac_mode_door_open_validation() -> None:
    """Stub for test_hvac_mode_door_open_validation (port deferred)."""

@test.skip("indirect parametrize - port deferred")
async def hvac_actions() -> None:
    """Stub for test_hvac_actions (port deferred)."""

@test.skip("requires syrupy snapshot")
async def temperature_attributes() -> None:
    """Stub for test_temperature_attributes (port deferred)."""

@test.skip("requires freezegun + coordinator refresh")
async def entity_unavailable_on_update_failure() -> None:
    """Stub for test_entity_unavailable_on_update_failure (port deferred)."""

@test.skip("requires translation injection")
async def service_error_handling() -> None:
    """Stub for test_service_error_handling (port deferred)."""

@test.skip("indirect parametrize - port deferred")
async def fan_mode_service_call() -> None:
    """Stub for test_fan_mode_service_call (port deferred)."""

@test.skip("indirect parametrize - port deferred")
async def preset_mode_service_call() -> None:
    """Stub for test_preset_mode_service_call (port deferred)."""

@test.skip("requires syrupy snapshot")
async def fan_mode_attributes() -> None:
    """Stub for test_fan_mode_attributes (port deferred)."""

@test.skip("requires translation injection for service errors")
async def fan_mode_validation_error() -> None:
    """Stub for test_fan_mode_validation_error (port deferred)."""

@test.skip("requires translation injection for service errors")
async def preset_mode_validation_error() -> None:
    """Stub for test_preset_mode_validation_error (port deferred)."""

@test.skip("requires syrupy snapshot")
async def preset_mode_attributes_default_names() -> None:
    """Stub for test_preset_mode_attributes_default_names (port deferred)."""

@test.skip("requires syrupy snapshot")
async def preset_mode_attributes_custom_names() -> None:
    """Stub for test_preset_mode_attributes_custom_names (port deferred)."""

@test.skip("requires options_flow + reload")
async def preset_mode_options_update() -> None:
    """Stub for test_preset_mode_options_update (port deferred)."""

@test.skip("requires translation injection for fan errors")
async def fan_mode_error_handling() -> None:
    """Stub for test_fan_mode_error_handling (port deferred)."""
