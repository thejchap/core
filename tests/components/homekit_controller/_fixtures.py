"""Tryke fixtures for the homekit_controller integration."""

from collections.abc import Callable, Generator
import datetime
from unittest.mock import MagicMock, patch

from aiohomekit.testing import FakeController
from freezegun import freeze_time
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, fixture

from homeassistant.util import dt as dt_util

from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def freeze_time_in_future() -> Generator[FrozenDateTimeFactory]:
    """Freeze time at a known point."""
    now = dt_util.utcnow()
    start_dt = datetime.datetime(now.year + 1, 1, 1, 0, 0, 0, tzinfo=now.tzinfo)
    with freeze_time(start_dt) as frozen_time:
        yield frozen_time


@fixture
def controller() -> Generator[FakeController]:
    """Replace aiohomekit.Controller with a FakeController."""
    instance = FakeController()
    with patch(
        "homeassistant.components.homekit_controller.utils.Controller",
        return_value=instance,
    ):
        yield instance


@fixture
def get_next_aid() -> Generator[Callable[[], int]]:
    """Generate a function that returns increasing accessory ids."""
    id_counter = 0

    def _get_id() -> int:
        nonlocal id_counter
        id_counter += 1
        return id_counter

    yield _get_id


@fixture
def hkc_mock_zeroconf(
    _zeroconf: MagicMock = Depends(mock_async_zeroconf),
) -> MagicMock:
    """Auto mock zeroconf."""
    return _zeroconf
