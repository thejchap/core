"""Tryke fixtures for Ambient Weather Network tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aioambient import OpenAPI
from tryke import Depends, fixture

from homeassistant.components.ambient_network.const import DOMAIN

from tests.common import (
    MockConfigEntry,
    load_json_array_fixture,
    load_json_object_fixture,
)


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.ambient_network.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def devices_by_location() -> list[dict[str, Any]]:
    """Return result of OpenAPI get_devices_by_location() call."""
    return load_json_array_fixture(
        "devices_by_location_response.json", "ambient_network"
    )


def _mock_device_details_callable(mac_address: str) -> dict[str, Any]:
    """Return result of OpenAPI get_device_details() call."""
    return load_json_object_fixture(
        f"device_details_response_{mac_address[0].lower()}.json", "ambient_network"
    )


@fixture
def open_api() -> OpenAPI:
    """Mock OpenAPI object."""
    return Mock(
        get_device_details=AsyncMock(side_effect=_mock_device_details_callable),
    )


@fixture
async def aioambient(open_api: OpenAPI = Depends(open_api)) -> AsyncGenerator[None]:
    """Mock aioambient library."""
    with (
        patch(
            "homeassistant.components.ambient_network.config_flow.OpenAPI",
            return_value=open_api,
        ),
        patch(
            "homeassistant.components.ambient_network.OpenAPI",
            return_value=open_api,
        ),
    ):
        yield


@fixture
def config_entry_aa() -> MockConfigEntry:
    """Mock config entry for AA:AA:AA:AA:AA:AA."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Station A",
        data={"mac": "AA:AA:AA:AA:AA:AA"},
    )
