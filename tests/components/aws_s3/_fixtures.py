"""Common fixtures for AWS S3 tests."""

from collections.abc import AsyncIterator, Generator
import json
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.aws_s3.backup import suggested_filenames
from homeassistant.components.aws_s3.const import DOMAIN
from homeassistant.components.backup import AgentBackup

from tests.common import MockConfigEntry

from .const import CONFIG_ENTRY_DATA


@fixture
def backup_size() -> int:
    """Backup size, override in tests to change defaults."""
    return 2**20


@fixture
def mock_agent_backup(backup_size: int = Depends(backup_size)) -> AgentBackup:
    """Test backup fixture."""
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
        size=backup_size,
    )


@fixture
def mock_client(
    mock_agent_backup: AgentBackup = Depends(mock_agent_backup),
) -> Generator[AsyncMock]:
    """Mock the S3 client."""
    with patch(
        "aiobotocore.session.AioSession.create_client",
        autospec=True,
        return_value=AsyncMock(),
    ) as create_client:
        client = create_client.return_value

        tar_file, metadata_file = suggested_filenames(mock_agent_backup)

        client.get_paginator = MagicMock()
        client.get_paginator.return_value.paginate.return_value.__aiter__.return_value = [
            {"Contents": [{"Key": tar_file}, {"Key": metadata_file}]}
        ]

        client.create_multipart_upload.return_value = {"UploadId": "upload_id"}
        client.upload_part.return_value = {"ETag": "etag"}

        class MockStream:
            async def iter_chunks(self) -> AsyncIterator[bytes]:
                yield b"backup data"

            async def read(self) -> bytes:
                return json.dumps(mock_agent_backup.as_dict()).encode()

        client.get_object.return_value = {"Body": MockStream()}
        client.head_bucket.return_value = {}

        create_client.return_value.__aenter__.return_value = client
        yield client


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        entry_id="test",
        title="test",
        domain=DOMAIN,
        data=CONFIG_ENTRY_DATA,
    )
