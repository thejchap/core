"""Tryke fixtures for the honeywell_string_lights integration."""

from tryke import Depends, fixture

from homeassistant.components.honeywell_string_lights.const import (
    CONF_TRANSMITTER,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry
from tests.components.radio_frequency.common import (
    MockRadioFrequencyEntity,
    init_radio_frequency_fixture_helper,
    mock_rf_entity_fixture_helper,
)
from tests.hass_fixtures import hass as hass_fixture

TRANSMITTER_ENTITY_ID = "radio_frequency.test_rf_transmitter"


@fixture
async def init_radio_frequency(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up the Radio Frequency integration for testing."""
    await init_radio_frequency_fixture_helper(hass)


@fixture
async def mock_rf_entity(
    hass: HomeAssistant = Depends(hass_fixture),
    _init_rf: None = Depends(init_radio_frequency),
) -> MockRadioFrequencyEntity:
    """Return a mock radio frequency entity."""
    return await mock_rf_entity_fixture_helper(hass)


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rf_entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
) -> MockConfigEntry:
    """Return a mock config entry for Honeywell String Lights."""
    entity_registry = er.async_get(hass)
    entity_entry = entity_registry.async_get(TRANSMITTER_ENTITY_ID)
    return MockConfigEntry(
        domain=DOMAIN,
        title="Honeywell String Lights",
        data={CONF_TRANSMITTER: entity_entry.id},
        unique_id=entity_entry.id,
    )
