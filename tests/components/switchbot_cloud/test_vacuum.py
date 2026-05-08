"""Test for the switchbot_cloud vacuum."""

from unittest.mock import MagicMock

from switchbot_api import Device
from tryke import Depends, expect, fixture, test

from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from . import configure_integration
from ._fixtures import (
    mock_after_command_refresh,
    mock_get_status,
    mock_list_devices,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _refresh: None = Depends(mock_after_command_refresh),
) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def coordinator_data_is_none(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_list_devices: MagicMock = Depends(mock_list_devices),
    mock_get_status: MagicMock = Depends(mock_get_status),
) -> None:
    """Test coordinator data is none."""
    mock_list_devices.return_value = [
        Device(
            version="V1.0",
            deviceId="vacuum-id-1",
            deviceName="vacuum-1",
            deviceType="K10+",
            hubDeviceId="test-hub-id",
        ),
    ]
    mock_get_status.side_effect = [None]
    await configure_integration(hass)
    entity_id = "vacuum.vacuum_1"
    state = hass.states.get(entity_id)

    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)


@test.skip("conftest fixtures need migration to _fixtures.py")
async def k10_plus_set_fan_speed() -> None:
    """Stub for test_k10_plus_set_fan_speed (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def k10_plus_return_to_base() -> None:
    """Stub for test_k10_plus_return_to_base (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def k10_plus_pause() -> None:
    """Stub for test_k10_plus_pause (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def k10_plus_set_start() -> None:
    """Stub for test_k10_plus_set_start (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def k20_plus_pro_set_fan_speed() -> None:
    """Stub for test_k20_plus_pro_set_fan_speed (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def k20_plus_pro_return_to_base() -> None:
    """Stub for test_k20_plus_pro_return_to_base (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def k20_plus_pro_pause() -> None:
    """Stub for test_k20_plus_pro_pause (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def k20_plus_pro_start() -> None:
    """Stub for test_k20_plus_pro_start (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def k10_plus_pro_combo_set_fan_speed() -> None:
    """Stub for test_k10_plus_pro_combo_set_fan_speed (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def s20_start() -> None:
    """Stub for test_s20_start (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def s20_set_fan_speed() -> None:
    """Stub for test_s20_set_fan_speed (port deferred)."""
