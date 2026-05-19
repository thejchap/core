"""Test the sensor websocket API."""

from pytest_unordered import unordered
from tryke import Depends, fixture, test

from homeassistant.components.sensor.const import (
    DOMAIN,
    NON_NUMERIC_DEVICE_CLASSES,
    SensorDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fx,
)


@fixture
def _trigger_executor() -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@test
async def device_class_units(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test we can get supported units."""
    assert await async_setup_component(hass, DOMAIN, {})

    client = await hass_ws_client(hass)

    # Device class with units which sensor allows customizing & converting
    await client.send_json_auto_id(
        {
            "type": "sensor/device_class_convertible_units",
            "device_class": "speed",
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "units": [
            "Beaufort",
            "ft/s",
            "in/d",
            "in/h",
            "in/s",
            "km/h",
            "kn",
            "m/min",
            "m/s",
            "mm/d",
            "mm/h",
            "mm/s",
            "mph",
        ]
    }

    # Device class with units which include `None`
    await client.send_json_auto_id(
        {
            "type": "sensor/device_class_convertible_units",
            "device_class": "power_factor",
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {"units": ["%", None]}

    # Device class with units which sensor doesn't allow customizing & converting
    await client.send_json_auto_id(
        {
            "type": "sensor/device_class_convertible_units",
            "device_class": "pm1",
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {"units": []}

    # Unknown device class
    await client.send_json_auto_id(
        {
            "type": "sensor/device_class_convertible_units",
            "device_class": "kebabsås",
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {"units": []}


@test
async def numeric_device_classes(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test we can get numeric device classes."""
    numeric_device_classes = set(SensorDeviceClass) - NON_NUMERIC_DEVICE_CLASSES

    assert await async_setup_component(hass, DOMAIN, {})

    client = await hass_ws_client(hass)

    # Device class with units which sensor allows customizing & converting
    await client.send_json_auto_id({"type": "sensor/numeric_device_classes"})
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "numeric_device_classes": unordered(list(numeric_device_classes))
    }
