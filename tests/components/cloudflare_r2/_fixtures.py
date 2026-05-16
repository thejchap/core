"""Tryke fixtures for Cloudflare R2 tests."""

from collections.abc import AsyncGenerator, AsyncIterator, Generator
import json
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.backup import AgentBackup, DOMAIN as BACKUP_DOMAIN
from homeassistant.components.cloudflare_r2.backup import (
    MULTIPART_MIN_PART_SIZE_BYTES,
    suggested_filenames,
)
from homeassistant.components.cloudflare_r2.const import CONF_PREFIX, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import setup_integration
from .const import USER_INPUT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx


def _make_test_backup(size: int) -> AgentBackup:
    """Build an ``AgentBackup`` of the requested size."""
    return AgentBackup(
        addons=[],
        backup_id="23e64aec",
        date="2024-11-22T11:48:48.727189+01:00",
        database_included=True,
        extra_metadata={},
        folders=[],
        homeassistant_included=True,
        homeassistant_version="2024.12.0.dev0",
        name="Core 2024.12.0.dev0",
        protected=False,
        size=size,
    )


@fixture
def test_backup() -> AgentBackup:
    """Test backup fixture (small / single-part upload)."""
    return _make_test_backup(2**20)


@fixture
def test_backup_large() -> AgentBackup:
    """Test backup fixture (large / multipart upload)."""
    return _make_test_backup(MULTIPART_MIN_PART_SIZE_BYTES)


@fixture
def test_backup_xlarge() -> AgentBackup:
    """Test backup fixture (extra large / multipart upload, multiple parts)."""
    return _make_test_backup(MULTIPART_MIN_PART_SIZE_BYTES * 2)


def _build_mock_client(backup: AgentBackup) -> Generator[AsyncMock]:
    """Patch the aiobotocore client and yield the configured mock."""
    with patch(
        "aiobotocore.session.AioSession.create_client",
        autospec=True,
        return_value=AsyncMock(),
    ) as create_client:
        client = create_client.return_value

        tar_file, metadata_file = suggested_filenames(backup)
        client.list_objects_v2.return_value = {
            "Contents": [{"Key": tar_file}, {"Key": metadata_file}]
        }
        client.create_multipart_upload.return_value = {"UploadId": "upload_id"}
        client.upload_part.return_value = {"ETag": "etag"}

        class MockStream:
            async def iter_chunks(self) -> AsyncIterator[bytes]:
                yield b"backup data"

            async def read(self) -> bytes:
                return json.dumps(backup.as_dict()).encode()

        client.get_object.return_value = {"Body": MockStream()}
        client.head_bucket.return_value = {}

        create_client.return_value.__aenter__.return_value = client
        yield client


@fixture
def mock_client(
    backup: AgentBackup = Depends(test_backup),
) -> Generator[AsyncMock]:
    """Mock the R2 client (S3-compatible) for small backups."""
    yield from _build_mock_client(backup)


@fixture
def mock_client_large(
    backup: AgentBackup = Depends(test_backup_large),
) -> Generator[AsyncMock]:
    """Mock the R2 client (S3-compatible) for large/multipart backups."""
    yield from _build_mock_client(backup)


@fixture
def mock_client_xlarge(
    backup: AgentBackup = Depends(test_backup_xlarge),
) -> Generator[AsyncMock]:
    """Mock the R2 client (S3-compatible) for extra-large/multipart backups."""
    yield from _build_mock_client(backup)


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        entry_id="test",
        title="test",
        domain=DOMAIN,
        data=USER_INPUT,
    )


@fixture
def mock_config_entry_with_prefix(
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> MockConfigEntry:
    """Return a mocked config entry with a prefix configured."""
    data = dict(entry.data)
    data[CONF_PREFIX] = "ha/backups"
    return MockConfigEntry(
        entry_id=entry.entry_id,
        title=entry.title,
        domain=entry.domain,
        data=data,
    )


@fixture
async def setup_backup_integration(
    hass: HomeAssistant = Depends(hass_fx),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_client),
) -> AsyncGenerator[None]:
    """Set up R2 + Backup integrations for testing (small backup variant)."""
    with (
        patch("homeassistant.components.backup.is_hassio", return_value=False),
        patch("homeassistant.components.backup.store.STORE_DELAY_SAVE", 0),
    ):
        assert await async_setup_component(hass, BACKUP_DOMAIN, {})
        await setup_integration(hass, entry)
        await hass.async_block_till_done()
        yield


@fixture
async def setup_backup_integration_large(
    hass: HomeAssistant = Depends(hass_fx),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_client_large),
) -> AsyncGenerator[None]:
    """Set up R2 + Backup integrations for testing (large backup variant)."""
    with (
        patch("homeassistant.components.backup.is_hassio", return_value=False),
        patch("homeassistant.components.backup.store.STORE_DELAY_SAVE", 0),
    ):
        assert await async_setup_component(hass, BACKUP_DOMAIN, {})
        await setup_integration(hass, entry)
        await hass.async_block_till_done()
        yield


@fixture
async def setup_backup_integration_xlarge(
    hass: HomeAssistant = Depends(hass_fx),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_client_xlarge),
) -> AsyncGenerator[None]:
    """Set up R2 + Backup integrations for testing (extra-large backup variant)."""
    with (
        patch("homeassistant.components.backup.is_hassio", return_value=False),
        patch("homeassistant.components.backup.store.STORE_DELAY_SAVE", 0),
    ):
        assert await async_setup_component(hass, BACKUP_DOMAIN, {})
        await setup_integration(hass, entry)
        await hass.async_block_till_done()
        yield
