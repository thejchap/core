"""Tryke fixtures for MadVR config_flow tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from tryke import fixture

from homeassistant.components.madvr.const import DEFAULT_NAME, DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import MOCK_CONFIG, MOCK_MAC

from tests.common import MockConfigEntry


@fixture
async def avoid_wait() -> AsyncGenerator[None]:
    """Mock sleep."""
    with patch("homeassistant.components.madvr.config_flow.RETRY_INTERVAL", 0):
        yield


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.madvr.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_madvr_client() -> Generator[AsyncMock]:
    """Mock a MadVR client."""
    with (
        patch(
            "homeassistant.components.madvr.config_flow.Madvr", autospec=True
        ) as mock_client,
        patch("homeassistant.components.madvr.Madvr", new=mock_client),
    ):
        client = mock_client.return_value
        client.host = MOCK_CONFIG[CONF_HOST]
        client.port = MOCK_CONFIG[CONF_PORT]
        client.mac_address = MOCK_MAC
        client.connected.return_value = True
        client.is_device_connectable.return_value = True
        client.loop = AsyncMock()
        client.tasks = AsyncMock()
        client.set_update_callback = MagicMock()

        is_on_mock = PropertyMock(return_value=True)
        type(client).is_on = is_on_mock

        yield client


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        unique_id=MOCK_MAC,
        title=DEFAULT_NAME,
        entry_id="3bd2acb0e4f0476d40865546d0d91132",
    )
