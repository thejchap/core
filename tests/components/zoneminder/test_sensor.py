"""Tests for ZoneMinder sensor entities."""

from datetime import timedelta
from unittest.mock import MagicMock, PropertyMock

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test
from zoneminder.monitor import MonitorState, TimePeriod

from homeassistant.components.zoneminder.const import DOMAIN
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import mock_zoneminder_client, single_server_config
from .conftest import create_mock_monitor

from tests.common import async_fire_time_changed
from tests.hass_fixtures import freezer as freezer_fixture, hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


async def _setup_zm_with_sensors(
    hass: HomeAssistant,
    mock_zoneminder_client: MagicMock,
    zm_config: dict,
    monitors: list,
    freezer: FrozenDateTimeFactory,
    sensor_config: dict | None = None,
    is_available: bool = True,
    active_state: str | None = "Running",
) -> None:
    """Set up ZM component with sensor platform and trigger first poll."""
    mock_zoneminder_client.get_monitors.return_value = monitors
    type(mock_zoneminder_client).is_available = PropertyMock(return_value=is_available)
    mock_zoneminder_client.get_active_state.return_value = active_state

    expect(await async_setup_component(hass, DOMAIN, zm_config)).to_be_truthy()
    await hass.async_block_till_done(wait_background_tasks=True)

    if sensor_config is None:
        sensor_config = {
            "sensor": [
                {
                    "platform": DOMAIN,
                    "monitored_conditions": [
                        "all",
                        "hour",
                        "day",
                        "week",
                        "month",
                    ],
                }
            ]
        }
    expect(await async_setup_component(hass, "sensor", sensor_config)).to_be_truthy()
    await hass.async_block_till_done(wait_background_tasks=True)
    freezer.tick(timedelta(seconds=60))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)


# --- Monitor Status Sensor ---


@test
async def monitor_status_sensor_exists(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test monitor status sensor is created."""
    monitors = [create_mock_monitor(name="Front Door", function=MonitorState.MODECT)]
    await _setup_zm_with_sensors(
        hass, mock_zoneminder_client, single_server_config, monitors, freezer
    )

    state = hass.states.get("sensor.front_door_status")
    expect(state).not_.to_be_none()


@test
async def monitor_status_sensor_value(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test monitor status sensor shows MonitorState value."""
    monitors = [create_mock_monitor(name="Front Door", function=MonitorState.RECORD)]
    await _setup_zm_with_sensors(
        hass, mock_zoneminder_client, single_server_config, monitors, freezer
    )

    state = hass.states.get("sensor.front_door_status")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("Record")


@test.cases(
    test.case("none", monitor_state=MonitorState.NONE, expected_value="None"),
    test.case("monitor", monitor_state=MonitorState.MONITOR, expected_value="Monitor"),
    test.case("modect", monitor_state=MonitorState.MODECT, expected_value="Modect"),
    test.case("record", monitor_state=MonitorState.RECORD, expected_value="Record"),
    test.case("mocord", monitor_state=MonitorState.MOCORD, expected_value="Mocord"),
    test.case("nodect", monitor_state=MonitorState.NODECT, expected_value="Nodect"),
)
async def monitor_status_sensor_all_states(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    *,
    monitor_state: MonitorState,
    expected_value: str,
) -> None:
    """Test monitor status sensor with all MonitorState values."""
    monitors = [create_mock_monitor(name="Cam", function=monitor_state)]
    await _setup_zm_with_sensors(
        hass, mock_zoneminder_client, single_server_config, monitors, freezer
    )

    state = hass.states.get("sensor.cam_status")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(expected_value)


@test
async def monitor_status_sensor_unavailable(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test monitor status sensor when monitor is unavailable."""
    monitors = [
        create_mock_monitor(name="Front Door", is_available=False, function=None)
    ]
    await _setup_zm_with_sensors(
        hass, mock_zoneminder_client, single_server_config, monitors, freezer
    )

    state = hass.states.get("sensor.front_door_status")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_UNAVAILABLE)


@test
async def monitor_status_sensor_null_function(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test monitor status sensor when function is falsy."""
    monitors = [
        create_mock_monitor(name="Front Door", function=None, is_available=True)
    ]
    await _setup_zm_with_sensors(
        hass, mock_zoneminder_client, single_server_config, monitors, freezer
    )

    state = hass.states.get("sensor.front_door_status")
    expect(state).not_.to_be_none()


# --- Event Sensors ---


@test.cases(
    test.case(
        "all", condition="all", expected_name_suffix="Events", expected_value="100"
    ),
    test.case(
        "hour",
        condition="hour",
        expected_name_suffix="Events Last Hour",
        expected_value="5",
    ),
    test.case(
        "day",
        condition="day",
        expected_name_suffix="Events Last Day",
        expected_value="20",
    ),
    test.case(
        "week",
        condition="week",
        expected_name_suffix="Events Last Week",
        expected_value="50",
    ),
    test.case(
        "month",
        condition="month",
        expected_name_suffix="Events Last Month",
        expected_value="80",
    ),
)
async def event_sensor_for_each_time_period(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    *,
    condition: str,
    expected_name_suffix: str,
    expected_value: str,
) -> None:
    """Test event sensors for all 5 time periods."""
    monitors = [create_mock_monitor(name="Front Door")]
    sensor_config = {
        "sensor": [
            {
                "platform": DOMAIN,
                "monitored_conditions": [condition],
            }
        ]
    }
    await _setup_zm_with_sensors(
        hass,
        mock_zoneminder_client,
        single_server_config,
        monitors,
        freezer,
        sensor_config=sensor_config,
    )

    entity_id = f"sensor.front_door_{expected_name_suffix.lower().replace(' ', '_')}"
    state = hass.states.get(entity_id)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(expected_value)


@test
async def event_sensor_unit_of_measurement(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test event sensors have 'Events' unit of measurement."""
    monitors = [create_mock_monitor(name="Front Door")]
    await _setup_zm_with_sensors(
        hass, mock_zoneminder_client, single_server_config, monitors, freezer
    )

    state = hass.states.get("sensor.front_door_events")
    expect(state).not_.to_be_none()
    expect(state.attributes.get("unit_of_measurement")).to_equal("Events")


@test
async def event_sensor_name_format(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test event sensor name format is '{monitor_name} {time_period_title}'."""
    monitors = [create_mock_monitor(name="Back Yard")]
    sensor_config = {
        "sensor": [
            {
                "platform": DOMAIN,
                "monitored_conditions": ["hour"],
            }
        ]
    }
    await _setup_zm_with_sensors(
        hass,
        mock_zoneminder_client,
        single_server_config,
        monitors,
        freezer,
        sensor_config=sensor_config,
    )

    state = hass.states.get("sensor.back_yard_events_last_hour")
    expect(state).not_.to_be_none()
    expect(state.name).to_equal("Back Yard Events Last Hour")


@test
async def event_sensor_none_handling(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test event sensor handles None event count."""
    monitors = [
        create_mock_monitor(
            name="Front Door",
            events=dict.fromkeys(TimePeriod),
        )
    ]
    await _setup_zm_with_sensors(
        hass, mock_zoneminder_client, single_server_config, monitors, freezer
    )

    state = hass.states.get("sensor.front_door_events")
    expect(state).not_.to_be_none()


# --- Run State Sensor ---


@test
async def run_state_sensor_exists(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test run state sensor is created."""
    monitors = [create_mock_monitor(name="Cam")]
    await _setup_zm_with_sensors(
        hass, mock_zoneminder_client, single_server_config, monitors, freezer
    )

    state = hass.states.get("sensor.run_state")
    expect(state).not_.to_be_none()


@test
async def run_state_sensor_value(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test run state sensor shows state name."""
    monitors = [create_mock_monitor(name="Cam")]
    await _setup_zm_with_sensors(
        hass,
        mock_zoneminder_client,
        single_server_config,
        monitors,
        freezer,
        active_state="Home",
    )

    state = hass.states.get("sensor.run_state")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("Home")


@test
async def run_state_sensor_unavailable(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test run state sensor when server unavailable."""
    monitors = [create_mock_monitor(name="Cam")]
    await _setup_zm_with_sensors(
        hass,
        mock_zoneminder_client,
        single_server_config,
        monitors,
        freezer,
        is_available=False,
        active_state=None,
    )

    state = hass.states.get("sensor.run_state")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_UNAVAILABLE)


# --- Platform behavior ---


@test
async def platform_not_ready_empty_monitors(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
) -> None:
    """Test PlatformNotReady on empty monitors."""
    mock_zoneminder_client.get_monitors.return_value = []

    expect(
        await async_setup_component(hass, DOMAIN, single_server_config)
    ).to_be_truthy()
    await hass.async_block_till_done()
    await async_setup_component(
        hass,
        "sensor",
        {"sensor": [{"platform": DOMAIN}]},
    )
    await hass.async_block_till_done()

    states = hass.states.async_all("sensor")
    expect(len(states)).to_equal(0)


@test
async def subset_condition_filtering(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test only selected monitored_conditions get event sensors."""
    monitors = [create_mock_monitor(name="Cam")]
    sensor_config = {
        "sensor": [
            {
                "platform": DOMAIN,
                "monitored_conditions": ["hour", "day"],
            }
        ]
    }
    await _setup_zm_with_sensors(
        hass,
        mock_zoneminder_client,
        single_server_config,
        monitors,
        freezer,
        sensor_config=sensor_config,
    )

    # Should have: 1 status + 2 event + 1 run state = 4 sensors
    states = hass.states.async_all("sensor")
    expect(len(states)).to_equal(4)

    expect(hass.states.get("sensor.cam_events_last_hour")).not_.to_be_none()
    expect(hass.states.get("sensor.cam_events_last_day")).not_.to_be_none()

    expect(hass.states.get("sensor.cam_events")).to_be_none()
    expect(hass.states.get("sensor.cam_events_last_week")).to_be_none()
    expect(hass.states.get("sensor.cam_events_last_month")).to_be_none()


@test
async def default_conditions_only_all(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test default monitored_conditions is only 'all'."""
    monitors = [create_mock_monitor(name="Cam")]
    sensor_config = {"sensor": [{"platform": DOMAIN}]}
    await _setup_zm_with_sensors(
        hass,
        mock_zoneminder_client,
        single_server_config,
        monitors,
        freezer,
        sensor_config=sensor_config,
    )

    # Should have: 1 status + 1 event (all) + 1 run state = 3 sensors
    states = hass.states.async_all("sensor")
    expect(len(states)).to_equal(3)


@test
async def include_archived_flag(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test include_archived flag is passed correctly to get_events."""
    monitors = [create_mock_monitor(name="Cam")]
    sensor_config = {
        "sensor": [
            {
                "platform": DOMAIN,
                "include_archived": True,
                "monitored_conditions": ["all"],
            }
        ]
    }
    await _setup_zm_with_sensors(
        hass,
        mock_zoneminder_client,
        single_server_config,
        monitors,
        freezer,
        sensor_config=sensor_config,
    )

    monitors[0].get_events.assert_called_with(TimePeriod.ALL, True)


@test
async def sensor_count_calculation(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test correct number of sensors created per monitor and client.

    For each monitor: 1 status + N event sensors
    Plus: 1 run state sensor per client
    """
    monitors = [
        create_mock_monitor(monitor_id=1, name="Cam1"),
        create_mock_monitor(monitor_id=2, name="Cam2"),
    ]
    sensor_config = {
        "sensor": [
            {
                "platform": DOMAIN,
                "monitored_conditions": ["all", "hour"],
                "include_archived": False,
            }
        ]
    }
    await _setup_zm_with_sensors(
        hass,
        mock_zoneminder_client,
        single_server_config,
        monitors,
        freezer,
        sensor_config=sensor_config,
    )

    # 2 monitors * (1 status + 2 events) + 1 run state = 7
    expect(len(hass.states.async_all("sensor"))).to_equal(7)
