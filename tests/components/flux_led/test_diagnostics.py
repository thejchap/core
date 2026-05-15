"""Test flux_led diagnostics."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.flux_led.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import (
    _mock_config_entry_for_bulb,
    _mocked_bulb,
    _patch_discovery,
    _patch_wifibulb,
)

from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def diagnostics(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test generating diagnostics for a config entry."""
    entry = _mock_config_entry_for_bulb(hass)
    bulb = _mocked_bulb()
    with _patch_discovery(), _patch_wifibulb(device=bulb):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
        await hass.async_block_till_done()
    diag = await get_diagnostics_for_config_entry(hass, hass_client, entry)
    expect(diag).to_equal(
        {
            "data": {"mock_diag": "mock_diag"},
            "entry": {
                "data": {
                    "host": "127.0.0.1",
                    "minor_version": 4,
                    "model": "AK001-ZJ2149",
                    "model_description": "Bulb RGBCW",
                    "model_info": "AK001-ZJ2149",
                    "model_num": 53,
                    "name": "Bulb RGBCW DDEEFF",
                    "remote_access_enabled": True,
                    "remote_access_host": "the.cloud",
                    "remote_access_port": 8816,
                },
                "title": "Mock Title",
            },
        }
    )
