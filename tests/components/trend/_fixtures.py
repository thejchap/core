"""Tryke fixtures for the trend component tests."""

from collections.abc import Awaitable, Callable
from typing import Any

from tryke import Depends, fixture

from homeassistant.components.trend.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

type ComponentSetup = Callable[[dict[str, Any]], Awaitable[None]]


@fixture
def config_entry() -> MockConfigEntry:
    """Return a MockConfigEntry for testing."""
    return MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My trend",
            "entity_id": "sensor.cpu_temp",
            "invert": False,
            "max_samples": 2.0,
            "min_gradient": 0.0,
            "sample_duration": 0.0,
        },
        title="My trend",
    )


@fixture
async def setup_component(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> ComponentSetup:
    """Set up the trend component."""

    async def _setup_func(component_params: dict[str, Any]) -> None:
        config_entry.add_to_hass(hass)
        hass.config_entries.async_update_entry(
            config_entry,
            options={
                **config_entry.options,
                **component_params,
                "name": "test_trend_sensor",
                "entity_id": "sensor.test_state",
            },
            title="test_trend_sensor",
        )
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    return _setup_func
