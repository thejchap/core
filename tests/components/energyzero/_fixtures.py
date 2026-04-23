"""Tryke fixtures for EnergyZero."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.energyzero.const import DOMAIN

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.energyzero.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="energy",
        domain=DOMAIN,
        data={},
        unique_id=DOMAIN,
        entry_id="12345",
    )


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
