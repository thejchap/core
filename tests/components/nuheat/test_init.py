"""NuHeat component tests."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.nuheat.const import DOMAIN
from homeassistant.core import HomeAssistant

from .mocks import MOCK_CONFIG_ENTRY, _get_mock_nuheat

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

VALID_CONFIG = {
    "nuheat": {"username": "warm", "password": "feet", "devices": "thermostat123"}
}
INVALID_CONFIG = {"nuheat": {"username": "warm", "password": "feet"}}


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def init_success(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test that we can setup with valid config."""
    mock_nuheat = _get_mock_nuheat()

    with patch(
        "homeassistant.components.nuheat.nuheat.NuHeat",
        return_value=mock_nuheat,
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ENTRY)
        config_entry.add_to_hass(hass)
        expect(
            await hass.config_entries.async_setup(config_entry.entry_id)
        ).to_be_truthy()
        await hass.async_block_till_done()
