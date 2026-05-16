"""Shared Tryke fixtures for Amber."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, patch

from amberelectric.models.interval import Interval
from tryke import Depends, fixture

from homeassistant.components.amberelectric.const import (
    CONF_SITE_ID,
    CONF_SITE_NAME,
    DOMAIN,
)
from homeassistant.const import CONF_API_TOKEN

from .helpers import (
    CONTROLLED_LOAD_CHANNEL,
    FEED_IN_CHANNEL,
    FORECASTS,
    GENERAL_AND_CONTROLLED_SITE_ID,
    GENERAL_AND_FEED_IN_SITE_ID,
    GENERAL_CHANNEL,
    GENERAL_CHANNEL_WITH_RANGE,
    GENERAL_FORECASTS,
    GENERAL_ONLY_SITE_ID,
)

from tests.common import MockConfigEntry

MOCK_API_TOKEN = "psk_0000000000000000"


def create_amber_config_entry(
    site_id: str, entry_id: str, name: str
) -> MockConfigEntry:
    """Create an Amber config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_TOKEN: MOCK_API_TOKEN,
            CONF_SITE_NAME: name,
            CONF_SITE_ID: site_id,
        },
        entry_id=entry_id,
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.amberelectric.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_amber_client() -> Generator[AsyncMock]:
    """Mock the Amber API client."""
    with patch(
        "homeassistant.components.amberelectric.amberelectric.AmberApi",
        autospec=True,
    ) as mock_client:
        yield mock_client


@fixture
def general_channel_config_entry() -> MockConfigEntry:
    """Generate the default Amber config entry."""
    return create_amber_config_entry(GENERAL_ONLY_SITE_ID, GENERAL_ONLY_SITE_ID, "home")


@fixture
def general_channel_and_controlled_load_config_entry() -> MockConfigEntry:
    """Generate the default Amber config entry for site with controlled load."""
    return create_amber_config_entry(
        GENERAL_AND_CONTROLLED_SITE_ID, GENERAL_AND_CONTROLLED_SITE_ID, "home"
    )


@fixture
def general_channel_and_feed_in_config_entry() -> MockConfigEntry:
    """Generate the default Amber config entry for site with feed in."""
    return create_amber_config_entry(
        GENERAL_AND_FEED_IN_SITE_ID, GENERAL_AND_FEED_IN_SITE_ID, "home"
    )


@fixture
def mock_amber_client_general_channel(
    mock_amber_client: AsyncMock = Depends(mock_amber_client),
) -> AsyncMock:
    """Fake general channel prices."""
    client = mock_amber_client.return_value
    client.get_current_prices.return_value = GENERAL_CHANNEL
    return mock_amber_client


@fixture
def mock_amber_client_general_channel_with_range(
    mock_amber_client: AsyncMock = Depends(mock_amber_client),
) -> AsyncMock:
    """Fake general channel prices with a range."""
    client = mock_amber_client.return_value
    client.get_current_prices.return_value = GENERAL_CHANNEL_WITH_RANGE
    return mock_amber_client


@fixture
def mock_amber_client_general_and_controlled_load(
    mock_amber_client: AsyncMock = Depends(mock_amber_client),
) -> AsyncMock:
    """Fake general channel and controlled load channel prices."""
    client = mock_amber_client.return_value
    client.get_current_prices.return_value = (
        GENERAL_CHANNEL + CONTROLLED_LOAD_CHANNEL
    )
    return mock_amber_client


@fixture
def mock_amber_client_general_and_feed_in(
    mock_amber_client: AsyncMock = Depends(mock_amber_client),
) -> AsyncMock:
    """Set up general channel and feed in channel."""
    client = mock_amber_client.return_value
    client.get_current_prices.return_value = (
        GENERAL_CHANNEL + FEED_IN_CHANNEL
    )
    return mock_amber_client


@fixture
def mock_amber_client_forecasts(
    mock_amber_client: AsyncMock = Depends(mock_amber_client),
) -> AsyncMock:
    """Set up general channel, controlled load and feed in channel."""
    client = mock_amber_client.return_value
    client.get_current_prices.return_value = FORECASTS
    return mock_amber_client


@fixture
def mock_amber_client_general_forecasts(
    mock_amber_client: AsyncMock = Depends(mock_amber_client),
) -> AsyncMock:
    """Set up general channel only."""
    client = mock_amber_client.return_value
    client.get_current_prices.return_value = GENERAL_FORECASTS
    return mock_amber_client
