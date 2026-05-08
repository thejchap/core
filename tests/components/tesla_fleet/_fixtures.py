"""Tryke fixtures for the Tesla Fleet integration."""

from __future__ import annotations

from collections.abc import Generator, Iterator
from copy import deepcopy
import time
from unittest.mock import AsyncMock, patch

from tesla_fleet_api.const import Scope
from tryke import Depends, fixture

from homeassistant.components.tesla_fleet.const import SCOPES

from .common import create_config_entry
from .const import (
    COMMAND_OK,
    ENERGY_HISTORY,
    LIVE_STATUS,
    PRODUCTS,
    SITE_INFO,
    VEHICLE_DATA,
    VEHICLE_ONLINE,
)

from tests.common import MockConfigEntry


@fixture
def expires_at() -> int:
    """Fixture to set the oauth token expiration time."""
    return int(time.time() + 3600)


@fixture
def normal_config_entry(
    expires_at_value: int = Depends(expires_at),
) -> MockConfigEntry:
    """Create Tesla Fleet entry in Home Assistant."""
    return create_config_entry(expires_at_value, SCOPES)


@fixture
def noscope_config_entry(
    expires_at_value: int = Depends(expires_at),
) -> MockConfigEntry:
    """Create Tesla Fleet entry in Home Assistant without scopes."""
    return create_config_entry(
        expires_at_value, [Scope.OPENID, Scope.OFFLINE_ACCESS]
    )


@fixture
def readonly_config_entry(
    expires_at_value: int = Depends(expires_at),
) -> MockConfigEntry:
    """Create Tesla Fleet entry in Home Assistant with read-only scopes."""
    return create_config_entry(
        expires_at_value,
        [
            Scope.OPENID,
            Scope.OFFLINE_ACCESS,
            Scope.VEHICLE_DEVICE_DATA,
            Scope.ENERGY_DEVICE_DATA,
        ],
    )


@fixture
def bad_config_entry(
    expires_at_value: int = Depends(expires_at),
) -> MockConfigEntry:
    """Create Tesla Fleet entry with a bad auth implementation."""
    return create_config_entry(expires_at_value, SCOPES, "bad")


@fixture
def mock_products() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet Api products method."""
    with patch(
        "homeassistant.components.tesla_fleet.TeslaFleetApi.products",
        return_value=PRODUCTS,
    ) as mock_products:
        yield mock_products


@fixture
def mock_vehicle_state() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet API Vehicle state method."""
    with patch(
        "tesla_fleet_api.tesla.VehicleFleet.vehicle",
        return_value=VEHICLE_ONLINE,
    ) as mock_vehicle:
        yield mock_vehicle


@fixture
def mock_vehicle_data() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet API Vehicle vehicle_data method."""
    with patch(
        "tesla_fleet_api.tesla.VehicleFleet.vehicle_data",
        return_value=VEHICLE_DATA,
    ) as mock_vehicle_data:
        yield mock_vehicle_data


@fixture
def mock_wake_up() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet API Vehicle wake_up method."""
    with patch(
        "tesla_fleet_api.tesla.VehicleFleet.wake_up",
        return_value=VEHICLE_ONLINE,
    ) as mock_wake_up:
        yield mock_wake_up


@fixture
def mock_live_status() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet API Energy live_status method."""
    with patch(
        "tesla_fleet_api.tesla.EnergySite.live_status",
        side_effect=lambda: deepcopy(LIVE_STATUS),
    ) as mock_live_status:
        yield mock_live_status


@fixture
def mock_site_info() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet API Energy site_info method."""
    with patch(
        "tesla_fleet_api.tesla.EnergySite.site_info",
        side_effect=lambda: deepcopy(SITE_INFO),
    ) as mock_site_info:
        yield mock_site_info


@fixture
def mock_find_server() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet find_server method."""
    with patch(
        "homeassistant.components.tesla_fleet.TeslaFleetApi.find_server",
    ) as mock_find_server:
        yield mock_find_server


@fixture
def mock_request() -> Iterator[AsyncMock]:
    """Mock all Tesla Fleet API requests."""
    with patch(
        "homeassistant.components.tesla_fleet.TeslaFleetApi._request",
        return_value=COMMAND_OK,
    ) as mock_request:
        yield mock_request


@fixture
def mock_energy_history() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet Energy energy_history method."""
    with patch(
        "tesla_fleet_api.tesla.EnergySite.energy_history",
        return_value=ENERGY_HISTORY,
    ) as mock_energy_history:
        yield mock_energy_history


@fixture
def mock_signed_command() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet signed_command method."""
    with patch(
        "tesla_fleet_api.tesla.VehicleSigned.signed_command",
        return_value=COMMAND_OK,
    ) as mock_signed_command:
        yield mock_signed_command


@fixture
def mock_api_chain(
    products: AsyncMock = Depends(mock_products),
    vehicle_state: AsyncMock = Depends(mock_vehicle_state),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
    wake_up: AsyncMock = Depends(mock_wake_up),
    live_status: AsyncMock = Depends(mock_live_status),
    site_info: AsyncMock = Depends(mock_site_info),
    energy_history: AsyncMock = Depends(mock_energy_history),
    signed_command: AsyncMock = Depends(mock_signed_command),
) -> Generator[None]:
    """Bundle the autouse Tesla Fleet API mocks for tests that just need defaults."""
    yield None
