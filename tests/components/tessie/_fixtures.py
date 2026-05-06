"""Tryke fixtures for Tessie."""

from __future__ import annotations

from collections.abc import Iterator
from copy import deepcopy
from unittest.mock import AsyncMock, patch

from tryke import fixture

from .common import (
    COMMAND_OK,
    ENERGY_HISTORY,
    LIVE_STATUS,
    PRODUCTS,
    SCOPES,
    SITE_INFO,
    TEST_STATE_OF_ALL_VEHICLES,
    TEST_VEHICLE_STATE_ONLINE,
)


@fixture
def mock_get_state() -> Iterator[AsyncMock]:
    """Mock get_state function."""
    with patch(
        "tesla_fleet_api.tessie.Vehicle.state",
        new_callable=AsyncMock,
    ) as mock_get_state:
        mock_get_state.return_value = TEST_VEHICLE_STATE_ONLINE
        yield mock_get_state


@fixture
def mock_get_state_of_all_vehicles() -> Iterator[AsyncMock]:
    """Mock get_state_of_all_vehicles function."""
    with patch(
        "tesla_fleet_api.tessie.Tessie.list_vehicles",
        new_callable=AsyncMock,
    ) as mock_get_state_of_all_vehicles:
        mock_get_state_of_all_vehicles.return_value = TEST_STATE_OF_ALL_VEHICLES
        yield mock_get_state_of_all_vehicles


@fixture
def mock_scopes() -> Iterator[AsyncMock]:
    """Mock scopes function."""
    with patch(
        "homeassistant.components.tessie.Tessie.scopes",
        return_value=SCOPES,
    ) as mock_scopes:
        yield mock_scopes


@fixture
def mock_products() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet Api products method."""
    with patch(
        "homeassistant.components.tessie.Tessie.products", return_value=PRODUCTS
    ) as mock_products:
        yield mock_products


@fixture
def mock_request() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet API request method."""
    with patch(
        "homeassistant.components.tessie.Tessie._request",
        return_value=COMMAND_OK,
    ) as mock_request:
        yield mock_request


@fixture
def mock_live_status() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet API EnergySpecific live_status method."""
    with patch(
        "tesla_fleet_api.tessie.EnergySite.live_status",
        side_effect=lambda: deepcopy(LIVE_STATUS),
    ) as mock_live_status:
        yield mock_live_status


@fixture
def mock_site_info() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet API EnergySpecific site_info method."""
    with patch(
        "tesla_fleet_api.tessie.EnergySite.site_info",
        side_effect=lambda: deepcopy(SITE_INFO),
    ) as mock_site_info:
        yield mock_site_info


@fixture
def mock_energy_history() -> Iterator[AsyncMock]:
    """Mock Tesla Fleet API EnergySite energy_history method."""
    with patch(
        "tesla_fleet_api.tessie.EnergySite.energy_history",
        side_effect=lambda *a, **kw: deepcopy(ENERGY_HISTORY),
    ) as mock_energy_history:
        yield mock_energy_history


@fixture
def mock_config_flow_list_vehicles() -> Iterator[AsyncMock]:
    """Mock Tessie.list_vehicles in config flow."""
    with patch(
        "homeassistant.components.tessie.config_flow.Tessie.list_vehicles",
        return_value=TEST_STATE_OF_ALL_VEHICLES,
    ) as mock_list_vehicles:
        yield mock_list_vehicles


@fixture
def mock_async_setup_entry() -> Iterator[AsyncMock]:
    """Mock async_setup_entry."""
    with patch(
        "homeassistant.components.tessie.async_setup_entry",
        return_value=True,
    ) as mock_async_setup_entry:
        yield mock_async_setup_entry
