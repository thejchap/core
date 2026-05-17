"""Test the ISS integration setup and coordinator."""

from unittest.mock import MagicMock

from requests.exceptions import ConnectionError as RequestsConnectionError, HTTPError
from tryke import Depends, expect, fixture, test

from homeassistant.components.iss.const import MAX_CONSECUTIVE_FAILURES
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, CONF_SHOW_ON_MAP
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from ._fixtures import init_integration, mock_config_entry, mock_pyiss

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor fixture (tryke discovery quirk)."""
    return 0


@test
async def setup_entry(
    _trigger: int = Depends(_trigger_executor),
    init_int: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test successful setup of config entry."""
    expect(init_int.state).to_be(ConfigEntryState.LOADED)
    coordinator = init_int.runtime_data
    expect(coordinator.data).not_.to_be(None)
    expect(coordinator.data.number_of_people_in_space).to_equal(7)
    expect(coordinator.data.current_location).to_equal(
        {
            "latitude": "40.271698",
            "longitude": "15.619478",
        }
    )


@test
async def unload_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_int: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test unload of config entry."""
    expect(init_int.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(init_int.entry_id)
    await hass.async_block_till_done()

    expect(init_int.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def update_listener(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_int: MockConfigEntry = Depends(init_integration),
    _pyiss: MagicMock = Depends(mock_pyiss),
) -> None:
    """Test options update triggers reload and applies new options."""
    state = hass.states.get("sensor.iss")
    expect(state).not_.to_be(None)
    expect("lat" in state.attributes).to_be(True)
    expect("long" in state.attributes).to_be(True)
    expect(ATTR_LATITUDE in state.attributes).to_be(False)
    expect(ATTR_LONGITUDE in state.attributes).to_be(False)

    hass.config_entries.async_update_entry(
        init_int, options={CONF_SHOW_ON_MAP: True}
    )
    await hass.async_block_till_done()

    # After reload with show_on_map=True, attributes should switch
    state = hass.states.get("sensor.iss")
    expect(state).not_.to_be(None)
    expect(ATTR_LATITUDE in state.attributes).to_be(True)
    expect(ATTR_LONGITUDE in state.attributes).to_be(True)
    expect("lat" in state.attributes).to_be(False)
    expect("long" in state.attributes).to_be(False)


@test
async def coordinator_single_failure_uses_cached_data(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_int: MockConfigEntry = Depends(init_integration),
    pyiss: MagicMock = Depends(mock_pyiss),
) -> None:
    """Test coordinator tolerates single API failure and uses cached data."""
    coordinator = init_int.runtime_data
    original_data = coordinator.data

    pyiss.number_of_people_in_space.side_effect = HTTPError("API Error")

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    expect(coordinator.data).to_equal(original_data)
    expect(coordinator.last_update_success).to_be(True)


@test
async def coordinator_multiple_failures_uses_cached_data(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_int: MockConfigEntry = Depends(init_integration),
    pyiss: MagicMock = Depends(mock_pyiss),
) -> None:
    """Test coordinator tolerates multiple failures below threshold."""
    coordinator = init_int.runtime_data
    original_data = coordinator.data

    pyiss.number_of_people_in_space.side_effect = RequestsConnectionError(
        "Connection failed"
    )

    for _ in range(MAX_CONSECUTIVE_FAILURES - 1):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    expect(coordinator.data).to_equal(original_data)
    expect(coordinator.last_update_success).to_be(True)


@test
async def coordinator_max_failures_marks_unavailable(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_int: MockConfigEntry = Depends(init_integration),
    pyiss: MagicMock = Depends(mock_pyiss),
) -> None:
    """Test coordinator marks update failed after MAX_CONSECUTIVE_FAILURES."""
    coordinator = init_int.runtime_data

    pyiss.number_of_people_in_space.side_effect = HTTPError("API Error")

    for _ in range(MAX_CONSECUTIVE_FAILURES):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    expect(coordinator.last_update_success).to_be(False)
    expect(isinstance(coordinator.last_exception, UpdateFailed)).to_be(True)


@test
async def coordinator_failure_counter_resets_on_success(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_int: MockConfigEntry = Depends(init_integration),
    pyiss: MagicMock = Depends(mock_pyiss),
) -> None:
    """Test coordinator resets failure counter after successful fetch."""
    coordinator = init_int.runtime_data

    pyiss.number_of_people_in_space.side_effect = HTTPError("API Error")
    for _ in range(2):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    pyiss.number_of_people_in_space.side_effect = None
    pyiss.number_of_people_in_space.return_value = 8
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    expect(coordinator.last_update_success).to_be(True)
    expect(coordinator.data.number_of_people_in_space).to_equal(8)

    pyiss.number_of_people_in_space.side_effect = RequestsConnectionError(
        "Connection failed"
    )
    for _ in range(MAX_CONSECUTIVE_FAILURES - 1):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    expect(coordinator.last_update_success).to_be(True)


@test
async def coordinator_initial_failure_no_cached_data(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    pyiss: MagicMock = Depends(mock_pyiss),
) -> None:
    """Test coordinator fails immediately on initial setup with no cached data."""
    pyiss.number_of_people_in_space.side_effect = HTTPError("API Error")
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def coordinator_handles_connection_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_int: MockConfigEntry = Depends(init_integration),
    pyiss: MagicMock = Depends(mock_pyiss),
) -> None:
    """Test coordinator handles ConnectionError exceptions."""
    coordinator = init_int.runtime_data
    original_data = coordinator.data

    pyiss.current_location.side_effect = RequestsConnectionError(
        "Network unreachable"
    )

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    expect(coordinator.data).to_equal(original_data)
    expect(coordinator.last_update_success).to_be(True)
