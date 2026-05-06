"""Tryke fixtures for the Waze Travel Time integration."""

from collections.abc import Generator
from unittest.mock import patch

from pywaze.route_calculator import CalcRoutesResponse, WRCError
from tryke import Depends, fixture


@fixture
def mock_update() -> Generator[object]:
    """Mock an update to the sensor."""
    with patch(
        "pywaze.route_calculator.WazeRouteCalculator.calc_routes",
        return_value=[
            CalcRoutesResponse(
                distance=300,
                duration=150,
                name="E1337 - Teststreet",
                street_names=["E1337", "IncludeThis", "Teststreet"],
            ),
            CalcRoutesResponse(
                distance=500,
                duration=600,
                name="E0815 - Otherstreet",
                street_names=["E0815", "ExcludeThis", "Otherstreet"],
            ),
        ],
    ) as mock_wrc:
        yield mock_wrc


@fixture
def validate_config_entry(mock_update: object = Depends(mock_update)) -> object:
    """Return valid config entry."""
    mock_update.return_value = []
    return mock_update


@fixture
def invalidate_config_entry(
    validate_config_entry: object = Depends(validate_config_entry),
) -> object:
    """Return invalid config entry."""
    validate_config_entry.side_effect = WRCError("test")
    return validate_config_entry
