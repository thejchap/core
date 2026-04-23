"""Tryke fixtures for ntfy tests."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from aiontfy import Account, AccountTokenResponse, Event, Notification, Version
from aiontfy.update import LatestRelease
from tryke import Depends, fixture

from homeassistant.components.ntfy.const import CONF_TOPIC, DEFAULT_URL, DOMAIN
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.const import CONF_TOKEN, CONF_URL, CONF_USERNAME, CONF_VERIFY_SSL

from tests.common import MockConfigEntry, load_fixture


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
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.ntfy.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_aiontfy() -> Generator[AsyncMock]:
    """Mock aiontfy."""
    with (
        patch("homeassistant.components.ntfy.Ntfy", autospec=True) as mock_client,
        patch("homeassistant.components.ntfy.config_flow.Ntfy", new=mock_client),
    ):
        client = mock_client.return_value

        client.publish.return_value = {}
        client.account.return_value = Account.from_json(
            load_fixture("account.json", DOMAIN)
        )
        client.generate_token.return_value = AccountTokenResponse(
            token="token", last_access=datetime.now()
        )
        client.version.return_value = Version.from_json(
            load_fixture("version.json", DOMAIN)
        )

        resp = Mock(
            id="h6Y2hKA5sy0U",
            time=datetime(2025, 3, 28, 17, 58, 46, tzinfo=UTC),
            expires=datetime(2025, 3, 29, 5, 58, 46, tzinfo=UTC),
            event=Event.MESSAGE,
            topic="mytopic",
            message="Hello",
            title="Title",
            tags=["octopus"],
            priority=3,
            click="https://example.com/",
            icon="https://example.com/icon.png",
            actions=[],
            attachment=None,
            content_type=None,
            sequence_id="Mc3otamDNcpJ",
        )

        resp.to_dict.return_value = {
            "id": "h6Y2hKA5sy0U",
            "time": datetime(2025, 3, 28, 17, 58, 46, tzinfo=UTC),
            "expires": datetime(2025, 3, 29, 5, 58, 46, tzinfo=UTC),
            "event": Event.MESSAGE,
            "topic": "mytopic",
            "message": "Hello",
            "title": "Title",
            "tags": ["octopus"],
            "priority": 3,
            "click": "https://example.com/",
            "icon": "https://example.com/icon.png",
            "actions": [],
            "attachment": None,
            "content_type": None,
            "sequence_id": "Mc3otamDNcpJ",
        }

        async def mock_ws(
            topics: list[str], callback: Callable[[Notification], None], **kwargs
        ):
            callback(resp)
            while True:
                await asyncio.sleep(1)

        client.subscribe.side_effect = mock_ws

        yield client


@fixture
def mock_update_checker() -> Generator[AsyncMock]:
    """Mock aiontfy update checker."""
    with patch(
        "homeassistant.components.ntfy.UpdateChecker", autospec=True
    ) as mock_client:
        client = mock_client.return_value

        client.latest_release.return_value = LatestRelease(
            tag_name="v2.17.0",
            name="v2.17.0",
            html_url="https://github.com/binwiederhier/ntfy/releases/tag/v2.17.0",
            body="**RELEASE_NOTES**",
        )
        yield client


@fixture
def mock_random() -> Generator[MagicMock]:
    """Mock random."""
    with patch(
        "homeassistant.components.ntfy.config_flow.random.choices",
        return_value=["randomtopic"],
    ) as mock_client:
        yield mock_client


@fixture
def config_entry() -> MockConfigEntry:
    """Mock ntfy configuration entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="ntfy.sh",
        data={
            CONF_URL: DEFAULT_URL,
            CONF_USERNAME: None,
            CONF_TOKEN: "token",
            CONF_VERIFY_SSL: True,
        },
        entry_id="123456789",
        subentries_data=[
            ConfigSubentryData(
                data={CONF_TOPIC: "mytopic"},
                subentry_id="ABCDEF",
                subentry_type="topic",
                title="mytopic",
                unique_id="mytopic",
            )
        ],
    )
