"""Tryke fixtures for the litterrobot integration."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from pylitterbot import Account, FeederRobot, LitterRobot3, LitterRobot4, Pet, Robot
from tryke import fixture

from .common import ACCOUNT_USER_ID, DOMAIN

from tests.common import load_json_object_fixture

ROBOT_DATA = load_json_object_fixture("litter_robot_3_data.json", DOMAIN)
ROBOT_4_DATA = load_json_object_fixture("litter_robot_4_data.json", DOMAIN)
FEEDER_ROBOT_DATA = load_json_object_fixture("feeder_robot_data.json", DOMAIN)
PET_DATA = load_json_object_fixture("pet_data.json", DOMAIN)


def create_mock_robot(
    robot_data: dict | None,
    account: Account,
    v4: bool,
    feeder: bool,
    side_effect: Any | None = None,
) -> Robot:
    """Create a mock Litter-Robot device."""
    if not robot_data:
        robot_data = {}

    if v4:
        robot = LitterRobot4(data={**ROBOT_4_DATA, **robot_data}, account=account)
    elif feeder:
        robot = FeederRobot(data={**FEEDER_ROBOT_DATA, **robot_data}, account=account)
        robot.set_gravity_mode = AsyncMock(side_effect=side_effect)
    else:
        robot = LitterRobot3(data={**ROBOT_DATA, **robot_data}, account=account)
    robot.start_cleaning = AsyncMock(side_effect=side_effect)
    robot.set_power_status = AsyncMock(side_effect=side_effect)
    robot.reset_waste_drawer = AsyncMock(side_effect=side_effect)
    robot.set_sleep_mode = AsyncMock(side_effect=side_effect)
    robot.set_night_light = AsyncMock(side_effect=side_effect)
    robot.set_panel_lockout = AsyncMock(side_effect=side_effect)
    robot.set_wait_time = AsyncMock(side_effect=side_effect)
    robot.refresh = AsyncMock(side_effect=side_effect)
    return robot


def create_mock_pet(
    pet_data: dict | None,
    account: Account,
    side_effect: Any | None = None,
) -> Pet:
    """Create a mock Pet."""
    if not pet_data:
        pet_data = {}

    pet = Pet(data={**PET_DATA, **pet_data}, session=account.session)
    pet.fetch_weight_history = AsyncMock(side_effect=side_effect)
    return pet


def create_mock_account(
    robot_data: dict | None = None,
    side_effect: Any | None = None,
    skip_robots: bool = False,
    v4: bool = False,
    feeder: bool = False,
    pet: bool = False,
) -> MagicMock:
    """Create a mock Litter-Robot account."""
    account = MagicMock(spec=Account)
    account.connect = AsyncMock()
    account.load_robots = AsyncMock()
    account.user_id = ACCOUNT_USER_ID
    account.robots = (
        []
        if skip_robots
        else [create_mock_robot(robot_data, account, v4, feeder, side_effect)]
    )
    account.get_robots = lambda robot_class: [
        robot for robot in account.robots if isinstance(robot, robot_class)
    ]
    account.pets = [create_mock_pet(PET_DATA, account, side_effect)] if pet else []
    return account


@fixture
def mock_account() -> MagicMock:
    """Mock a Litter-Robot account."""
    return create_mock_account()
