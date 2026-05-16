"""Tryke fixtures for the WebDAV tests."""

from collections.abc import AsyncGenerator, AsyncIterator, Generator
from json import dumps
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.backup import DOMAIN as BACKUP_DOMAIN
from homeassistant.components.webdav.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .const import BACKUP_METADATA, MOCK_LIST_FILES

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.webdav.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="user@webdav.demo",
        domain=DOMAIN,
        data={
            CONF_URL: "https://webdav.demo",
            CONF_USERNAME: "user",
            CONF_PASSWORD: "supersecretpassword",
        },
        entry_id="01JKXV07ASC62D620DGYNG2R8H",
    )


async def _download_mock(path: str, timeout=None) -> AsyncIterator[bytes]:
    """Mock the download function."""
    if path.endswith(".json"):
        yield dumps(BACKUP_METADATA).encode()
        return

    yield b"backup data"


@fixture
def webdav_client() -> Generator[AsyncMock]:
    """Mock the aiowebdav client."""
    with (
        patch(
            "homeassistant.components.webdav.helpers.Client",
            autospec=True,
        ) as mock_webdav_client,
    ):
        mock = mock_webdav_client.return_value
        mock.check.return_value = True
        mock.mkdir.return_value = True
        mock.list_files.return_value = MOCK_LIST_FILES
        mock.download_iter.side_effect = _download_mock
        mock.upload_iter.return_value = None
        mock.clean.return_value = None
        mock.move.return_value = None
        yield mock


@fixture
async def setup_backup_integration(
    hass: HomeAssistant = Depends(hass_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    webdav_client: AsyncMock = Depends(webdav_client),
) -> AsyncGenerator[None]:
    """Set up webdav integration with backup component."""
    with (
        patch("homeassistant.components.backup.is_hassio", return_value=False),
        patch("homeassistant.components.backup.store.STORE_DELAY_SAVE", 0),
    ):
        assert await async_setup_component(hass, BACKUP_DOMAIN, {})
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        yield
