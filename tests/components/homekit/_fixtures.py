"""Tryke fixtures for the homekit integration.

Mirrors ``tests/components/homekit/conftest.py`` (pytest) for tryke ports.
Each consumer test should import the fixtures it needs and wire them via
``Depends(...)``. The module-local ``_trigger_executor`` pattern (see
``.migration/PATTERNS.md``) is used by individual test files, not here.
"""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from contextlib import suppress
import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from tryke import Depends, fixture

from homeassistant.components.device_tracker.legacy import YAML_DEVICES
from homeassistant.components.homekit.accessories import HomeDriver
from homeassistant.components.homekit.const import BRIDGE_NAME, EVENT_HOMEKIT_CHANGED
from homeassistant.components.homekit.iidmanager import AccessoryIIDStorage
from homeassistant.core import Event, HomeAssistant

from tests.common import async_capture_events
from tests.hass_fixtures import hass as hass_fixture


@fixture
def iid_storage(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[AccessoryIIDStorage]:
    """Mock the iid storage."""
    with patch.object(AccessoryIIDStorage, "_async_schedule_save"):
        yield AccessoryIIDStorage(hass, "")


@fixture
def run_driver(
    hass: HomeAssistant = Depends(hass_fixture),
    iid_storage: AccessoryIIDStorage = Depends(iid_storage),
) -> Generator[HomeDriver]:
    """Return a HomeDriver instance for HomeKit accessory init.

    This driver is not stopped on teardown (matches the legacy conftest).
    """
    event_loop = asyncio.get_event_loop()
    with (
        patch("pyhap.accessory_driver.AsyncZeroconf"),
        patch("pyhap.accessory_driver.AccessoryEncoder"),
        patch("pyhap.accessory_driver.HAPServer"),
        patch("pyhap.accessory_driver.AccessoryDriver.publish"),
        patch("pyhap.accessory_driver.AccessoryDriver.persist"),
    ):
        yield HomeDriver(
            hass,
            pincode=b"123-45-678",
            entry_id="",
            entry_title="mock entry",
            bridge_name=BRIDGE_NAME,
            iid_storage=iid_storage,
            address="127.0.0.1",
            loop=event_loop,
        )


@fixture
def hk_driver(
    hass: HomeAssistant = Depends(hass_fixture),
    iid_storage: AccessoryIIDStorage = Depends(iid_storage),
) -> Generator[HomeDriver]:
    """Return a HomeDriver instance for HomeKit accessory init."""
    event_loop = asyncio.get_event_loop()
    with (
        patch("pyhap.accessory_driver.AsyncZeroconf"),
        patch("pyhap.accessory_driver.AccessoryEncoder"),
        patch("pyhap.accessory_driver.HAPServer.async_stop"),
        patch("pyhap.accessory_driver.HAPServer.async_start"),
        patch("pyhap.accessory_driver.AccessoryDriver.publish"),
        patch("pyhap.accessory_driver.AccessoryDriver.persist"),
    ):
        yield HomeDriver(
            hass,
            pincode=b"123-45-678",
            entry_id="",
            entry_title="mock entry",
            bridge_name=BRIDGE_NAME,
            iid_storage=iid_storage,
            address="127.0.0.1",
            loop=event_loop,
        )


@fixture
def mock_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf — local copy of tests/conftest.py:mock_zeroconf."""
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
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> Generator[MagicMock]:
    """Mock AsyncZeroconf — local copy of tests/conftest.py:mock_async_zeroconf."""
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
def mock_hap(
    hass: HomeAssistant = Depends(hass_fixture),
    iid_storage: AccessoryIIDStorage = Depends(iid_storage),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> Generator[HomeDriver]:
    """Return a HomeDriver with start/stop fully mocked."""
    event_loop = asyncio.get_event_loop()
    with (
        patch("pyhap.accessory_driver.AsyncZeroconf"),
        patch("pyhap.accessory_driver.AccessoryEncoder"),
        patch("pyhap.accessory_driver.HAPServer.async_stop"),
        patch("pyhap.accessory_driver.HAPServer.async_start"),
        patch("pyhap.accessory_driver.AccessoryDriver.publish"),
        patch("pyhap.accessory_driver.AccessoryDriver.async_start"),
        patch("pyhap.accessory_driver.AccessoryDriver.async_stop"),
        patch("pyhap.accessory_driver.AccessoryDriver.persist"),
    ):
        yield HomeDriver(
            hass,
            pincode=b"123-45-678",
            entry_id="",
            entry_title="mock entry",
            bridge_name=BRIDGE_NAME,
            iid_storage=iid_storage,
            address="127.0.0.1",
            loop=event_loop,
        )


@fixture
def events(
    hass: HomeAssistant = Depends(hass_fixture),
) -> list[Event]:
    """Yield caught homekit_changed events."""
    return async_capture_events(hass, EVENT_HOMEKIT_CHANGED)


@fixture
def demo_cleanup(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[None]:
    """Clean up the device_tracker demo file after the test."""
    yield
    with suppress(FileNotFoundError):
        os.remove(hass.config.path(YAML_DEVICES))
