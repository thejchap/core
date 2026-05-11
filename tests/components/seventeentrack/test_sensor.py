"""Tests for the seventeentrack sensor."""

from unittest.mock import AsyncMock

from pyseventeentrack.errors import SeventeenTrackError
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from . import init_integration
from ._fixtures import (
    DEFAULT_SUMMARY,
    mock_config_entry,
    mock_seventeentrack,
)
from .conftest import get_package

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_valid_config(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_seventeentrack: AsyncMock = Depends(mock_seventeentrack),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Ensure everything starts correctly."""
    await init_integration(hass, mock_config_entry)
    expect(len(hass.states.async_entity_ids())).to_equal(len(DEFAULT_SUMMARY.keys()))


@test
async def valid_config(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_seventeentrack: AsyncMock = Depends(mock_seventeentrack),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Ensure everything starts correctly."""
    await init_integration(hass, mock_config_entry)
    expect(len(hass.states.async_entity_ids())).to_equal(len(DEFAULT_SUMMARY.keys()))


@test
async def invalid_config(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Ensure nothing is created when config is wrong."""
    await init_integration(hass, mock_config_entry)
    expect(hass.states.async_entity_ids("sensor")).to_equal([])


@test
async def login_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_seventeentrack: AsyncMock = Depends(mock_seventeentrack),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Ensure everything starts correctly."""
    mock_seventeentrack.return_value.profile.login.side_effect = SeventeenTrackError(
        "Error"
    )
    await init_integration(hass, mock_config_entry)
    expect(hass.states.async_entity_ids("sensor")).to_equal([])


@test
async def package_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_seventeentrack: AsyncMock = Depends(mock_seventeentrack),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Ensure package is added correctly when user add a new package."""
    mock_seventeentrack.return_value.profile.packages.side_effect = SeventeenTrackError(
        "Error"
    )
    mock_seventeentrack.return_value.profile.summary.return_value = {}

    await init_integration(hass, mock_config_entry)
    expect(hass.states.get("sensor.17track_package_friendly_name_1")).to_be(None)


@test
async def summary_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_seventeentrack: AsyncMock = Depends(mock_seventeentrack),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test summary empty if error."""
    package = get_package(status=30)
    mock_seventeentrack.return_value.profile.packages.return_value = [package]
    mock_seventeentrack.return_value.profile.summary.side_effect = SeventeenTrackError(
        "Error"
    )

    await init_integration(hass, mock_config_entry)

    expect(len(hass.states.async_entity_ids())).to_equal(0)

    expect(
        hass.states.get("sensor.seventeentrack_packages_ready_to_be_picked_up")
    ).to_be(None)
