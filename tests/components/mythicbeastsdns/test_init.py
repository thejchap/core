"""Test the Mythic Beasts DNS component."""

import logging
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import mythicbeastsdns
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass, mock_network

_LOGGER = logging.getLogger(__name__)


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


async def mbddns_update_mock(domain, password, host, ttl=60, session=None):
    """Mock out mythic beasts updater."""
    if password == "incorrect":
        _LOGGER.error("Updating Mythic Beasts failed: Not authenticated")
        return False
    if host[0] == "$":
        _LOGGER.error("Updating Mythic Beasts failed: Invalid Character")
        return False
    return True


@test
async def update(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Run with correct values and check true is returned."""
    with patch("mbddns.update", new=mbddns_update_mock):
        result = await async_setup_component(
            hass,
            mythicbeastsdns.DOMAIN,
            {
                mythicbeastsdns.DOMAIN: {
                    "domain": "example.org",
                    "password": "correct",
                    "host": "hass",
                }
            },
        )
        expect(result).to_be(True)


@test
async def update_fails_if_wrong_token(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Run with incorrect token and check false is returned."""
    with patch("mbddns.update", new=mbddns_update_mock):
        result = await async_setup_component(
            hass,
            mythicbeastsdns.DOMAIN,
            {
                mythicbeastsdns.DOMAIN: {
                    "domain": "example.org",
                    "password": "incorrect",
                    "host": "hass",
                }
            },
        )
        expect(result).to_be(False)


@test
async def update_fails_if_invalid_host(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Run with invalid characters in host and check false is returned."""
    with patch("mbddns.update", new=mbddns_update_mock):
        result = await async_setup_component(
            hass,
            mythicbeastsdns.DOMAIN,
            {
                mythicbeastsdns.DOMAIN: {
                    "domain": "example.org",
                    "password": "correct",
                    "host": "$hass",
                }
            },
        )
        expect(result).to_be(False)
