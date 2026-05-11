"""Test the Saunum climate platform."""

from dataclasses import replace
from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import (
    ATTR_FAN_MODE,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    DOMAIN as CLIMATE_DOMAIN,
    FAN_LOW,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_TEMPERATURE,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant

from ._fixtures import init_integration, mock_config_entry, mock_saunum_client

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

@test.cases(
    test.case(
        "set_hvac_mode_heat",
        service=SERVICE_SET_HVAC_MODE,
        service_data={ATTR_HVAC_MODE: HVACMode.HEAT},
        client_method="async_start_session",
        expected_args=(),
    ),
    test.case(
        "set_hvac_mode_off",
        service=SERVICE_SET_HVAC_MODE,
        service_data={ATTR_HVAC_MODE: HVACMode.OFF},
        client_method="async_stop_session",
        expected_args=(),
    ),
    test.case(
        "set_temperature",
        service=SERVICE_SET_TEMPERATURE,
        service_data={ATTR_TEMPERATURE: 85},
        client_method="async_set_target_temperature",
        expected_args=(85,),
    ),
)
async def climate_service_calls(
    service: str,
    service_data: dict,
    client_method: str,
    expected_args: tuple,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    saunum_client: MagicMock = Depends(mock_saunum_client),
    entry: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test climate service calls."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        service,
        {ATTR_ENTITY_ID: "climate.saunum_leil", **service_data},
        blocking=True,
    )

    getattr(saunum_client, client_method).assert_called_once_with(*expected_args)

@test.skip("requires translation injection for service errors")
async def hvac_mode_door_open_validation() -> None:
    """Stub for test_hvac_mode_door_open_validation (port deferred)."""

@test.cases(
    test.case(
        "heating",
        heater_elements_active=3,
        expected_hvac_action=HVACAction.HEATING,
    ),
    test.case(
        "idle",
        heater_elements_active=0,
        expected_hvac_action=HVACAction.IDLE,
    ),
)
async def hvac_actions(
    heater_elements_active: int,
    expected_hvac_action: HVACAction,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    saunum_client: MagicMock = Depends(mock_saunum_client),
) -> None:
    """Test HVAC actions when session is active."""
    saunum_client.async_get_data.return_value = replace(
        saunum_client.async_get_data.return_value,
        session_active=True,
        heater_elements_active=heater_elements_active,
    )

    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("climate.saunum_leil")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(HVACMode.HEAT)
    expect(state.attributes.get(ATTR_HVAC_ACTION)).to_equal(expected_hvac_action)

@test.skip("requires syrupy snapshot")
async def temperature_attributes() -> None:
    """Stub for test_temperature_attributes (port deferred)."""

@test.skip("requires freezegun + coordinator refresh")
async def entity_unavailable_on_update_failure() -> None:
    """Stub for test_entity_unavailable_on_update_failure (port deferred)."""

@test.skip("requires translation injection")
async def service_error_handling() -> None:
    """Stub for test_service_error_handling (port deferred)."""

@test
async def fan_mode_service_call(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    saunum_client: MagicMock = Depends(mock_saunum_client),
) -> None:
    """Test setting fan mode."""
    saunum_client.async_get_data.return_value = replace(
        saunum_client.async_get_data.return_value, session_active=True
    )

    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_FAN_MODE,
        {ATTR_ENTITY_ID: "climate.saunum_leil", ATTR_FAN_MODE: FAN_LOW},
        blocking=True,
    )

    saunum_client.async_set_fan_speed.assert_called_once_with(1)


@test
async def preset_mode_service_call(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    saunum_client: MagicMock = Depends(mock_saunum_client),
    entry: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test setting preset mode."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: "climate.saunum_leil", ATTR_PRESET_MODE: "type_2"},
        blocking=True,
    )

    saunum_client.async_set_sauna_type.assert_called_once_with(1)

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
