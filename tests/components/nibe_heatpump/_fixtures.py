"""Tryke fixtures for the nibe_heatpump integration."""

from collections.abc import Generator
from contextlib import ExitStack
from unittest.mock import AsyncMock, Mock, patch

from nibe.exceptions import CoilNotFoundException
from tryke import Depends, fixture

from . import MockConnection


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Make sure we never actually run setup."""
    with patch(
        "homeassistant.components.nibe_heatpump.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_connection_construct() -> Mock:
    """Catch constructor calls."""
    return Mock()


@fixture
def mock_connection(
    construct: Mock = Depends(mock_connection_construct),
) -> Generator[MockConnection]:
    """Provide a mock connection."""
    mock_connection = MockConnection()

    def construct_fn(heatpump, *args, **kwargs):
        construct(heatpump, *args, **kwargs)
        mock_connection.heatpump = heatpump
        return mock_connection

    with ExitStack() as stack:
        places = [
            "homeassistant.components.nibe_heatpump.config_flow.NibeGW",
            "homeassistant.components.nibe_heatpump.config_flow.Modbus",
            "homeassistant.components.nibe_heatpump.NibeGW",
            "homeassistant.components.nibe_heatpump.Modbus",
        ]
        for place in places:
            stack.enter_context(patch(place, new=construct_fn))
        yield mock_connection


@fixture
def coils(
    connection: MockConnection = Depends(mock_connection),
) -> Generator[dict[int, object]]:
    """Return a dict with coil data."""
    from homeassistant.components.nibe_heatpump import HeatPump  # noqa: PLC0415

    get_coils_original = HeatPump.get_coils
    get_coil_by_address_original = HeatPump.get_coil_by_address

    def get_coils(x):
        coils_data = get_coils_original(x)
        return [coil for coil in coils_data if coil.address in connection.coils]

    def get_coil_by_address(self, address):
        coils_data = get_coil_by_address_original(self, address)
        if coils_data.address not in connection.coils:
            raise CoilNotFoundException
        return coils_data

    with (
        patch.object(HeatPump, "get_coils", new=get_coils),
        patch.object(HeatPump, "get_coil_by_address", new=get_coil_by_address),
    ):
        yield connection.coils
