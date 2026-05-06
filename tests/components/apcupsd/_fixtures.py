"""Tryke fixtures for APCUPSd."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.apcupsd.const import DOMAIN
from homeassistant.components.apcupsd.coordinator import APCUPSdData
from homeassistant.config_entries import SOURCE_USER

from . import CONF_DATA, MOCK_STATUS

from tests.common import MockConfigEntry


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
