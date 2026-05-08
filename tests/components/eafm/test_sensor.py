"""Tests for polling measures."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def reading_measures_not_list(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that a measure can be a dict not a list."""
    initial_value = {
        "label": "My station",
        "measures": {
            "@id": "really-long-unique-id",
            "label": "York Viking Recorder - level-stage-i-15_min----",
            "qualifier": "Stage",
            "parameterName": "Water Level",
            "latestReading": {"value": 5},
            "stationReference": "L1234",
        },
    }
    mock_get_station = AsyncMock(return_value=initial_value)

    with patch(
        "homeassistant.components.eafm.coordinator.get_station",
        new=mock_get_station,
    ):
        entry = MockConfigEntry(
            version=1,
            domain="eafm",
            entry_id="VikingRecorder1234",
            data={"station": "L1234"},
            title="Viking Recorder",
        )
        entry.add_to_hass(hass)
        expect(await async_setup_component(hass, "eafm", {})).to_be(True)
        expect(entry.state).to_be(ConfigEntryState.LOADED)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.my_station_water_level_stage")
        expect(state).not_.to_be(None)
        expect(state.state).to_equal("5")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reading_no_unit() -> None:
    """Stub for test_reading_no_unit (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def ignore_invalid_latest_reading() -> None:
    """Stub for test_ignore_invalid_latest_reading (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reading_unavailable() -> None:
    """Stub for test_reading_unavailable (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def recover_from_failure() -> None:
    """Stub for test_recover_from_failure (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reading_is_sampled() -> None:
    """Stub for test_reading_is_sampled (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def multiple_readings_are_sampled() -> None:
    """Stub for test_multiple_readings_are_sampled (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def ignore_no_latest_reading() -> None:
    """Stub for test_ignore_no_latest_reading (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_measures() -> None:
    """Stub for test_no_measures (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def mark_existing_as_unavailable_if_no_latest() -> None:
    """Stub for test_mark_existing_as_unavailable_if_no_latest (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""


