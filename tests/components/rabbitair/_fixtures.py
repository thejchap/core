"""Tryke fixtures for rabbitair tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from tryke import Depends, fixture


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
def rabbitair_connect() -> Generator[None]:
    """Mock connection."""
    from rabbitair import Mode, Model, Speed  # noqa: PLC0415

    TEST_MAC = "01:23:45:67:89:AB"
    TEST_FIRMWARE = "2.3.17"
    TEST_HARDWARE = "1.0.0.4"

    mock_info = Mock()
    mock_info.mac = TEST_MAC

    mock_state = Mock()
    mock_state.model = Model.A3
    mock_state.main_firmware = TEST_HARDWARE
    mock_state.power = True
    mock_state.mode = Mode.Auto
    mock_state.speed = Speed.Low
    mock_state.wifi_firmware = TEST_FIRMWARE

    with (
        patch("rabbitair.UdpClient.get_info", return_value=mock_info),
        patch("rabbitair.UdpClient.get_state", return_value=mock_state),
    ):
        yield
