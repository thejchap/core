"""Tryke fixtures for devolo Home Control tests."""

from collections.abc import Generator
from itertools import cycle
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from tryke import fixture

from zeroconf import DNSCache, Zeroconf
from zeroconf.asyncio import AsyncZeroconf


@fixture
def mydevolo() -> Generator[MagicMock]:
    """Fixture to patch mydevolo into a desired state."""
    mydevolo = MagicMock()
    mydevolo.uuid.return_value = "123456"
    mydevolo.credentials_valid.return_value = True
    mydevolo.maintenance.return_value = False
    mydevolo.get_gateway_ids.return_value = ["1400000000000001", "1400000000000002"]
    with patch(
        "homeassistant.components.devolo_home_control.Mydevolo",
        side_effect=cycle([mydevolo]),
    ):
        yield mydevolo


@fixture
def mock_async_zeroconf() -> Generator[MagicMock]:
    """Mock AsyncZeroconf and Zeroconf for devolo flows."""
    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser",
        ) as mock_browser,
        patch(
            "homeassistant.components.zeroconf.HaAsyncZeroconf", spec=AsyncZeroconf
        ) as mock_aiozc,
    ):
        asb = mock_browser.return_value
        asb.async_cancel = AsyncMock()
        zc = mock_zc.return_value
        zc.cache = DNSCache()
        aiozc = mock_aiozc.return_value
        aiozc.async_unregister_service = AsyncMock()
        aiozc.async_register_service = AsyncMock()
        aiozc.async_update_service = AsyncMock()
        aiozc.zeroconf = Mock(spec=Zeroconf)
        aiozc.zeroconf.async_wait_for_start = AsyncMock()
        aiozc.zeroconf.cache = DNSCache()
        aiozc.zeroconf.done = False
        aiozc.async_close = AsyncMock()
        aiozc.ha_async_close = AsyncMock()
        yield aiozc
