"""Tryke fixtures for Paperless-ngx tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from pypaperless.models import RemoteVersion, Statistic, Status
from tryke import Depends, fixture

from homeassistant.components.paperless_ngx.const import DOMAIN

from .const import USER_INPUT_ONE

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def mock_status_data() -> dict[str, Any]:
    """Return test status data."""
    return load_json_object_fixture("test_data_status.json", DOMAIN)


@fixture
def mock_remote_version_data() -> dict[str, Any]:
    """Return test remote version data."""
    return load_json_object_fixture("test_data_remote_version.json", DOMAIN)


@fixture
def mock_statistic_data() -> dict[str, Any]:
    """Return test statistic data."""
    return load_json_object_fixture("test_data_statistic.json", DOMAIN)


@fixture
def mock_paperless(
    statistic: dict[str, Any] = Depends(mock_statistic_data),
    status: dict[str, Any] = Depends(mock_status_data),
    remote_version: dict[str, Any] = Depends(mock_remote_version_data),
) -> Generator[AsyncMock]:
    """Mock the pypaperless.Paperless client."""
    with (
        patch(
            "homeassistant.components.paperless_ngx.coordinator.Paperless",
            autospec=True,
        ) as paperless_mock,
        patch(
            "homeassistant.components.paperless_ngx.config_flow.Paperless",
            new=paperless_mock,
        ),
        patch(
            "homeassistant.components.paperless_ngx.Paperless",
            new=paperless_mock,
        ),
    ):
        paperless = paperless_mock.return_value

        paperless.base_url = "http://paperless.example.com/"
        paperless.host_version = "2.3.0"
        paperless.initialize.return_value = None
        paperless.statistics = AsyncMock(
            return_value=Statistic.create_with_data(
                paperless, data=statistic, fetched=True
            )
        )
        paperless.status = AsyncMock(
            return_value=Status.create_with_data(
                paperless, data=status, fetched=True
            )
        )
        paperless.remote_version = AsyncMock(
            return_value=RemoteVersion.create_with_data(
                paperless, data=remote_version, fetched=True
            )
        )

        yield paperless


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.paperless_ngx.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


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
        entry_id="0KLG00V55WEVTJ0CJHM0GADNGH",
        title="Paperless-ngx",
        domain=DOMAIN,
        data=USER_INPUT_ONE,
    )
