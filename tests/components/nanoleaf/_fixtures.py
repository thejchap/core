"""Tryke fixtures for Nanoleaf config_flow tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from tryke import fixture


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
