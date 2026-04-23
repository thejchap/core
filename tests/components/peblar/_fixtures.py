"""Tryke fixtures for Peblar tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from peblar import (
    PeblarEVInterface,
    PeblarMeter,
    PeblarSystem,
    PeblarSystemInformation,
    PeblarUserConfiguration,
    PeblarVersions,
)
from tryke import Depends, fixture

from homeassistant.components.peblar.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD

from tests.common import MockConfigEntry, load_fixture


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Peblar",
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.127",
            CONF_PASSWORD: "OMGSPIDERS",
        },
        unique_id="23-45-A4O-MOF",
    )


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch("homeassistant.components.peblar.async_setup_entry", return_value=True):
        yield


@fixture
def mock_peblar() -> Generator[MagicMock]:
    """Return a mocked Peblar client."""
    with (
        patch("homeassistant.components.peblar.Peblar", autospec=True) as peblar_mock,
        patch("homeassistant.components.peblar.config_flow.Peblar", new=peblar_mock),
    ):
        peblar = peblar_mock.return_value
        peblar.available_versions.return_value = PeblarVersions.from_json(
            load_fixture("available_versions.json", DOMAIN)
        )
        peblar.current_versions.return_value = PeblarVersions.from_json(
            load_fixture("current_versions.json", DOMAIN)
        )
        peblar.user_configuration.return_value = PeblarUserConfiguration.from_json(
            load_fixture("user_configuration.json", DOMAIN)
        )
        peblar.system_information.return_value = PeblarSystemInformation.from_json(
            load_fixture("system_information.json", DOMAIN)
        )

        api = peblar.rest_api.return_value
        api.ev_interface.return_value = PeblarEVInterface.from_json(
            load_fixture("ev_interface.json", DOMAIN)
        )
        api.meter.return_value = PeblarMeter.from_json(
            load_fixture("meter.json", DOMAIN)
        )
        api.system.return_value = PeblarSystem.from_json(
            load_fixture("system.json", DOMAIN)
        )

        yield peblar


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
