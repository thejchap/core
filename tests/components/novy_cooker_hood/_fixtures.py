"""Tryke fixtures for the novy_cooker_hood integration."""

from collections.abc import AsyncGenerator, Generator, Iterator
from unittest.mock import AsyncMock, MagicMock, patch

from rf_protocols import CodeCollection
from tryke import Depends, fixture

from homeassistant.components.novy_cooker_hood.const import (
    CONF_CODE,
    CONF_TRANSMITTER,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry
from tests.components.radio_frequency.common import (
    MockRadioFrequencyCommand,
    MockRadioFrequencyEntity,
    init_radio_frequency_fixture_helper,
    mock_rf_entity_fixture_helper,
)
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)

TRANSMITTER_ENTITY_ID = "radio_frequency.test_rf_transmitter"


@fixture
def mock_get_codes() -> Iterator[MagicMock]:
    """Patch the bundled-codes loader so tests don't hit the filesystem."""
    fake_collection = MagicMock(spec=CodeCollection)
    fake_collection.async_load_command = AsyncMock(
        side_effect=lambda name: MockRadioFrequencyCommand()
    )
    with patch(
        "homeassistant.components.novy_cooker_hood.commands.get_codes",
        return_value=fake_collection,
    ):
        yield fake_collection


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
def mock_config_entry(
    rf_entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> MockConfigEntry:
    """Return a mock config entry for Novy Cooker Hood."""
    entity_entry = entity_registry.async_get(TRANSMITTER_ENTITY_ID)
    assert entity_entry is not None
    return MockConfigEntry(
        domain=DOMAIN,
        title="Novy Cooker Hood",
        data={CONF_TRANSMITTER: entity_entry.id, CONF_CODE: 1},
        unique_id=f"{entity_entry.id}_1",
    )


@fixture
def mock_toggle_gap() -> Iterator[None]:
    """Set the toggle gap to 0 so the test step doesn't actually wait."""
    with patch("homeassistant.components.novy_cooker_hood.config_flow._TOGGLE_GAP", 0):
        yield
