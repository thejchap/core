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
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


# Inject actron_air translations so:
# - HomeAssistantError(translation_key="api_error") formats correctly.
# - Service validation error messages are present.
_FAKE_TRANSLATIONS = {
    "component.actron_air.exceptions.api_error.message": (
        "Failed to communicate with Actron Air device: {error}"
    ),
    "component.actron_air.exceptions.no_temperature.message": (
        "No temperature provided"
    ),
}


async def _fake_get_translations(
    hass_arg, language, category, integrations=None, config_flow=None
):
    if integrations and "actron_air" in integrations:
        return _FAKE_TRANSLATIONS
    return {}


def _fake_get_cached_translations(hass_arg, language, category, integration=None):
    """Return the same fake bundle for cached translation lookups."""
    return _FAKE_TRANSLATIONS


def _fake_get_exception_message(
    translation_domain, translation_key, translation_placeholders=None
):
    """Resolve api_error.message manually since translation cache is empty."""
    key = f"component.{translation_domain}.exceptions.{translation_key}.message"
    message = _FAKE_TRANSLATIONS.get(key, translation_key)
    if translation_placeholders:
        try:
            message = message.format(**translation_placeholders)
        except KeyError:
            pass
    return message


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke to build a per-module HookExecutor for this file."""


def _patch_translations():
    """Patch all four translation lookup paths the integration may hit."""
    return (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_exception_message",
            side_effect=_fake_get_exception_message,
        ),
        patch.dict(
            "homeassistant.exceptions._function_cache",
            {"async_get_exception_message": _fake_get_exception_message},
            clear=False,
        ),
    )


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_entities() -> None:
    """Stub for test_climate_entities (snapshot-based)."""


@test
async def system_set_temperature(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setting temperature for system climate entity."""
    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test API error when setting temperature for system climate entity."""
    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
        await setup_integration(hass, mock_config_entry)

        status = mock_actron_api.state_manager.get_status.return_value
        status.user_aircon_settings.set_temperature.side_effect = ActronAirAPIError(
            "Test error"
        )

        raised: HomeAssistantError | None = None
        try:
            await hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_TEMPERATURE,
                {ATTR_ENTITY_ID: "climate.test_system", ATTR_TEMPERATURE: 22.5},
                blocking=True,
            )
        except HomeAssistantError as err:
            err._message = str(err)  # noqa: SLF001
            raised = err

    expect(raised is not None).to_be(True)
    expect("Test error" in str(raised)).to_be(True)


@test
async def system_set_temperature_missing_temperature(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test validation when temperature is not provided for system entity."""
    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
        await setup_integration(hass, mock_config_entry)

    coordinator = next(
        iter(mock_config_entry.runtime_data.system_coordinators.values())
    )
    entity = ActronSystemClimate(coordinator)
    status = mock_actron_api.state_manager.get_status.return_value

    async with expect_raises_async(ServiceValidationError):
        await entity.async_set_temperature(
            **{ATTR_TARGET_TEMP_HIGH: 24, ATTR_TARGET_TEMP_LOW: 18}
        )

    status.user_aircon_settings.set_temperature.assert_not_awaited()


@test
async def system_set_fan_mode(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setting fan mode for system climate entity."""
    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test API error when setting fan mode for system climate entity."""
    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
        await setup_integration(hass, mock_config_entry)

        status = mock_actron_api.state_manager.get_status.return_value
        status.user_aircon_settings.set_fan_mode.side_effect = ActronAirAPIError(
            "Test error"
        )

        raised: HomeAssistantError | None = None
        try:
            await hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_FAN_MODE,
                {ATTR_ENTITY_ID: "climate.test_system", ATTR_FAN_MODE: "high"},
                blocking=True,
            )
        except HomeAssistantError as err:
            err._message = str(err)  # noqa: SLF001
            raised = err

    expect(raised is not None).to_be(True)
    expect("Test error" in str(raised)).to_be(True)


@test
async def system_set_hvac_mode(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setting HVAC mode for system climate entity."""
    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test API error when setting HVAC mode for system climate entity."""
    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
        await setup_integration(hass, mock_config_entry)

        status = mock_actron_api.state_manager.get_status.return_value
        status.ac_system.set_system_mode.side_effect = ActronAirAPIError("Test error")

        raised: HomeAssistantError | None = None
        try:
            await hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_HVAC_MODE,
                {ATTR_ENTITY_ID: "climate.test_system", ATTR_HVAC_MODE: HVACMode.HEAT},
                blocking=True,
            )
        except HomeAssistantError as err:
            err._message = str(err)  # noqa: SLF001
            raised = err

    expect(raised is not None).to_be(True)
    expect("Test error" in str(raised)).to_be(True)


@test
async def zone_set_temperature(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(init_integration_with_zone),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test setting temperature for zone climate entity."""
    p1, p2, p3, p4 = _patch_translations()
    with p1, p2, p3, p4:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: "climate.living_room", ATTR_TEMPERATURE: 23.0},
            blocking=True,
        )

    mock_zone.set_temperature.assert_awaited_once_with(temperature=23.0)


@test
async def zone_set_temperature_api_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(init_integration_with_zone),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test API error when setting temperature for zone climate entity."""
    mock_zone.set_temperature.side_effect = ActronAirAPIError("Test error")

    p1, p2, p3, p4 = _patch_translations()
    raised: HomeAssistantError | None = None
    with p1, p2, p3, p4:
        try:
            await hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_TEMPERATURE,
                {ATTR_ENTITY_ID: "climate.living_room", ATTR_TEMPERATURE: 23.0},
                blocking=True,
            )
        except HomeAssistantError as err:
            err._message = str(err)  # noqa: SLF001
            raised = err

    expect(raised is not None).to_be(True)
    expect("Test error" in str(raised)).to_be(True)


@test
async def zone_set_temperature_missing_temperature(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(init_integration_with_zone),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test validation when temperature is not provided for zone entity."""
    coordinator = next(
        iter(mock_config_entry.runtime_data.system_coordinators.values())
    )
    entity = ActronZoneClimate(coordinator, mock_zone)

    async with expect_raises_async(ServiceValidationError):
        await entity.async_set_temperature(
            **{ATTR_TARGET_TEMP_HIGH: 24, ATTR_TARGET_TEMP_LOW: 18}
        )

    mock_zone.set_temperature.assert_not_awaited()


@test
async def zone_set_hvac_mode_on(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(init_integration_with_zone),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test setting HVAC mode to on for zone climate entity."""
    mock_zone.is_active = False
    mock_zone.hvac_mode = "OFF"

    p1, p2, p3, p4 = _patch_translations()
    with p1, p2, p3, p4:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.living_room", ATTR_HVAC_MODE: HVACMode.COOL},
            blocking=True,
        )

    mock_zone.enable.assert_awaited_once_with(True)


@test
async def zone_set_hvac_mode_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(init_integration_with_zone),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test setting HVAC mode to off for zone climate entity."""
    p1, p2, p3, p4 = _patch_translations()
    with p1, p2, p3, p4:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.living_room", ATTR_HVAC_MODE: HVACMode.OFF},
            blocking=True,
        )

    mock_zone.enable.assert_awaited_once_with(False)


@test
async def zone_set_hvac_mode_api_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(init_integration_with_zone),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test API error when setting HVAC mode for zone climate entity."""
    mock_zone.enable.side_effect = ActronAirAPIError("Test error")

    p1, p2, p3, p4 = _patch_translations()
    raised: HomeAssistantError | None = None
    with p1, p2, p3, p4:
        try:
            await hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_HVAC_MODE,
                {ATTR_ENTITY_ID: "climate.living_room", ATTR_HVAC_MODE: HVACMode.OFF},
                blocking=True,
            )
        except HomeAssistantError as err:
            err._message = str(err)  # noqa: SLF001
            raised = err

    expect(raised is not None).to_be(True)
    expect("Test error" in str(raised)).to_be(True)


@test
async def system_hvac_mode_unmapped(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test system climate entity returns None for unmapped HVAC mode."""
    status = mock_actron_api.state_manager.get_status.return_value
    status.user_aircon_settings.is_on = True
    status.user_aircon_settings.mode = "UNKNOWN_MODE"

    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
        await setup_integration(hass, mock_config_entry)

    state = hass.states.get("climate.test_system")
    expect(state.state).to_equal("unknown")


@test
async def zone_hvac_mode_unmapped(
    _trigger: None = Depends(_trigger_executor),
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

    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
        await setup_integration(hass, mock_config_entry)

    state = hass.states.get("climate.living_room")
    expect(state.state).to_equal("unknown")


@test
async def zone_hvac_mode_inactive(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test zone climate entity returns OFF when zone is inactive."""
    mock_zone.is_active = False

    status = mock_actron_api.state_manager.get_status.return_value
    status.remote_zone_info = [mock_zone]

    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
        await setup_integration(hass, mock_config_entry)

    state = hass.states.get("climate.living_room")
    expect(state.state).to_equal("off")


@test
async def system_hvac_modes_default(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test system reports correct HVAC modes when DRY is not supported."""
    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test system reports DRY HVAC mode when hardware supports it."""
    status = mock_actron_api.state_manager.get_status.return_value
    status.user_aircon_settings.mode_support = ActronAirModeSupport(
        Cool=True, Heat=True, Fan=True, Auto=True, Dry=True
    )

    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test system falls back to default modes when ModeSupport is absent."""
    status = mock_actron_api.state_manager.get_status.return_value
    status.user_aircon_settings.mode_support = None

    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
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
    _trigger: None = Depends(_trigger_executor),
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

    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_zone: MagicMock = Depends(mock_zone),
) -> None:
    """Test zone falls back to default modes when ModeSupport is absent."""
    status = mock_actron_api.state_manager.get_status.return_value
    status.user_aircon_settings.mode_support = None
    status.remote_zone_info = [mock_zone]

    p1, p2, p3, p4 = _patch_translations()
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]), p1, p2, p3, p4:
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
