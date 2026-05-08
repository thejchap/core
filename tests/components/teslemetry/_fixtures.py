"""Tryke fixtures for the Teslemetry integration."""

from __future__ import annotations

from collections.abc import Generator, Iterator
from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.teslemetry.const import DOMAIN, TOKEN_URL
from homeassistant.core import HomeAssistant

from .const import (
    COMMAND_OK,
    ENERGY_HISTORY,
    LIVE_STATUS,
    METADATA,
    METADATA_LEGACY,
    PRODUCTS,
    SITE_INFO,
    VEHICLE_DATA,
    WAKE_UP_ONLINE,
)

from tests.hass_fixtures import aioclient_mock, hass as hass_fixture
from tests.hass_tryke_helpers import setup_application_credentials
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
async def setup_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up application credentials for OAuth2."""
    await setup_application_credentials(hass, DOMAIN, "client_id", "client_secret", DOMAIN)


@fixture
def mock_token_response() -> dict[str, Any]:
    """Return a mock OAuth token response."""
    return {
        "refresh_token": "mock-refresh-token",
        "access_token": "mock-access-token",
        "type": "Bearer",
        "expires_in": 60,
    }


@fixture
def mock_token_post(
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    token_response: dict[str, Any] = Depends(mock_token_response),
) -> None:
    """Mock the OAuth token endpoint."""
    aioclient.post(TOKEN_URL, json=token_response)


@fixture
def mock_setup_entry() -> Iterator[AsyncMock]:
    """Mock Teslemetry async_setup_entry method."""
    with patch(
        "homeassistant.components.teslemetry.async_setup_entry", return_value=True
    ) as mock_async_setup_entry:
        yield mock_async_setup_entry


@fixture
def mock_metadata() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet Api metadata method."""
    with patch(
        "tesla_fleet_api.teslemetry.Teslemetry.metadata", return_value=METADATA
    ) as mock_metadata:
        yield mock_metadata


@fixture
def mock_products() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet Api products method."""
    with patch(
        "tesla_fleet_api.teslemetry.Teslemetry.products", return_value=PRODUCTS
    ) as mock_products:
        yield mock_products


@fixture
def mock_vehicle_data() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet API Vehicle Specific vehicle_data method."""
    with patch(
        "tesla_fleet_api.teslemetry.Vehicle.vehicle_data",
        return_value=VEHICLE_DATA,
    ) as mock_vehicle_data:
        yield mock_vehicle_data


@fixture
def mock_legacy() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet Api metadata legacy."""
    with patch(
        "tesla_fleet_api.teslemetry.Teslemetry.metadata", return_value=METADATA_LEGACY
    ) as mock_legacy:
        yield mock_legacy


@fixture
def mock_wake_up() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet API Vehicle wake_up method."""
    with patch(
        "tesla_fleet_api.teslemetry.Vehicle.wake_up",
        return_value=WAKE_UP_ONLINE,
    ) as mock_wake_up:
        yield mock_wake_up


@fixture
def mock_vehicle() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet API Vehicle vehicle method."""
    with patch(
        "tesla_fleet_api.teslemetry.Vehicle.vehicle",
        return_value=WAKE_UP_ONLINE,
    ) as mock_vehicle:
        yield mock_vehicle


@fixture
def mock_request() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet API Vehicle request method."""
    with patch(
        "tesla_fleet_api.teslemetry.Teslemetry._request",
        return_value=COMMAND_OK,
    ) as mock_request:
        yield mock_request


@fixture
def mock_live_status() -> Iterator[AsyncMock]:
    """Mock Teslemetry Energy live_status method."""
    with patch(
        "tesla_fleet_api.tesla.energysite.EnergySite.live_status",
        side_effect=lambda: deepcopy(LIVE_STATUS),
    ) as mock_live_status:
        yield mock_live_status


@fixture
def mock_site_info() -> Iterator[AsyncMock]:
    """Mock Teslemetry Energy site_info method."""
    with patch(
        "tesla_fleet_api.tesla.energysite.EnergySite.site_info",
        side_effect=lambda: deepcopy(SITE_INFO),
    ) as mock_site_info:
        yield mock_site_info


@fixture
def mock_energy_history() -> Iterator[AsyncMock]:
    """Mock Teslemetry Energy energy_history method."""
    with patch(
        "tesla_fleet_api.tesla.energysite.EnergySite.energy_history",
        return_value=ENERGY_HISTORY,
    ) as mock_energy_history:
        yield mock_energy_history


@fixture
def mock_stream_listen() -> Iterator[AsyncMock]:
    """Mock Teslemetry Stream listen method."""
    with patch(
        "teslemetry_stream.TeslemetryStream.listen",
    ) as mock_stream_listen:
        yield mock_stream_listen


@fixture
def mock_add_listener() -> Iterator[AsyncMock]:
    """Mock Teslemetry Stream add listener method."""
    from teslemetry_stream.stream import recursive_match  # noqa: PLC0415

    with patch(
        "teslemetry_stream.TeslemetryStream.async_add_listener",
    ) as mock_add_listener:
        mock_add_listener.listeners = []

        def unsubscribe() -> None:
            return

        def side_effect(callback, filters):
            mock_add_listener.listeners.append((callback, filters))
            return unsubscribe

        def send(event) -> None:
            for listener, filters in mock_add_listener.listeners:
                if recursive_match(filters, event):
                    listener(event)

        mock_add_listener.send = send
        mock_add_listener.side_effect = side_effect
        yield mock_add_listener


@fixture
def mock_stream_get_config() -> Iterator[AsyncMock]:
    """Mock Teslemetry Stream get_config method."""
    with patch(
        "teslemetry_stream.TeslemetryStreamVehicle.get_config",
    ) as mock_stream_get_config:
        yield mock_stream_get_config


@fixture
def mock_stream_update_config() -> Iterator[AsyncMock]:
    """Mock Teslemetry Stream update_config method."""
    with patch(
        "teslemetry_stream.TeslemetryStreamVehicle.update_config",
    ) as mock_stream_update_config:
        yield mock_stream_update_config


@fixture
def mock_stream_connected() -> Iterator[AsyncMock]:
    """Mock Teslemetry Stream connected method."""
    with patch(
        "teslemetry_stream.TeslemetryStream.connected",
        return_value=True,
    ) as mock_stream_connected:
        yield mock_stream_connected


@fixture
def mock_api_chain(
    metadata: AsyncMock = Depends(mock_metadata),
    products: AsyncMock = Depends(mock_products),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
    wake_up: AsyncMock = Depends(mock_wake_up),
    vehicle: AsyncMock = Depends(mock_vehicle),
    request: AsyncMock = Depends(mock_request),
    live_status: AsyncMock = Depends(mock_live_status),
    site_info: AsyncMock = Depends(mock_site_info),
    energy_history: AsyncMock = Depends(mock_energy_history),
    stream_listen: AsyncMock = Depends(mock_stream_listen),
    add_listener: AsyncMock = Depends(mock_add_listener),
    stream_get_config: AsyncMock = Depends(mock_stream_get_config),
    stream_update_config: AsyncMock = Depends(mock_stream_update_config),
    stream_connected: AsyncMock = Depends(mock_stream_connected),
) -> Generator[None]:
    """Bundle the autouse Teslemetry API mocks for tests that just need defaults."""
    yield None
