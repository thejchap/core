"""Tests for the registry."""

from typing import Any

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.core import CoreState, HomeAssistant
from homeassistant.helpers import storage
from homeassistant.helpers.registry import SAVE_DELAY, SAVE_DELAY_LONG, BaseRegistry

from tests.common import async_fire_time_changed
from tests.hass_fixtures import freezer, hass, hass_storage


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


class SampleRegistry(BaseRegistry):
    """Class to hold a registry of X."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the registry."""
        self.hass = hass
        self._store = storage.Store(hass, 1, "test")
        self.save_calls = 0

    async def _async_load(self) -> None:
        """Load the registry."""

    def _data_to_save(self) -> dict[str, Any]:
        """Return data of registry to save."""
        self.save_calls += 1
        return {}


@test.cases(
    test.case("NOT_RUNNING", long_delay_state=CoreState.not_running),
    test.case("STARTING", long_delay_state=CoreState.starting),
    test.case("STOPPED", long_delay_state=CoreState.stopped),
    test.case("FINAL_WRITE", long_delay_state=CoreState.final_write),
)
async def async_schedule_save(
    long_delay_state: CoreState,
    hass: HomeAssistant = Depends(hass),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test saving the registry.

    If CoreState is not running, it should save with long delay.

    Storage will always save at final write if there is a
    write pending so we should not schedule a save in that case.
    """
    registry = SampleRegistry(hass)
    hass.set_state(long_delay_state)

    registry.async_schedule_save()
    freezer.tick(SAVE_DELAY)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(registry.save_calls).to_equal(0)

    freezer.tick(SAVE_DELAY_LONG)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(registry.save_calls).to_equal(1)

    hass.set_state(CoreState.running)
    registry.async_schedule_save()
    freezer.tick(SAVE_DELAY)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(registry.save_calls).to_equal(2)
