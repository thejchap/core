"""Tryke fixtures for the IDrive e2 integration."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.idrive_e2 import CONF_BUCKET
from homeassistant.components.idrive_e2.const import DOMAIN

from .const import USER_INPUT

from tests.common import MockConfigEntry


@fixture
def mock_client() -> Generator[AsyncMock]:
    """Mock the IDrive e2 client."""
    with patch(
        "homeassistant.components.idrive_e2.AioSession.create_client",
        autospec=True,
        return_value=AsyncMock(),
    ) as create_client:
        client = create_client.return_value
        client.get_paginator = MagicMock()
        client.get_paginator.return_value.paginate.return_value.__aiter__.return_value = []
        client.create_multipart_upload.return_value = {"UploadId": "upload_id"}
        client.upload_part.return_value = {"ETag": "etag"}
        client.list_buckets.return_value = {
            "Buckets": [{"Name": USER_INPUT[CONF_BUCKET]}]
        }
        client.head_bucket.return_value = {}
        create_client.return_value.__aenter__.return_value = client
        yield client


@fixture
def mock_idrive_client() -> Generator[AsyncMock]:
    """Patch IDriveE2Client to return a mocked client."""
    from homeassistant.components.idrive_e2.const import CONF_ENDPOINT_URL

    inner = AsyncMock()
    inner.get_region_endpoint.return_value = USER_INPUT[CONF_ENDPOINT_URL]

    with patch(
        "homeassistant.components.idrive_e2.config_flow.IDriveE2Client",
        return_value=inner,
    ):
        yield inner


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        entry_id="test",
        title="test",
        domain=DOMAIN,
        data=USER_INPUT,
    )
