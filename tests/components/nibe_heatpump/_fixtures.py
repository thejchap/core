"""Tryke fixtures for Nibe Heat Pump tests."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import ExitStack
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from nibe.exceptions import CoilNotFoundException
from tryke import Depends, fixture

from tests.components.nibe_heatpump import MockConnection


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Make sure we never actually run setup."""
    with patch(
        "homeassistant.components.nibe_heatpump.async_setup_entry", return_value=True
    ) as mock:
        yield mock


@fixture
def mock_connection_construct() -> Mock:
    """Fixture to catch constructor calls."""
    return Mock()


@fixture
def mock_connection(
    mock_connection_construct_: Mock = Depends(mock_connection_construct),
) -> Generator[MockConnection]:
    """Make sure we have a dummy connection."""
    connection = MockConnection()

    def construct(heatpump, *args, **kwargs):
        mock_connection_construct_(heatpump, *args, **kwargs)
        connection.heatpump = heatpump
        return connection

    with ExitStack() as stack:
        places = [
            "homeassistant.components.nibe_heatpump.config_flow.NibeGW",
            "homeassistant.components.nibe_heatpump.config_flow.Modbus",
            "homeassistant.components.nibe_heatpump.NibeGW",
            "homeassistant.components.nibe_heatpump.Modbus",
        ]
        for place in places:
            stack.enter_context(patch(place, new=construct))
        yield connection


@fixture
def coils(
    mock_connection_: MockConnection = Depends(mock_connection),
) -> Generator[dict[int, Any]]:
    """Return a dict with coil data."""
    from homeassistant.components.nibe_heatpump import HeatPump  # noqa: PLC0415

    get_coils_original = HeatPump.get_coils
    get_coil_by_address_original = HeatPump.get_coil_by_address

    def get_coils(x):
        coils_data = get_coils_original(x)
        return [coil for coil in coils_data if coil.address in mock_connection_.coils]

    def get_coil_by_address(self, address):
        coils_data = get_coil_by_address_original(self, address)
        if coils_data.address not in mock_connection_.coils:
            raise CoilNotFoundException
        return coils_data

    with (
        patch.object(HeatPump, "get_coils", new=get_coils),
        patch.object(HeatPump, "get_coil_by_address", new=get_coil_by_address),
    ):
        yield mock_connection_.coils
