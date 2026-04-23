"""Tryke fixtures for Music Assistant config_flow tests."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from music_assistant_client.music import Music
from music_assistant_client.player_queues import PlayerQueues
from music_assistant_client.players import Players
from music_assistant_models.api import ServerInfoMessage
from music_assistant_models.config_entries import PlayerConfig
from tryke import fixture

from homeassistant.components.music_assistant.config_flow import CONF_URL
from homeassistant.components.music_assistant.const import DOMAIN

from tests.common import MockConfigEntry, load_fixture

MOCK_SERVER_ID = "1234"


@fixture
def mock_get_server_info() -> Generator[AsyncMock]:
    """Mock the function to get server info."""
    with patch(
        "homeassistant.components.music_assistant.config_flow._get_server_info"
    ) as mock_get_server_info:
        mock_get_server_info.return_value = ServerInfoMessage.from_json(
            load_fixture("server_info_message.json", DOMAIN)
        )
        yield mock_get_server_info


@fixture
async def music_assistant_client() -> AsyncGenerator[MagicMock]:
    """Fixture for a Music Assistant client."""
    with patch(
        "homeassistant.components.music_assistant.MusicAssistantClient", autospec=True
    ) as client_class:
        client = client_class.return_value

        async def connect() -> None:
            """Mock connect."""
            await asyncio.sleep(0)

        async def listen(init_ready: asyncio.Event | None) -> None:
            """Mock listen."""
            if init_ready is not None:
                init_ready.set()
            listen_block = asyncio.Event()
            await listen_block.wait()
            raise AssertionError("Listen was not cancelled!")

        client.connect = AsyncMock(side_effect=connect)
        client.start_listening = AsyncMock(side_effect=listen)
        client.send_command = AsyncMock(return_value=None)
        client.server_info = ServerInfoMessage(
            server_id=MOCK_SERVER_ID,
            server_version="0.0.0",
            schema_version=1,
            min_supported_schema_version=1,
            base_url="http://localhost:8095",
            homeassistant_addon=False,
            onboard_done=True,
        )
        client.connection = MagicMock()
        client.connection.connected = True
        client.players = Players(client)
        client.player_queues = PlayerQueues(client)
        client.music = Music(client)
        client.server_url = client.server_info.base_url
        client.get_media_item_image_url = MagicMock(return_value=None)
        client.config = MagicMock()

        async def get_player_configs() -> list[PlayerConfig]:
            return [
                PlayerConfig(
                    values={},
                    provider=player.provider,
                    player_id=player.player_id,
                )
                for player in client.players
            ]

        client.config.get_player_configs = get_player_configs

        yield client


@fixture
def mock_async_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf to prevent cross-test teardown issues."""
    from zeroconf import DNSCache, Zeroconf
    from zeroconf.asyncio import AsyncZeroconf

    with patch(
        "homeassistant.components.zeroconf.HaAsyncZeroconf", spec=AsyncZeroconf
    ) as mock_aiozc:
        zc = mock_aiozc.return_value
        zc.async_unregister_service = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.zeroconf = Mock(spec=Zeroconf)
        zc.zeroconf.async_wait_for_start = AsyncMock()
        zc.zeroconf.cache = DNSCache()
        zc.zeroconf.done = False
        zc.async_close = AsyncMock()
        zc.ha_async_close = AsyncMock()
        yield zc


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Music Assistant",
        data={CONF_URL: "http://localhost:8095"},
        unique_id="1234",
    )
