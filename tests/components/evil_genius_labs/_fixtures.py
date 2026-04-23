"""Tryke fixtures for Evil Genius Labs."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.util.json import JsonObjectType

from tests.common import load_json_array_fixture, load_json_object_fixture


@fixture
def all_fixture() -> dict[str, Any]:
    """Fixture data."""
    data = load_json_array_fixture("data.json", "evil_genius_labs")
    return {item["name"]: item for item in data}


@fixture
def info_fixture() -> JsonObjectType:
    """Fixture info."""
    return load_json_object_fixture("info.json", "evil_genius_labs")


@fixture
def product_fixture() -> dict[str, str]:
    """Fixture info."""
    return {"productName": "Fibonacci256"}


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
