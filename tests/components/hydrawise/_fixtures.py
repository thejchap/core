"""Tryke fixtures for the Hydrawise integration."""

from collections.abc import Generator
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from pydrawise.schema import (
    Controller,
    ControllerHardware,
    ControllerWaterUseSummary,
    CustomSensorTypeEnum,
    LocalizedValueType,
    ScheduledZoneRun,
    ScheduledZoneRuns,
    Sensor,
    SensorModel,
    SensorStatus,
    UnitsSummary,
    User,
    Zone,
)
from tryke import Depends, fixture

from homeassistant.util import dt as dt_util


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.hydrawise.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def user() -> User:
    """Hydrawise User fixture."""
    return User(
        customer_id=12345,
        email="asdf@asdf.com",
        units=UnitsSummary(units_name="imperial"),
    )


@fixture
def controller() -> Controller:
    """Hydrawise Controller fixture."""
    return Controller(
        id=52496,
        name="Home Controller",
        hardware=ControllerHardware(serial_number="0310b36090"),
        last_contact_time=datetime.fromtimestamp(1693292420),
        online=True,
        sensors=[],
    )


@fixture
def sensors() -> list[Sensor]:
    """Hydrawise sensor fixtures."""
    return [
        Sensor(
            id=337844,
            name="Rain sensor ",
            model=SensorModel(
                id=3318,
                name="Rain Sensor (normally closed wire)",
                active=True,
                off_level=1,
                off_timer=0,
                divisor=0.0,
                flow_rate=0.0,
                sensor_type=CustomSensorTypeEnum.LEVEL_CLOSED,
            ),
            status=SensorStatus(water_flow=None, active=False),
        ),
        Sensor(
            id=337845,
            name="Flow meter",
            model=SensorModel(
                id=3324,
                name="1, 1½ or 2 inch NPT Flow Meter",
                active=True,
                off_level=0,
                off_timer=0,
                divisor=0.52834,
                flow_rate=3.7854,
                sensor_type=CustomSensorTypeEnum.FLOW,
            ),
            status=SensorStatus(
                water_flow=LocalizedValueType(value=577.0044752010709, unit="gal"),
                active=False,
            ),
        ),
    ]


@fixture
def zones() -> list[Zone]:
    """Hydrawise zone fixtures."""
    return [
        Zone(
            name="Zone One",
            id=5965394,
            scheduled_runs=ScheduledZoneRuns(
                summary="",
                current_run=None,
                next_run=ScheduledZoneRun(
                    start_time=dt_util.now() + timedelta(seconds=330597),
                    end_time=dt_util.now()
                    + timedelta(seconds=330597)
                    + timedelta(seconds=1800),
                    normal_duration=timedelta(seconds=1800),
                    duration=timedelta(seconds=1800),
                ),
            ),
        ),
        Zone(
            name="Zone Two",
            id=5965395,
            scheduled_runs=ScheduledZoneRuns(
                current_run=ScheduledZoneRun(remaining_time=timedelta(seconds=1788))
            ),
        ),
    ]


@fixture
def controller_water_use_summary() -> ControllerWaterUseSummary:
    """Mock water use summary for the controller."""
    return ControllerWaterUseSummary(
        total_use=345.6,
        total_active_use=332.6,
        total_inactive_use=13.0,
        active_use_by_zone_id={5965394: 120.1, 5965395: 0.0},
        total_active_time=timedelta(seconds=123),
        active_time_by_zone_id={5965394: timedelta(seconds=123), 5965395: timedelta()},
        unit="gal",
    )


@fixture
def mock_pydrawise(
    user: User = Depends(user),
    controller: Controller = Depends(controller),
    zones: list[Zone] = Depends(zones),
    sensors: list[Sensor] = Depends(sensors),
    controller_water_use_summary: ControllerWaterUseSummary = Depends(
        controller_water_use_summary
    ),
) -> Generator[AsyncMock]:
    """Mock Hydrawise."""
    with patch("pydrawise.hybrid.HybridClient", autospec=True) as mock_pydrawise:
        user.controllers = [controller]
        controller.sensors = sensors
        mock_pydrawise.return_value.get_user.return_value = user
        mock_pydrawise.return_value.get_zones.return_value = zones
        mock_pydrawise.return_value.get_water_use_summary.return_value = (
            controller_water_use_summary
        )
        yield mock_pydrawise.return_value


@fixture
def mock_auth() -> Generator[AsyncMock]:
    """Mock pydrawise HybridAuth."""
    with patch("pydrawise.auth.HybridAuth", autospec=True) as mock_auth:
        yield mock_auth.return_value
