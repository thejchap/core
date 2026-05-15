"""The test for the Trafikverket train utils."""

from datetime import datetime

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components.trafikverket_train.util import next_departuredate
from homeassistant.const import WEEKDAYS
from homeassistant.util import dt as dt_util

from tests.hass_fixtures import freezer


@fixture
def _trigger_executor() -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
async def sensor_next(
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Test the Trafikverket Train utils."""
    expect(next_departuredate(WEEKDAYS)).to_equal(dt_util.now().date())
    freezer.move_to(datetime(2023, 12, 22))  # Friday
    expect(next_departuredate(["mon", "tue", "wed", "thu"])).to_equal(
        datetime(2023, 12, 25).date()
    )
    freezer.move_to(datetime(2023, 12, 25))  # Monday
    expect(next_departuredate(["fri", "sat", "sun"])).to_equal(
        datetime(2023, 12, 29).date()
    )
