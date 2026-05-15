"""Tryke fixtures for snooz tests (ported from conftest.py)."""

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from . import SnoozFixture, create_mock_snooz, create_mock_snooz_config_entry

from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture


@fixture
async def mock_connected_snooz(
    hass: HomeAssistant = Depends(hass_fixture),
    _bluetooth: None = Depends(enable_bluetooth),
) -> SnoozFixture:
    """Mock a Snooz configuration entry and device."""
    device = await create_mock_snooz()
    entry = await create_mock_snooz_config_entry(hass, device)
    return SnoozFixture(entry, device)
