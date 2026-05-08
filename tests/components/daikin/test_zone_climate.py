"""Tests for Daikin zone climate entities."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import (
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODES,
    ATTR_MAX_TEMP,
    ATTR_MIN_TEMP,
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE,
    HVACAction,
    HVACMode,
)
from homeassistant.components.daikin.const import DOMAIN, KEY_MAC
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    CONF_HOST,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_component import async_update_entity

from ._fixtures import (
    ZoneDevice,
    configure_zone_device,
    zone_device as zone_device_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async

HOST = "127.0.0.1"


_FAKE_TRANSLATIONS: dict[str, str] = {}


async def _fake_get_translations(
    hass_arg, language, category, integrations=None, config_flow=None
):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass_arg, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
) -> AsyncGenerator[HomeAssistant]:
    with (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        yield hass


async def _async_setup_daikin(
    hass: HomeAssistant, zone_device: ZoneDevice
) -> MockConfigEntry:
    """Set up a Daikin config entry with a mocked library device."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=zone_device.mac,
        data={CONF_HOST: HOST, KEY_MAC: zone_device.mac},
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    return config_entry


def _zone_entity_id(
    entity_registry: er.EntityRegistry, zone_device: ZoneDevice, zone_id: int
) -> str | None:
    """Return the entity id for a zone climate unique id."""
    return entity_registry.async_get_entity_id(
        CLIMATE_DOMAIN,
        DOMAIN,
        f"{zone_device.mac}-zone{zone_id}-temperature",
    )


async def _async_set_zone_temperature(
    hass: HomeAssistant, entity_id: str, temperature: float
) -> None:
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: temperature},
        blocking=True,
    )


@test
async def setup_entry_adds_zone_climates(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """Configured zones create zone climate entities."""
    configure_zone_device(
        zone_device, zones=[["-", "0", 0], ["Living", "1", 22], ["Office", "1", 21]]
    )
    await _async_setup_daikin(hass, zone_device)

    expect(_zone_entity_id(entity_registry, zone_device, 0)).to_be(None)
    expect(_zone_entity_id(entity_registry, zone_device, 1) is not None).to_be(True)
    expect(_zone_entity_id(entity_registry, zone_device, 2) is not None).to_be(True)


@test
async def setup_entry_skips_zone_climates_without_support(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """Missing zone temperature lists skip zone climate entities."""
    configure_zone_device(zone_device, zones=[["Living", "1", 22]])
    zone_device.values["lztemp_h"] = ""
    zone_device.values["lztemp_c"] = ""

    await _async_setup_daikin(hass, zone_device)

    expect(_zone_entity_id(entity_registry, zone_device, 0)).to_be(None)


@test
async def setup_entry_handles_missing_zone_temperature_key(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """Missing zone temperature keys do not break climate setup."""
    configure_zone_device(zone_device, zones=[["Living", "1", 22]])
    zone_device.values.pop("lztemp_h")

    await _async_setup_daikin(hass, zone_device)

    expect(_zone_entity_id(entity_registry, zone_device, 0)).to_be(None)
    main_entity_id = entity_registry.async_get_entity_id(
        CLIMATE_DOMAIN,
        DOMAIN,
        zone_device.mac,
    )
    expect(main_entity_id is not None).to_be(True)
    expect(hass.states.get(main_entity_id) is not None).to_be(True)


@test.cases(
    test.case("hot", mode="hot", expected_zone_key="lztemp_h"),
    test.case("cool", mode="cool", expected_zone_key="lztemp_c"),
)
async def zone_climate_sets_temperature_for_active_mode(
    *,
    mode: str,
    expected_zone_key: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """Setting temperature updates the active mode zone value."""
    configure_zone_device(
        zone_device,
        zones=[["Living", "1", 22], ["Office", "1", 21]],
        mode=mode,
    )
    await _async_setup_daikin(hass, zone_device)
    entity_id = _zone_entity_id(entity_registry, zone_device, 0)
    expect(entity_id is not None).to_be(True)

    await _async_set_zone_temperature(hass, entity_id, 23)

    zone_device.set_zone.assert_awaited_once_with(0, expected_zone_key, "23")


@test
async def zone_climate_rejects_out_of_range_temperature(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """Service validation rejects values outside the allowed range."""
    configure_zone_device(
        zone_device, zones=[["Living", "1", 22]], target_temperature=22
    )
    await _async_setup_daikin(hass, zone_device)
    entity_id = _zone_entity_id(entity_registry, zone_device, 0)
    expect(entity_id is not None).to_be(True)

    async with expect_raises_async(ServiceValidationError):
        await _async_set_zone_temperature(hass, entity_id, 30)


@test
async def zone_climate_unavailable_without_target_temperature(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """Zones are unavailable if system target temperature is missing."""
    configure_zone_device(
        zone_device, zones=[["Living", "1", 22]], target_temperature=None
    )
    await _async_setup_daikin(hass, zone_device)
    entity_id = _zone_entity_id(entity_registry, zone_device, 0)
    expect(entity_id is not None).to_be(True)

    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNAVAILABLE)


@test
async def zone_climate_zone_inactive_after_setup(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """Inactive zones raise a translated error during service calls."""
    configure_zone_device(zone_device, zones=[["Living", "1", 22]])
    await _async_setup_daikin(hass, zone_device)
    entity_id = _zone_entity_id(entity_registry, zone_device, 0)
    expect(entity_id is not None).to_be(True)
    zone_device.zones[0][0] = "-"

    async with expect_raises_async(HomeAssistantError):
        await _async_set_zone_temperature(hass, entity_id, 21)


@test
async def zone_climate_zone_missing_after_setup(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """Missing zones raise a translated error during service calls."""
    configure_zone_device(
        zone_device, zones=[["Living", "1", 22], ["Office", "1", 22]]
    )
    await _async_setup_daikin(hass, zone_device)
    entity_id = _zone_entity_id(entity_registry, zone_device, 1)
    expect(entity_id is not None).to_be(True)
    zone_device.zones = [["Living", "1", 22]]

    async with expect_raises_async(HomeAssistantError):
        await _async_set_zone_temperature(hass, entity_id, 21)


@test
async def zone_climate_parameters_unavailable(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """Missing zone parameter lists make the zone entity unavailable."""
    configure_zone_device(zone_device, zones=[["Living", "1", 22]])
    await _async_setup_daikin(hass, zone_device)
    entity_id = _zone_entity_id(entity_registry, zone_device, 0)
    expect(entity_id is not None).to_be(True)
    zone_device.values["lztemp_h"] = ""
    zone_device.values["lztemp_c"] = ""

    await async_update_entity(hass, entity_id)
    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNAVAILABLE)


@test
async def zone_climate_hvac_modes_read_only(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """Changing HVAC mode through a zone climate is blocked."""
    configure_zone_device(zone_device, zones=[["Living", "1", 22]])
    await _async_setup_daikin(hass, zone_device)
    entity_id = _zone_entity_id(entity_registry, zone_device, 0)
    expect(entity_id is not None).to_be(True)

    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: entity_id, "hvac_mode": HVACMode.HEAT},
            blocking=True,
        )


@test
async def zone_climate_set_temperature_requires_heat_or_cool(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """Setting temperature in unsupported modes raises a translated error."""
    configure_zone_device(zone_device, zones=[["Living", "1", 22]], mode="auto")
    await _async_setup_daikin(hass, zone_device)
    entity_id = _zone_entity_id(entity_registry, zone_device, 0)
    expect(entity_id is not None).to_be(True)

    async with expect_raises_async(HomeAssistantError):
        await _async_set_zone_temperature(hass, entity_id, 21)


@test
async def zone_climate_properties(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """Zone climate exposes expected state attributes."""
    configure_zone_device(
        zone_device,
        zones=[["Living", "1", 22]],
        target_temperature=24,
        mode="cool",
        heating_values="20",
        cooling_values="18",
    )
    await _async_setup_daikin(hass, zone_device)
    entity_id = _zone_entity_id(entity_registry, zone_device, 0)
    expect(entity_id is not None).to_be(True)

    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(HVACMode.COOL)
    expect(state.attributes[ATTR_HVAC_ACTION]).to_equal(HVACAction.COOLING)
    expect(state.attributes[ATTR_TEMPERATURE]).to_equal(18.0)
    expect(state.attributes[ATTR_MIN_TEMP]).to_equal(22.0)
    expect(state.attributes[ATTR_MAX_TEMP]).to_equal(26.0)
    expect(state.attributes[ATTR_HVAC_MODES]).to_equal([HVACMode.COOL])
    expect(state.attributes["zone_id"]).to_equal(0)


@test
async def zone_climate_target_temperature_inactive_mode(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """In non-heating/cooling modes, zone target temperature is None."""
    configure_zone_device(
        zone_device,
        zones=[["Living", "1", 22]],
        mode="auto",
        heating_values="bad",
        cooling_values="19",
    )
    await _async_setup_daikin(hass, zone_device)
    entity_id = _zone_entity_id(entity_registry, zone_device, 0)
    expect(entity_id is not None).to_be(True)

    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(HVACMode.HEAT_COOL)
    expect(state.attributes[ATTR_TEMPERATURE]).to_be(None)


@test
async def zone_climate_set_zone_failed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    zone_device: ZoneDevice = Depends(zone_device_fixture),
) -> None:
    """Service call surfaces backend zone update errors."""
    configure_zone_device(zone_device, zones=[["Living", "1", 22]])
    await _async_setup_daikin(hass, zone_device)
    entity_id = _zone_entity_id(entity_registry, zone_device, 0)
    expect(entity_id is not None).to_be(True)
    zone_device.set_zone = AsyncMock(side_effect=NotImplementedError)

    async with expect_raises_async(HomeAssistantError):
        await _async_set_zone_temperature(hass, entity_id, 21)
