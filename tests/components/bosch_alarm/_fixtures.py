"""Tryke fixtures for bosch_alarm tests."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

from bosch_alarm_mode2.const import PANEL_FAMILY, PanelModel
from bosch_alarm_mode2.panel import Area, Door, Output, Point
from bosch_alarm_mode2.utils import Observable
from tryke import Depends, fixture

from homeassistant.components.bosch_alarm.const import CONF_USER_CODE, DOMAIN
from homeassistant.const import CONF_HOST, CONF_MODEL, CONF_PORT

from tests.common import MockConfigEntry


@fixture
def points() -> dict[int, AsyncMock]:
    """Define mocked points."""
    names = [
        "Window",
        "Door",
        "Motion Detector",
        "CO Detector",
        "Smoke Detector",
        "Glassbreak Sensor",
        "Bedroom",
    ]
    result: dict[int, AsyncMock] = {}
    for i, name in enumerate(names):
        mock = AsyncMock(spec=Point)
        mock.name = name
        mock.status_observer = AsyncMock(spec=Observable)
        mock.is_open.return_value = False
        mock.is_normal.return_value = True
        result[i] = mock
    return result


@fixture
def output() -> AsyncMock:
    """Define a mocked output."""
    mock = AsyncMock(spec=Output)
    mock.name = "Output A"
    mock.status_observer = AsyncMock(spec=Observable)
    mock.is_active.return_value = False
    return mock


@fixture
def door() -> AsyncMock:
    """Define a mocked door."""
    mock = AsyncMock(spec=Door)
    mock.name = "Main Door"
    mock.status_observer = AsyncMock(spec=Observable)
    mock.is_open.return_value = False
    mock.is_cycling.return_value = False
    mock.is_secured.return_value = False
    mock.is_locked.return_value = True
    return mock


@fixture
def area() -> AsyncMock:
    """Define a mocked area."""
    mock = AsyncMock(spec=Area)
    mock.name = "Area1"
    mock.status_observer = AsyncMock(spec=Observable)
    mock.alarm_observer = AsyncMock(spec=Observable)
    mock.ready_observer = AsyncMock(spec=Observable)
    mock.alarms = []
    mock.alarms_ids = []
    mock.faults = 0
    mock.all_ready = True
    mock.part_ready = True
    mock.is_triggered.return_value = False
    mock.is_disarmed.return_value = True
    mock.is_armed.return_value = False
    mock.is_arming.return_value = False
    mock.is_pending.return_value = False
    mock.is_part_armed.return_value = False
    mock.is_all_armed.return_value = False
    return mock


@fixture
def mock_panel_solution_3000(
    area: AsyncMock = Depends(area),
    door: AsyncMock = Depends(door),
    output: AsyncMock = Depends(output),
    points: dict[int, AsyncMock] = Depends(points),
) -> Generator[AsyncMock]:
    """Define a fixture to set up Bosch Alarm for solution_3000."""
    panel_model = PanelModel("Solution 3000", PANEL_FAMILY.SOLUTION)
    with (
        patch(
            "homeassistant.components.bosch_alarm.Panel", autospec=True
        ) as mock_panel,
        patch(
            "homeassistant.components.bosch_alarm.config_flow.Panel", new=mock_panel
        ),
    ):
        client = mock_panel.return_value
        client.areas = {1: area}
        client.doors = {1: door}
        client.outputs = {1: output}
        client.points = points
        client.model = panel_model
        client.faults = []
        client.events = []
        client.panel_faults_ids = []
        client.firmware_version = "1.0.0"
        client.protocol_version = "1.0.0"
        client.serial_number = None
        client.connection_status_observer = AsyncMock(spec=Observable)
        client.faults_observer = AsyncMock(spec=Observable)
        client.history_observer = AsyncMock(spec=Observable)
        yield client


@fixture
def mock_config_entry_solution_3000() -> MockConfigEntry:
    """Mock config entry for bosch alarm solution_3000."""
    extra: dict[str, Any] = {
        CONF_MODEL: "Solution 3000",
        CONF_USER_CODE: "1234",
    }
    data = {
        CONF_HOST: "0.0.0.0",
        CONF_PORT: 7700,
    } | extra
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=None,
        entry_id="01JQ917ACKQ33HHM7YCFXYZX51",
        data=data,
    )


@fixture
def disable_platform_only() -> Generator[None]:
    """Disable platforms to speed up tests."""
    with patch("homeassistant.components.bosch_alarm.PLATFORMS", []):
        yield
