"""Tryke fixtures for Deako tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from tryke import Depends, fixture

from homeassistant.components.deako.const import DOMAIN

from tests.common import MockConfigEntry


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


@fixture
def mock_async_zeroconf(
    _zc: MagicMock = Depends(mock_zeroconf),
) -> Generator[MagicMock]:
    """Mock AsyncZeroconf."""
    from zeroconf import DNSCache, Zeroconf  # noqa: PLC0415
    from zeroconf.asyncio import AsyncZeroconf  # noqa: PLC0415

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
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
    )


@fixture
def pydeako_deako_mock() -> Generator[MagicMock]:
    """Mock pydeako deako client."""
    with patch("homeassistant.components.deako.Deako", autospec=True) as mock:
        yield mock


@fixture
def pydeako_discoverer_mock(
    _zc: MagicMock = Depends(mock_async_zeroconf),
) -> Generator[MagicMock]:
    """Mock pydeako discovery client."""
    with (
        patch("homeassistant.components.deako.DeakoDiscoverer", autospec=True) as mock,
        patch("homeassistant.components.deako.config_flow.DeakoDiscoverer", new=mock),
    ):
        yield mock


@fixture
def mock_deako_setup() -> Generator[MagicMock]:
    """Mock async_setup_entry for config flow tests."""
    with patch(
        "homeassistant.components.deako.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup
