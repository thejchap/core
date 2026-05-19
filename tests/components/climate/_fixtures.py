"""Tryke fixtures for the climate entity platform tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.climate import (
    DOMAIN,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    SWING_HORIZONTAL_OFF,
    SWING_HORIZONTAL_ON,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import ATTR_TEMPERATURE, Platform, UnitOfTemperature
from homeassistant.core import HomeAssistant

from tests.common import (
    MockConfigEntry,
    MockEntity,
    MockModule,
    mock_config_flow,
    mock_integration,
    mock_platform,
    setup_test_component_platform,
)
from tests.components.common import target_entities
from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_recorder_mock


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
):
    """Set up the recorder for tests that need it."""
    return await setup_recorder_mock(hass)


@fixture
def climate_only() -> Generator[None]:
    """Enable only the climate platform on the demo integration."""
    with patch(
        "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
        [Platform.CLIMATE],
    ):
        yield


@fixture
def enable_labs_preview_features() -> Generator[None]:
    """Enable labs preview features."""
    with patch(
        "homeassistant.components.labs.async_is_preview_feature_enabled",
        return_value=True,
    ):
        yield


@fixture
async def target_climates(
    hass: HomeAssistant = Depends(hass_fixture),
) -> dict[str, list[str]]:
    """Create multiple climate entities associated with different targets."""
    return await target_entities(hass, "climate")

TEST_DOMAIN = "test"


class _MockFlow(ConfigFlow):
    """Test flow."""


class MockClimateEntity(MockEntity, ClimateEntity):
    """Mock Climate device to use in tests."""

    _attr_supported_features = (
        ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.SWING_HORIZONTAL_MODE
    )
    _attr_preset_mode = "home"
    _attr_preset_modes = ["home", "away"]
    _attr_fan_mode = "auto"
    _attr_fan_modes = ["auto", "off"]
    _attr_swing_mode = "auto"
    _attr_swing_modes = ["auto", "off"]
    _attr_swing_horizontal_mode = "on"
    _attr_swing_horizontal_modes = [SWING_HORIZONTAL_ON, SWING_HORIZONTAL_OFF]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature = 20
    _attr_target_temperature_high = 25
    _attr_target_temperature_low = 15

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool mode.

        Need to be one of HVACMode.*.
        """
        return HVACMode.HEAT

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac operation modes.

        Need to be a subset of HVAC_MODES.
        """
        return [HVACMode.OFF, HVACMode.HEAT]

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode."""
        self._attr_preset_mode = preset_mode

    def set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode."""
        self._attr_fan_mode = fan_mode

    def set_swing_mode(self, swing_mode: str) -> None:
        """Set swing mode."""
        self._attr_swing_mode = swing_mode

    def set_swing_horizontal_mode(self, swing_horizontal_mode: str) -> None:
        """Set horizontal swing mode."""
        self._attr_swing_horizontal_mode = swing_horizontal_mode

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        self._attr_hvac_mode = hvac_mode

    def set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            self._attr_target_temperature = kwargs[ATTR_TEMPERATURE]
        if ATTR_TARGET_TEMP_HIGH in kwargs:
            self._attr_target_temperature_high = kwargs[ATTR_TARGET_TEMP_HIGH]
            self._attr_target_temperature_low = kwargs[ATTR_TARGET_TEMP_LOW]


class MockClimateEntityTestMethods(MockClimateEntity):
    """Mock Climate device."""

    def turn_on(self) -> None:
        """Turn on."""

    def turn_off(self) -> None:
        """Turn off."""


async def setup_test_integration(
    hass: HomeAssistant,
    entities: list[ClimateEntity],
) -> MockConfigEntry:
    """Set up a mocked test integration with the climate platform.

    Replacement for the ``register_test_integration`` + ``config_flow_fixture``
    pair from the original pytest conftest. Combines the integration mock,
    config flow registration, and platform entity registration into a single
    helper so per-test entities can be wired without indirect fixtures.
    """
    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    cm = mock_config_flow(TEST_DOMAIN, _MockFlow)
    cm.__enter__()

    config_entry = MockConfigEntry(domain=TEST_DOMAIN)
    config_entry.add_to_hass(hass)

    async def help_async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.CLIMATE]
        )
        return True

    async def help_async_unload_entry(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Unload test config entry."""
        return await hass.config_entries.async_unload_platforms(
            config_entry, [Platform.CLIMATE]
        )

    mock_integration(
        hass,
        MockModule(
            TEST_DOMAIN,
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
    )

    setup_test_component_platform(
        hass,
        DOMAIN,
        entities=entities,
        from_config_entry=True,
    )
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
