"""Tryke fixtures for APCUPSd."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.apcupsd.const import DOMAIN
from homeassistant.components.apcupsd.coordinator import APCUPSdData
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant

from . import CONF_DATA, MOCK_STATUS

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.apcupsd.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
async def mock_request_status() -> AsyncGenerator[AsyncMock]:
    """Return a mocked aioapcaccess.request_status function."""
    with patch("aioapcaccess.request_status") as mock_request_status:
        mock_request_status.return_value = MOCK_STATUS
        yield mock_request_status


@fixture
def mock_config_entry(
    mock_request_status: AsyncMock = Depends(mock_request_status),
) -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="APC UPS Daemon",
        data=CONF_DATA,
        unique_id=APCUPSdData(mock_request_status.return_value).serial_no,
        source=SOURCE_USER,
    )


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_request_status: AsyncMock = Depends(mock_request_status),
) -> MockConfigEntry:
    """Set up APC UPS Daemon integration for testing."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    return mock_config_entry
