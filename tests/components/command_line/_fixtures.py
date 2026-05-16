"""Tryke fixtures for command_line tests (ported from conftest.py)."""

from typing import Any

from tryke import Depends, fixture

from homeassistant import setup
from homeassistant.components.command_line.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture


@fixture
def get_config() -> dict[str, Any]:
    """Return default minimal configuration.

    Override by depending on a different fixture in individual tests.
    """
    return {
        "command_line": [
            {
                "binary_sensor": {
                    "name": "Test",
                    "command": "echo 1",
                    "payload_on": "1",
                    "payload_off": "0",
                    "command_timeout": 15,
                }
            },
            {
                "cover": {
                    "name": "Test",
                    "command_state": "echo 1",
                    "command_timeout": 15,
                }
            },
            {
                "notify": {
                    "name": "Test",
                    "command": "echo 1",
                    "command_timeout": 15,
                }
            },
            {
                "sensor": {
                    "name": "Test",
                    "command": "echo 5",
                    "unit_of_measurement": "in",
                    "command_timeout": 15,
                }
            },
            {
                "switch": {
                    "name": "Test",
                    "command_state": "echo 1",
                    "command_timeout": 15,
                }
            },
        ]
    }


async def async_load_yaml_integration(
    hass: HomeAssistant, get_config: dict[str, Any]
) -> None:
    """Set up the Command Line integration in Home Assistant."""
    await setup.async_setup_component(hass, DOMAIN, get_config)
    await hass.async_block_till_done()


@fixture
async def load_yaml_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    get_config: dict[str, Any] = Depends(get_config),
) -> None:
    """Set up the Command Line integration in Home Assistant."""
    await async_load_yaml_integration(hass, get_config)
