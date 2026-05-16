"""Tryke fixtures for the radio_frequency integration tests."""

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.components.radio_frequency.common import (
    MockRadioFrequencyEntity,
    init_radio_frequency_fixture_helper,
    mock_rf_entity_fixture_helper,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def init_radio_frequency(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up the Radio Frequency integration for testing."""
    await init_radio_frequency_fixture_helper(hass)


@fixture
async def mock_rf_entity(
    hass: HomeAssistant = Depends(hass_fixture),
    _rf: None = Depends(init_radio_frequency),
) -> MockRadioFrequencyEntity:
    """Return a mock radio frequency entity."""
    return await mock_rf_entity_fixture_helper(hass)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts test module into Tryke's HookExecutor path."""
    return 0
