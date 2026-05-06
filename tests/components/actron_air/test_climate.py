"""Tests for the Actron Air climate platform."""

from unittest.mock import MagicMock, patch

from actron_neo_api import ActronAirAPIError
from actron_neo_api.models.settings import ActronAirModeSupport
from tryke import Depends, expect, fixture, test

from homeassistant.components.actron_air.climate import (
    ActronSystemClimate,
    ActronZoneClimate,
)
from homeassistant.components.climate import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE,
    HVACMode,
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from . import setup_integration
from ._fixtures import (
    init_integration_with_zone,
    mock_actron_api,
    mock_config_entry,
    mock_zone,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


async def _expect_raises_async(
    coro_factory, exc_type: type[BaseException], match: str | None = None
) -> None:
    """Async-safe version of expect(...).to_raise() preserving regex match."""
    import re  # noqa: PLC0415

    raised: BaseException | None = None
    try:
        await coro_factory()
    except BaseException as exc:  # noqa: BLE001 - test assertion
        raised = exc
    expect(raised).not_.to_be(None)
    expect(isinstance(raised, exc_type)).to_be_truthy()
    if match is not None:
        candidates = (
            str(raised),
            *(str(a) for a in getattr(raised, "args", ())),
        )
        expect(bool(re.search(match, " ".join(candidates)))).to_be_truthy()


@test.skip("uses syrupy snapshot")
async def climate_entities() -> None:
    """Test climate entities (snapshot platform)."""


@test
async def system_set_temperature(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setting temperature for system climate entity."""
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    status = mock_actron_api.state_manager.get_status.return_value

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: "climate.test_system", ATTR_TEMPERATURE: 22.5},
        blocking=True,
    )

    status.user_aircon_settings.set_temperature.assert_awaited_once_with(
        temperature=22.5
    )


@test
async def system_set_temperature_api_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test API error when setting temperature for system climate entity."""
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    status = mock_actron_api.state_manager.get_status.return_value
    status.user_aircon_settings.set_temperature.side_effect = ActronAirAPIError(
        "Test error"
    )

    async def call() -> None:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: "climate.test_system", ATTR_TEMPERATURE: 22.5},
            blocking=True,
        )

    await _expect_raises_async(call, HomeAssistantError, match="Test error")


@test
async def system_set_temperature_missing_temperature(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test validation when temperature is not provided for system entity."""
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    coordinator = next(
        iter(mock_config_entry.runtime_data.system_coordinators.values())
    )
    entity = ActronSystemClimate(coordinator)
    status = mock_actron_api.state_manager.get_status.return_value

    async def call() -> None:
        await entity.async_set_temperature(
            **{ATTR_TARGET_TEMP_HIGH: 24, ATTR_TARGET_TEMP_LOW: 18}
        )

    await _expect_raises_async(call, ServiceValidationError)

    status.user_aircon_settings.set_temperature.assert_not_awaited()


@test
async def system_set_fan_mode(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setting fan mode for system climate entity."""
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    status = mock_actron_api.state_manager.get_status.return_value

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_FAN_MODE,
        {ATTR_ENTITY_ID: "climate.test_system", ATTR_FAN_MODE: "low"},
        blocking=True,
    )

    status.user_aircon_settings.set_fan_mode.assert_awaited_once_with("LOW")


@test
async def system_set_fan_mode_api_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test API error when setting fan mode for system climate entity."""
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    status = mock_actron_api.state_manager.get_status.return_value
    status.user_aircon_settings.set_fan_mode.side_effect = ActronAirAPIError(
        "Test error"
    )

    async def call() -> None:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: "climate.test_system", ATTR_FAN_MODE: "high"},
            blocking=True,
        )

    await _expect_raises_async(call, HomeAssistantError, match="Test error")


@test
async def system_set_hvac_mode(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setting HVAC mode for system climate entity."""
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    status = mock_actron_api.state_manager.get_status.return_value

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.test_system", ATTR_HVAC_MODE: HVACMode.COOL},
        blocking=True,
    )

    status.ac_system.set_system_mode.assert_awaited_once_with("COOL")


@test
async def system_set_hvac_mode_api_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test API error when setting HVAC mode for system climate entity."""
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    status = mock_actron_api.state_manager.get_status.return_value
    status.ac_system.set_system_mode.side_effect = ActronAirAPIError("Test error")

    async def call() -> None:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.test_system", ATTR_HVAC_MODE: HVACMode.HEAT},
            blocking=True,
        )

    await _expect_raises_async(call, HomeAssistantError, match="Test error")


@test
async def zone_set_temperature(
    _setup: None = Depends(init_integration_with_zone),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test setting temperature for zone climate entity."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: "climate.living_room", ATTR_TEMPERATURE: 23.0},
        blocking=True,
    )

    mock_zone.set_temperature.assert_awaited_once_with(temperature=23.0)


@test
async def zone_set_temperature_api_error(
    _setup: None = Depends(init_integration_with_zone),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test API error when setting temperature for zone climate entity."""
    mock_zone.set_temperature.side_effect = ActronAirAPIError("Test error")

    async def call() -> None:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: "climate.living_room", ATTR_TEMPERATURE: 23.0},
            blocking=True,
        )

    await _expect_raises_async(call, HomeAssistantError, match="Test error")


@test
async def zone_set_temperature_missing_temperature(
    _setup: None = Depends(init_integration_with_zone),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test validation when temperature is not provided for zone entity."""
    coordinator = next(
        iter(mock_config_entry.runtime_data.system_coordinators.values())
    )
    entity = ActronZoneClimate(coordinator, mock_zone)

    async def call() -> None:
        await entity.async_set_temperature(
            **{ATTR_TARGET_TEMP_HIGH: 24, ATTR_TARGET_TEMP_LOW: 18}
        )

    await _expect_raises_async(call, ServiceValidationError)

    mock_zone.set_temperature.assert_not_awaited()


@test
async def zone_set_hvac_mode_on(
    _setup: None = Depends(init_integration_with_zone),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test setting HVAC mode to on for zone climate entity."""
    mock_zone.is_active = False
    mock_zone.hvac_mode = "OFF"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.living_room", ATTR_HVAC_MODE: HVACMode.COOL},
        blocking=True,
    )

    mock_zone.enable.assert_awaited_once_with(True)


@test
async def zone_set_hvac_mode_off(
    _setup: None = Depends(init_integration_with_zone),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test setting HVAC mode to off for zone climate entity."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.living_room", ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )

    mock_zone.enable.assert_awaited_once_with(False)


@test
async def zone_set_hvac_mode_api_error(
    _setup: None = Depends(init_integration_with_zone),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test API error when setting HVAC mode for zone climate entity."""
    mock_zone.enable.side_effect = ActronAirAPIError("Test error")

    async def call() -> None:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.living_room", ATTR_HVAC_MODE: HVACMode.OFF},
            blocking=True,
        )

    await _expect_raises_async(call, HomeAssistantError, match="Test error")


@test
async def system_hvac_mode_unmapped(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test system climate entity returns None for unmapped HVAC mode."""
    status = mock_actron_api.state_manager.get_status.return_value
    status.user_aircon_settings.is_on = True
    status.user_aircon_settings.mode = "UNKNOWN_MODE"

    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    state = hass.states.get("climate.test_system")
    expect(state.state).to_equal("unknown")


@test
async def zone_hvac_mode_unmapped(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test zone climate entity returns None for unmapped HVAC mode."""
    mock_zone.is_active = True
    mock_zone.hvac_mode = "UNKNOWN_MODE"

    status = mock_actron_api.state_manager.get_status.return_value
    status.remote_zone_info = [mock_zone]

    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    state = hass.states.get("climate.living_room")
    expect(state.state).to_equal("unknown")


@test
async def zone_hvac_mode_inactive(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test zone climate entity returns OFF when zone is inactive."""
    mock_zone.is_active = False

    status = mock_actron_api.state_manager.get_status.return_value
    status.remote_zone_info = [mock_zone]

    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    state = hass.states.get("climate.living_room")
    expect(state.state).to_equal("off")


@test
async def system_hvac_modes_default(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test system reports correct HVAC modes when DRY is not supported."""
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    state = hass.states.get("climate.test_system")
    expect(state.attributes["hvac_modes"]).to_equal(
        [
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.FAN_ONLY,
            HVACMode.AUTO,
            HVACMode.OFF,
        ]
    )


@test
async def system_hvac_modes_with_dry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test system reports DRY HVAC mode when hardware supports it."""
    status = mock_actron_api.state_manager.get_status.return_value
    status.user_aircon_settings.mode_support = ActronAirModeSupport(
        Cool=True, Heat=True, Fan=True, Auto=True, Dry=True
    )

    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    state = hass.states.get("climate.test_system")
    expect(state.attributes["hvac_modes"]).to_equal(
        [
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.FAN_ONLY,
            HVACMode.AUTO,
            HVACMode.DRY,
            HVACMode.OFF,
        ]
    )


@test
async def system_hvac_modes_no_mode_support(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test system falls back to default modes when ModeSupport is absent."""
    status = mock_actron_api.state_manager.get_status.return_value
    status.user_aircon_settings.mode_support = None

    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    state = hass.states.get("climate.test_system")
    expect(state.attributes["hvac_modes"]).to_equal(
        [
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.FAN_ONLY,
            HVACMode.AUTO,
            HVACMode.OFF,
        ]
    )


@test
async def zone_hvac_modes_with_dry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test zone reports DRY HVAC mode when hardware supports it."""
    status = mock_actron_api.state_manager.get_status.return_value
    status.user_aircon_settings.mode_support = ActronAirModeSupport(
        Cool=True, Heat=True, Fan=True, Auto=True, Dry=True
    )
    status.remote_zone_info = [mock_zone]

    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    state = hass.states.get("climate.living_room")
    expect(state.attributes["hvac_modes"]).to_equal(
        [
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.FAN_ONLY,
            HVACMode.AUTO,
            HVACMode.DRY,
            HVACMode.OFF,
        ]
    )


@test
async def zone_hvac_modes_no_mode_support(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test zone falls back to default modes when ModeSupport is absent."""
    status = mock_actron_api.state_manager.get_status.return_value
    status.user_aircon_settings.mode_support = None
    status.remote_zone_info = [mock_zone]

    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    state = hass.states.get("climate.living_room")
    expect(state.attributes["hvac_modes"]).to_equal(
        [
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.FAN_ONLY,
            HVACMode.AUTO,
            HVACMode.OFF,
        ]
    )
