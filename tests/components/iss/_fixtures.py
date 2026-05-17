"""Tryke fixtures for the ISS integration."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.iss.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={},
        entry_id="test_entry_id",
    )


@fixture
def mock_pyiss() -> Generator[MagicMock]:
    """Mock the pyiss.ISS class."""
    with patch("homeassistant.components.iss.coordinator.pyiss.ISS") as mock_iss_class:
        mock_iss = MagicMock()
        mock_iss.number_of_people_in_space.return_value = 7
        mock_iss.current_location.return_value = {
            "latitude": "40.271698",
            "longitude": "15.619478",
        }
        mock_iss_class.return_value = mock_iss
        yield mock_iss


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _pyiss: MagicMock = Depends(mock_pyiss),
) -> MockConfigEntry:
    """Set up the ISS integration for testing."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
