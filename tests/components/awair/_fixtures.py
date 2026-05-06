"""Tryke fixtures for Awair."""

import json
from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from tests.common import load_fixture


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
def cloud_devices() -> Any:
    """Fixture representing devices returned by Awair Cloud API."""
    return json.loads(load_fixture("awair/cloud_devices.json"))


@fixture
def local_devices() -> Any:
    """Fixture representing devices returned by Awair local API."""
    return json.loads(load_fixture("awair/local_devices.json"))


@fixture
def no_devices() -> Any:
    """Fixture representing when no devices are found in Awair's cloud API."""
    return json.loads(load_fixture("awair/no_devices.json"))


@fixture
def user() -> Any:
    """Fixture representing the User object returned from Awair's Cloud API."""
    return json.loads(load_fixture("awair/user.json"))
