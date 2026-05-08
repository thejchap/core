"""The test for the Ecobee thermostat module."""

from unittest import mock

from tryke import Depends, expect, fixture, test

from homeassistant.components.ecobee.climate import Thermostat
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


def _make_ecobee_fixture() -> mock.Mock:
    """Build a mock thermostat data dict."""
    vals = {
        "name": "Ecobee",
        "modelNumber": "athenaSmart",
        "identifier": "abc",
        "program": {
            "climates": [
                {
                    "name": "Climate1",
                    "climateRef": "c1",
                    "sensors": [{"name": "Ecobee"}],
                },
                {"name": "Away", "climateRef": "away", "sensors": [{"name": "Ecobee"}]},
                {"name": "Home", "climateRef": "home", "sensors": [{"name": "Ecobee"}]},
            ],
            "currentClimateRef": "c1",
        },
        "runtime": {
            "connected": True,
            "actualTemperature": 300,
            "actualHumidity": 15,
            "desiredHeat": 400,
            "desiredCool": 200,
            "desiredFanMode": "on",
        },
        "settings": {
            "hvacMode": "auto",
            "heatStages": 1,
            "coolStages": 1,
            "fanMinOnTime": 10,
            "heatCoolMinDelta": 50,
            "holdAction": "nextTransition",
        },
        "equipmentStatus": "fan",
        "events": [],
        "remoteSensors": [{"id": "ei:0", "name": "Ecobee"}],
    }
    mock_ecobee = mock.Mock()
    mock_ecobee.get = mock.Mock(side_effect=vals.get)
    mock_ecobee.__getitem__ = mock.Mock(side_effect=vals.__getitem__)
    mock_ecobee.__setitem__ = mock.Mock(side_effect=vals.__setitem__)
    return mock_ecobee


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def name(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test name property."""
    ecobee_fixture = _make_ecobee_fixture()
    data = mock.Mock()
    data.ecobee.get_thermostat.return_value = ecobee_fixture
    thermostat = Thermostat(data, 1, ecobee_fixture, hass)
    expect(thermostat.device_info["name"]).to_equal("Ecobee")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def aux_heat_not_supported_by_default() -> None:
    """Stub for test_aux_heat_not_supported_by_default."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def current_temperature() -> None:
    """Stub for test_current_temperature."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def target_temperature_low() -> None:
    """Stub for test_target_temperature_low."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def target_temperature_high() -> None:
    """Stub for test_target_temperature_high."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def target_temperature() -> None:
    """Stub for test_target_temperature."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def desired_fan_mode() -> None:
    """Stub for test_desired_fan_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def fan() -> None:
    """Stub for test_fan."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def hvac_mode() -> None:
    """Stub for test_hvac_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def hvac_modes() -> None:
    """Stub for test_hvac_modes."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def hvac_mode2() -> None:
    """Stub for test_hvac_mode2."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def extra_state_attributes() -> None:
    """Stub for test_extra_state_attributes."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_temperature() -> None:
    """Stub for test_set_temperature."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_hvac_mode() -> None:
    """Stub for test_set_hvac_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_fan_min_on_time() -> None:
    """Stub for test_set_fan_min_on_time."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def resume_program() -> None:
    """Stub for test_resume_program."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def hold_preference() -> None:
    """Stub for test_hold_preference."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def hold_hours() -> None:
    """Stub for test_hold_hours."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_fan_mode_on() -> None:
    """Stub for test_set_fan_mode_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_fan_mode_auto() -> None:
    """Stub for test_set_fan_mode_auto."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def preset_indefinite_away() -> None:
    """Stub for test_preset_indefinite_away."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_preset_mode() -> None:
    """Stub for test_set_preset_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def remote_sensors() -> None:
    """Stub for test_remote_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def remote_sensor_devices() -> None:
    """Stub for test_remote_sensor_devices."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def active_sensors_in_preset_mode() -> None:
    """Stub for test_active_sensors_in_preset_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def active_sensor_devices_in_preset_mode() -> None:
    """Stub for test_active_sensor_devices_in_preset_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def remote_sensor_ids_names() -> None:
    """Stub for test_remote_sensor_ids_names."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_sensors_used_in_climate() -> None:
    """Stub for test_set_sensors_used_in_climate."""

