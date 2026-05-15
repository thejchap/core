"""Tryke fixtures for the device_sun_light_trigger tests."""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components import device_tracker, light
from homeassistant.const import CONF_PLATFORM, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import setup_test_component_platform
from tests.components.device_tracker.common import (
    MockScanner,
    mock_legacy_device_tracker_setup,
)
from tests.components.light.common import MockLight
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_light_entities() -> list[MockLight]:
    """Return mocked light entities."""
    return [
        MockLight("Ceiling", STATE_ON),
        MockLight("Ceiling", STATE_OFF),
        MockLight(None, STATE_OFF),
    ]


@fixture
def mock_legacy_device_scanner() -> MockScanner:
    """Return mocked legacy device scanner entity."""
    return MockScanner()


@fixture
def mock_legacy_device_tracker_setup_fixture() -> (
    Callable[[HomeAssistant, MockScanner], None]
):
    """Return setup callable for legacy device tracker setup."""
    return mock_legacy_device_tracker_setup


@fixture
async def scanner(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_light_entities: list[MockLight] = Depends(mock_light_entities),
    mock_legacy_device_scanner: MockScanner = Depends(mock_legacy_device_scanner),
    mock_legacy_device_tracker_setup_fn: Callable[
        [HomeAssistant, MockScanner], None
    ] = Depends(mock_legacy_device_tracker_setup_fixture),
) -> None:
    """Initialize components."""
    mock_legacy_device_tracker_setup_fn(hass, mock_legacy_device_scanner)
    mock_legacy_device_scanner.reset()
    mock_legacy_device_scanner.come_home("DEV1")

    setup_test_component_platform(hass, "light", mock_light_entities)

    with patch(
        "homeassistant.components.device_tracker.legacy.load_yaml_config_file",
        return_value={
            "device_1": {
                "mac": "DEV1",
                "name": "Unnamed Device",
                "picture": "http://example.com/dev1.jpg",
                "track": True,
                "vendor": None,
            },
            "device_2": {
                "mac": "DEV2",
                "name": "Unnamed Device",
                "picture": "http://example.com/dev2.jpg",
                "track": True,
                "vendor": None,
            },
        },
    ):
        await async_setup_component(
            hass,
            device_tracker.DOMAIN,
            {device_tracker.DOMAIN: {CONF_PLATFORM: "test"}},
        )

    await async_setup_component(
        hass, light.DOMAIN, {light.DOMAIN: {CONF_PLATFORM: "test"}}
    )
    await hass.async_block_till_done()
