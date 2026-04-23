"""Tryke fixtures for Duck DNS."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.duckdns.const import DOMAIN
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_DOMAIN

from tests.common import MockConfigEntry

TEST_SUBDOMAIN = "homeassistant"
TEST_TOKEN = "123e4567-e89b-12d3-a456-426614174000"
NEW_TOKEN = "11111111-2222-3333-4444-55555555"


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.duckdns.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def config_entry() -> MockConfigEntry:
    """Mock Duck DNS configuration entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"{TEST_SUBDOMAIN}.duckdns.org",
        data={
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
        },
        entry_id="12345",
    )


@fixture
def mock_update_duckdns() -> Generator[AsyncMock]:
    """Mock _update_duckdns."""

    with patch(
        "homeassistant.components.duckdns.config_flow.update_duckdns",
        return_value=True,
    ) as mock:
        yield mock


@fixture
def mock_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf."""
    from zeroconf import DNSCache  # noqa: PLC0415

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser",
        ) as mock_browser,
    ):
        asb = mock_browser.return_value
        asb.async_cancel = AsyncMock()
        zc = mock_zc.return_value
        zc.cache = DNSCache()
        yield mock_zc
