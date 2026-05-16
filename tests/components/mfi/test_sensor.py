"""The tests for the mFi sensor platform."""

from copy import deepcopy
from unittest import mock

from mficlient.client import FailedToLogin
import requests
from tryke import Depends, expect, fixture, test

from homeassistant.components import sensor as sensor_component
from homeassistant.components.mfi import sensor as mfi
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture

PLATFORM = mfi
COMPONENT = sensor_component
THING = "sensor"
GOOD_CONFIG = {
    "sensor": {
        "platform": "mfi",
        "host": "foo",
        "port": 6123,
        "username": "user",
        "password": "pass",
        "ssl": True,
        "verify_ssl": True,
    }
}


@fixture
def _trigger_executor() -> int:
    """Anchor fixture so async tests get an executor."""
    return 0


@test
async def setup_missing_config(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup with missing configuration."""
    with mock.patch("homeassistant.components.mfi.sensor.MFiClient") as mock_client:
        config = {"sensor": {"platform": "mfi"}}
        expect(await async_setup_component(hass, COMPONENT.DOMAIN, config)).to_be(True)
        expect(mock_client.called).to_be(False)


@test
async def setup_failed_login(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup with login failure."""
    with mock.patch("homeassistant.components.mfi.sensor.MFiClient") as mock_client:
        mock_client.side_effect = FailedToLogin
        expect(
            PLATFORM.setup_platform(hass, GOOD_CONFIG[COMPONENT.DOMAIN], None)
        ).to_be_falsy()


@test
async def setup_failed_connect(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup with connection failure."""
    with mock.patch("homeassistant.components.mfi.sensor.MFiClient") as mock_client:
        mock_client.side_effect = requests.exceptions.ConnectionError
        expect(
            PLATFORM.setup_platform(hass, GOOD_CONFIG[COMPONENT.DOMAIN], None)
        ).to_be_falsy()


@test
async def setup_minimum(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup with minimum configuration."""
    with mock.patch("homeassistant.components.mfi.sensor.MFiClient") as mock_client:
        config = deepcopy(GOOD_CONFIG)
        del config[THING]["port"]
        expect(await async_setup_component(hass, COMPONENT.DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()
        expect(mock_client.call_count).to_equal(1)
        expect(mock_client.call_args).to_equal(
            mock.call("foo", "user", "pass", port=6443, use_tls=True, verify=True)
        )


@test
async def setup_with_port(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup with port."""
    with mock.patch("homeassistant.components.mfi.sensor.MFiClient") as mock_client:
        expect(await async_setup_component(hass, COMPONENT.DOMAIN, GOOD_CONFIG)).to_be(
            True
        )
        await hass.async_block_till_done()
        expect(mock_client.call_count).to_equal(1)
        expect(mock_client.call_args).to_equal(
            mock.call("foo", "user", "pass", port=6123, use_tls=True, verify=True)
        )


@test
async def setup_with_tls_disabled(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup without TLS."""
    with mock.patch("homeassistant.components.mfi.sensor.MFiClient") as mock_client:
        config = deepcopy(GOOD_CONFIG)
        del config[THING]["port"]
        config[THING]["ssl"] = False
        config[THING]["verify_ssl"] = False
        expect(await async_setup_component(hass, COMPONENT.DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()
        expect(mock_client.call_count).to_equal(1)
        expect(mock_client.call_args).to_equal(
            mock.call("foo", "user", "pass", port=6080, use_tls=False, verify=False)
        )


@test
async def setup_adds_proper_devices(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if setup adds devices."""
    with (
        mock.patch("homeassistant.components.mfi.sensor.MFiClient") as mock_client,
        mock.patch(
            "homeassistant.components.mfi.sensor.MfiSensor", side_effect=mfi.MfiSensor
        ) as mock_sensor,
    ):
        ports = {
            i: mock.MagicMock(model=model, label=f"Port {i}", value=0)
            for i, model in enumerate(mfi.SENSOR_MODELS)
        }
        ports["bad"] = mock.MagicMock(model="notasensor")
        mock_client.return_value.get_devices.return_value = [
            mock.MagicMock(ports=ports)
        ]
        expect(await async_setup_component(hass, COMPONENT.DOMAIN, GOOD_CONFIG)).to_be(
            True
        )
        await hass.async_block_till_done()
        for ident, port in ports.items():
            if ident != "bad":
                mock_sensor.assert_any_call(port)
        expect(mock.call(ports["bad"], hass) in mock_sensor.mock_calls).to_be(False)


@fixture
def port() -> mock.MagicMock:
    """Port fixture."""
    return mock.MagicMock()


@fixture
def sensor(
    hass: HomeAssistant = Depends(hass_fixture),
    port: mock.MagicMock = Depends(port),
) -> mfi.MfiSensor:
    """Sensor fixture."""
    sensor = mfi.MfiSensor(port)
    sensor.hass = hass
    return sensor


@test
async def name(
    _trigger: int = Depends(_trigger_executor),
    port: mock.MagicMock = Depends(port),
    sensor: mfi.MfiSensor = Depends(sensor),
) -> None:
    """Test the name."""
    expect(port.label).to_equal(sensor.name)


@test
async def uom_temp(
    _trigger: int = Depends(_trigger_executor),
    port: mock.MagicMock = Depends(port),
    sensor: mfi.MfiSensor = Depends(sensor),
) -> None:
    """Test the UOM temperature."""
    port.tag = "temperature"
    expect(sensor.unit_of_measurement).to_equal(UnitOfTemperature.CELSIUS)
    expect(sensor.device_class).to_be(SensorDeviceClass.TEMPERATURE)


@test
async def uom_power(
    _trigger: int = Depends(_trigger_executor),
    port: mock.MagicMock = Depends(port),
    sensor: mfi.MfiSensor = Depends(sensor),
) -> None:
    """Test the UOEM power."""
    port.tag = "active_pwr"
    expect(sensor.unit_of_measurement).to_equal("Watts")
    expect(sensor.device_class).to_be_none()


@test
async def uom_digital(
    _trigger: int = Depends(_trigger_executor),
    port: mock.MagicMock = Depends(port),
    sensor: mfi.MfiSensor = Depends(sensor),
) -> None:
    """Test the UOM digital input."""
    port.model = "Input Digital"
    expect(sensor.unit_of_measurement).to_be_none()
    expect(sensor.device_class).to_be_none()


@test
async def uom_unknown(
    _trigger: int = Depends(_trigger_executor),
    port: mock.MagicMock = Depends(port),
    sensor: mfi.MfiSensor = Depends(sensor),
) -> None:
    """Test the UOM."""
    port.tag = "balloons"
    expect(sensor.unit_of_measurement).to_equal("balloons")
    expect(sensor.device_class).to_be_none()


@test
async def uom_uninitialized(
    _trigger: int = Depends(_trigger_executor),
    port: mock.MagicMock = Depends(port),
    sensor: mfi.MfiSensor = Depends(sensor),
) -> None:
    """Test that the UOM defaults if not initialized."""
    type(port).tag = mock.PropertyMock(side_effect=ValueError)
    expect(sensor.unit_of_measurement).to_be_none()
    expect(sensor.device_class).to_be_none()


@test
async def state_digital(
    _trigger: int = Depends(_trigger_executor),
    port: mock.MagicMock = Depends(port),
    sensor: mfi.MfiSensor = Depends(sensor),
) -> None:
    """Test the digital input."""
    port.model = "Input Digital"
    port.value = 0
    expect(sensor.state).to_equal(mfi.STATE_OFF)
    port.value = 1
    expect(sensor.state).to_equal(mfi.STATE_ON)
    port.value = 2
    expect(sensor.state).to_equal(mfi.STATE_ON)


@test
async def state_digits(
    _trigger: int = Depends(_trigger_executor),
    port: mock.MagicMock = Depends(port),
    sensor: mfi.MfiSensor = Depends(sensor),
) -> None:
    """Test the state of digits."""
    port.tag = "didyoucheckthedict?"
    port.value = 1.25
    with mock.patch.dict(mfi.DIGITS, {"didyoucheckthedict?": 1}):
        expect(sensor.state).to_equal(1.2)
    with mock.patch.dict(mfi.DIGITS, {}):
        expect(sensor.state).to_equal(1.0)


@test
async def state_uninitialized(
    _trigger: int = Depends(_trigger_executor),
    port: mock.MagicMock = Depends(port),
    sensor: mfi.MfiSensor = Depends(sensor),
) -> None:
    """Test the state of uninitialized sensorfs."""
    type(port).tag = mock.PropertyMock(side_effect=ValueError)
    expect(sensor.state).to_equal(mfi.STATE_OFF)


@test
async def update(
    _trigger: int = Depends(_trigger_executor),
    port: mock.MagicMock = Depends(port),
    sensor: mfi.MfiSensor = Depends(sensor),
) -> None:
    """Test the update."""
    sensor.update()
    expect(port.refresh.call_count).to_equal(1)
    expect(port.refresh.call_args).to_equal(mock.call())
