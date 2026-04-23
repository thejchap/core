"""Tryke fixtures for Litter-Robot config_flow tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from pylitterbot import Account, LitterRobot3
from tryke import fixture

from tests.common import load_json_object_fixture

from .common import ACCOUNT_USER_ID, DOMAIN

ROBOT_DATA = load_json_object_fixture("litter_robot_3_data.json", DOMAIN)


@fixture
def mock_account() -> MagicMock:
    """Mock a Litter-Robot account."""
    account = MagicMock(spec=Account)
    account.connect = AsyncMock()
    account.load_robots = AsyncMock()
    account.user_id = ACCOUNT_USER_ID
    robot = LitterRobot3(data=ROBOT_DATA, account=account)
    robot.start_cleaning = AsyncMock()
    robot.set_power_status = AsyncMock()
    robot.reset_waste_drawer = AsyncMock()
    robot.set_sleep_mode = AsyncMock()
    robot.set_night_light = AsyncMock()
    robot.set_panel_lockout = AsyncMock()
    robot.set_wait_time = AsyncMock()
    robot.refresh = AsyncMock()
    account.robots = [robot]
    account.get_robots = lambda robot_class: [
        r for r in account.robots if isinstance(r, robot_class)
    ]
    account.pets = []
    return account
