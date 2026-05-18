"""Tryke fixtures for alarm_control_panel tests."""

from __future__ import annotations

from tryke import fixture

from .common import MockAlarm


@fixture
def mock_alarm_control_panel_entities() -> dict[str, MockAlarm]:
    """Mock Alarm control panel class."""
    return {
        "arm_code": MockAlarm(
            name="Alarm arm code",
            code_arm_required=True,
            unique_id="unique_arm_code",
        ),
        "no_arm_code": MockAlarm(
            name="Alarm no arm code",
            code_arm_required=False,
            unique_id="unique_no_arm_code",
        ),
    }
