"""Tryke fixtures for Azure Event Hub."""

from collections.abc import AsyncGenerator, Generator
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from azure.eventhub.aio import EventHubProducerClient
from tryke import Depends, fixture

from homeassistant.components.azure_event_hub.const import (
    CONF_FILTER,
    CONF_SEND_INTERVAL,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.dt import utcnow

from .const import AZURE_EVENT_HUB_PATH, BASIC_OPTIONS, PRODUCER_PATH, SAS_CONFIG_FULL

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import hass


@fixture
def mock_get_eventhub_properties() -> Generator[AsyncMock]:
    """Mock azure event hub properties, used to test the connection."""
    with patch(f"{PRODUCER_PATH}.get_eventhub_properties") as get_eventhub_properties:
        yield get_eventhub_properties


@fixture
def mock_from_connection_string() -> Generator[MagicMock]:
    """Mock AEH from connection string creation."""
    mock_aeh = MagicMock(spec=EventHubProducerClient)
    mock_aeh.__aenter__.return_value = mock_aeh
    with patch(
        f"{PRODUCER_PATH}.from_connection_string",
        return_value=mock_aeh,
    ) as from_conn_string:
        yield from_conn_string


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock the setup entry call, used for config flow tests."""
    with patch(
        f"{AZURE_EVENT_HUB_PATH}.async_setup_entry", return_value=True
    ) as setup_entry:
        yield setup_entry


@fixture
def mock_send_batch() -> Generator[AsyncMock]:
    """Mock send_batch."""
    with patch(f"{PRODUCER_PATH}.send_batch") as mock_send_batch:
        yield mock_send_batch


@fixture
def mock_create_batch() -> Generator[MagicMock]:
    """Mock batch creator and return mocked batch object."""
    mock_batch = MagicMock()
    with patch(f"{PRODUCER_PATH}.create_batch", return_value=mock_batch):
        yield mock_batch


@fixture
def mock_close() -> Generator[AsyncMock]:
    """Mock the close method."""
    with patch(f"{PRODUCER_PATH}.close") as mock_close:
        yield mock_close


@fixture
async def entry(
    hass: HomeAssistant = Depends(hass),
    _mock_create_batch: MagicMock = Depends(mock_create_batch),
    _mock_send_batch: AsyncMock = Depends(mock_send_batch),
    _mock_close: AsyncMock = Depends(mock_close),
    _mock_get_eventhub_properties: AsyncMock = Depends(mock_get_eventhub_properties),
) -> AsyncGenerator[MockConfigEntry]:
    """Create the setup in HA."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=SAS_CONFIG_FULL,
        title="test-instance",
        options=BASIC_OPTIONS,
    )
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_FILTER: {}}})
    assert entry.state is ConfigEntryState.LOADED

    async_fire_time_changed(
        hass,
        utcnow() + timedelta(seconds=entry.options[CONF_SEND_INTERVAL]),
    )
    await hass.async_block_till_done()

    yield entry

    await hass.config_entries.async_unload(entry.entry_id)
