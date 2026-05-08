"""Tryke fixtures for ccm15."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from ccm15 import CCM15DeviceState, CCM15SlaveDevice
from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.ccm15.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def ccm15_device() -> Generator[None]:
    """Mock ccm15 device."""
    ccm15_devices = {
        0: CCM15SlaveDevice(bytes.fromhex("000000b0b8001b")),
        1: CCM15SlaveDevice(bytes.fromhex("00000041c0001a")),
    }
    device_state = CCM15DeviceState(devices=ccm15_devices)
    with patch(
        "homeassistant.components.ccm15.coordinator.CCM15Device.get_status_async",
        return_value=device_state,
    ):
        yield


@fixture
def network_failure_ccm15_device() -> Generator[None]:
    """Mock empty set of ccm15 device."""
    device_state = CCM15DeviceState(devices={})
    with patch(
        "homeassistant.components.ccm15.coordinator.CCM15Device.get_status_async",
        return_value=device_state,
    ):
        yield


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
