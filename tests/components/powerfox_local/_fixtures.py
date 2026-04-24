"""Tryke fixtures for Powerfox Local tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from powerfox import LocalResponse
from tryke import Depends, fixture

from homeassistant.components.powerfox_local.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_HOST

from . import MOCK_API_KEY, MOCK_DEVICE_ID, MOCK_HOST

from tests.common import MockConfigEntry


def _local_response() -> LocalResponse:
    return LocalResponse(
        timestamp=datetime(2024, 11, 26, 10, 48, 51, tzinfo=UTC),
        power=111,
        energy_usage=1111111,
        energy_return=111111,
        energy_usage_high_tariff=111111,
        energy_usage_low_tariff=111111,
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.powerfox_local.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_powerfox_local_client() -> Generator[AsyncMock]:
    """Mock a PowerfoxLocal client."""
    with (
        patch(
            "homeassistant.components.powerfox_local.coordinator.PowerfoxLocal",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.powerfox_local.config_flow.PowerfoxLocal",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.value.return_value = _local_response()
        yield client


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a Powerfox Local config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"Poweropti ({MOCK_DEVICE_ID[-5:]})",
        unique_id=MOCK_DEVICE_ID,
        data={
            CONF_HOST: MOCK_HOST,
            CONF_API_KEY: MOCK_API_KEY,
        },
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
