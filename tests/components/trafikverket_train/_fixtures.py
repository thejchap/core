"""Tryke fixtures for the Trafikverket Train integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from pytrafikverket import StationInfoModel
from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.trafikverket_train.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def get_train_stations() -> list[list[StationInfoModel]]:
    """Construct StationInfoModel Mock."""
    return [
        [
            StationInfoModel(
                signature="Cst",
                station_name="Stockholm C",
                advertised=True,
            )
        ],
        [
            StationInfoModel(
                signature="U",
                station_name="Uppsala C",
                advertised=True,
            )
        ],
    ]
