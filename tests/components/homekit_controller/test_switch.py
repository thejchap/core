"""Basic checks for HomeKitSwitch."""

from collections.abc import Callable
from unittest.mock import MagicMock

from aiohomekit.model import Accessory
from aiohomekit.model.characteristics import CharacteristicsTypes
from aiohomekit.model.services import ServicesTypes
from aiohomekit.testing import FakeController
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from ._fixtures import (
    controller,
    freeze_time_in_future,
    get_next_aid,
    hkc_mock_zeroconf,
)
from .common import setup_test_component

from tests.hass_fixtures import (
    hass as hass_fixture,
    mock_bleak_scanner_start,
    mock_bluetooth_adapters,
    mock_network,
)


def create_switch_service(accessory: Accessory) -> None:
    """Define outlet characteristics."""
    service = accessory.add_service(ServicesTypes.OUTLET)

    on_char = service.add_char(CharacteristicsTypes.ON)
    on_char.value = False

    outlet_in_use = service.add_char(CharacteristicsTypes.OUTLET_IN_USE)
    outlet_in_use.value = False


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bt_adapters: None = Depends(mock_bluetooth_adapters),
    _bleak: MagicMock = Depends(mock_bleak_scanner_start),
    _zeroconf: MagicMock = Depends(hkc_mock_zeroconf),
    _frozen: object = Depends(freeze_time_in_future),
) -> None:
    """Module-level fixture anchor."""


@test
async def switch_read_outlet_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _controller: FakeController = Depends(controller),
    next_aid: Callable[[], int] = Depends(get_next_aid),
) -> None:
    """Test that we can read the state of a HomeKit outlet accessory."""
    helper = await setup_test_component(hass, next_aid(), create_switch_service)

    # Initial state is off, outlet not in use
    switch_1 = await helper.poll_and_get_state()
    expect(switch_1.state).to_equal("off")
    expect(switch_1.attributes["outlet_in_use"]).to_be(False)


@test.skip("port deferred - sibling test")
async def switch_change_outlet_state() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def faucet_change_active_state() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def faucet_read_active_state() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def valve_change_active_state() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def valve_read_state() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def char_switch_change_state() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def char_switch_read_state() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def airplay_enable_switch_change_state() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def airplay_enable_switch_read_state() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def migrate_unique_id() -> None:
    """Stub."""
