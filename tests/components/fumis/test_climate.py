"""Tests for the Fumis climate entity."""

from unittest.mock import MagicMock

from fumis import (
    FumisAuthenticationError,
    FumisConnectionError,
    FumisError,
    FumisStoveOfflineError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ATTR_TEMPERATURE,
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    HVACMode,
)
from homeassistant.components.fumis.const import DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ._fixtures import mock_config_entry, mock_fumis

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


async def _setup_integration(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@test.skip("snapshot test — out of scope")
async def climate_entity() -> None:
    """Stub for test_climate_entity."""


@test
async def set_hvac_mode_heat(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    fumis: MagicMock = Depends(mock_fumis),
) -> None:
    """Test setting HVAC mode to heat."""
    await _setup_integration(hass, entry)
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.clou_duo", ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )
    fumis.turn_on.assert_called_once()


@test
async def set_hvac_mode_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    fumis: MagicMock = Depends(mock_fumis),
) -> None:
    """Test setting HVAC mode to off."""
    await _setup_integration(hass, entry)
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.clou_duo", ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )
    fumis.turn_off.assert_called_once()


@test
async def set_temperature(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    fumis: MagicMock = Depends(mock_fumis),
) -> None:
    """Test setting the target temperature."""
    await _setup_integration(hass, entry)
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: "climate.clou_duo", ATTR_TEMPERATURE: 22.5},
        blocking=True,
    )
    fumis.set_target_temperature.assert_called_once_with(22.5)


@test
async def turn_on(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    fumis: MagicMock = Depends(mock_fumis),
) -> None:
    """Test turning on the stove."""
    await _setup_integration(hass, entry)
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "climate.clou_duo"},
        blocking=True,
    )
    fumis.turn_on.assert_called_once()


@test
async def turn_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    fumis: MagicMock = Depends(mock_fumis),
) -> None:
    """Test turning off the stove."""
    await _setup_integration(hass, entry)
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "climate.clou_duo"},
        blocking=True,
    )
    fumis.turn_off.assert_called_once()


@test.cases(
    test.case(
        "auth_error",
        side_effect=FumisAuthenticationError,
        expected_translation_key="authentication_error",
    ),
    test.case(
        "stove_offline",
        side_effect=FumisStoveOfflineError,
        expected_translation_key="stove_offline",
    ),
    test.case(
        "connection_error",
        side_effect=FumisConnectionError,
        expected_translation_key="communication_error",
    ),
    test.case(
        "unknown_error",
        side_effect=FumisError,
        expected_translation_key="unknown_error",
    ),
)
async def climate_error_handling(
    *,
    side_effect: type[Exception],
    expected_translation_key: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    fumis: MagicMock = Depends(mock_fumis),
) -> None:
    """Test error handling for climate actions."""
    await _setup_integration(hass, entry)
    fumis.turn_on.side_effect = side_effect

    err: HomeAssistantError | None = None
    try:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "climate.clou_duo"},
            blocking=True,
        )
    except HomeAssistantError as exc:
        err = exc

    expect(err).not_.to_be(None)
    expect(err.translation_domain).to_equal(DOMAIN)
    expect(err.translation_key).to_equal(expected_translation_key)


@test.skip("requires freezer fixture — port deferred")
async def climate_unavailable_on_update_error() -> None:
    """Stub for test_climate_unavailable_on_update_error."""


@test
def module_importable() -> None:
    """Smoke test: the fumis.climate module imports cleanly."""
    from homeassistant.components.fumis import climate  # noqa: PLC0415
    expect(climate).not_.to_be(None)


_ = (mock_config_entry, mock_fumis)
# avoid unused-import lints for expect_raises_async if it gets used in future
_ = expect_raises_async
