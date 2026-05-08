"""Test all functions related to the basic accessory implementation (tryke port).

Smaller / leaf-level tests are ported here. The battery / linked-battery
matrix and call_service tests remain skip-stubbed pending a per-test
review (they exercise async_update_state / state-dispatch internals that
warrant separate triage).
"""

from __future__ import annotations

from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.homekit.accessories import (
    HomeAccessory,
    HomeBridge,
    HomeDriver,
)
from homeassistant.components.homekit.const import (
    ATTR_INTEGRATION,
    BRIDGE_MODEL,
    BRIDGE_NAME,
    BRIDGE_SERIAL_NUMBER,
    CHAR_FIRMWARE_REVISION,
    CHAR_HARDWARE_REVISION,
    CHAR_MANUFACTURER,
    CHAR_MODEL,
    CHAR_NAME,
    CHAR_SERIAL_NUMBER,
    EMPTY_MAC,
    MANUFACTURER,
    SERV_ACCESSORY_INFO,
)
from homeassistant.components.homekit.iidmanager import AccessoryIIDStorage
from homeassistant.components.homekit.util import format_version
from homeassistant.const import (
    ATTR_HW_VERSION,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_SW_VERSION,
    __version__ as hass_version,
)
from homeassistant.core import HomeAssistant

from tests.components.homekit._fixtures import (
    hk_driver as hk_driver_fixture,
    iid_storage as iid_storage_fixture,
)
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (see PATTERNS.md)."""
    return hass


@test
async def accessory_cancels_track_state_change_on_stop(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Ensure homekit state changed listeners are unsubscribed on reload."""
    entity_id = "sensor.accessory"
    hass.states.async_set(entity_id, None)
    acc = HomeAccessory(
        hass, hk_driver, "Home Accessory", entity_id, 2, {"platform": "isy994"}
    )
    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ):
        acc.run()
    await acc.stop()


@test
async def accessory_with_missing_basic_service_info(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test HomeAccessory class fills in defaults when info is missing."""
    entity_id = "sensor.accessory"
    hass.states.async_set(entity_id, "on")
    acc = HomeAccessory(
        hass,
        hk_driver,
        "Home Accessory",
        entity_id,
        3,
        {
            ATTR_MODEL: None,
            ATTR_MANUFACTURER: None,
            ATTR_SW_VERSION: None,
            ATTR_INTEGRATION: None,
        },
    )
    serv = acc.get_service(SERV_ACCESSORY_INFO)
    expect(serv.get_characteristic(CHAR_NAME).value).to_equal("Home Accessory")
    expect(serv.get_characteristic(CHAR_MANUFACTURER).value).to_equal(
        "Home Assistant Sensor"
    )
    expect(serv.get_characteristic(CHAR_MODEL).value).to_equal("Sensor")
    expect(serv.get_characteristic(CHAR_SERIAL_NUMBER).value).to_equal(entity_id)
    expect(
        format_version(hass_version).startswith(
            serv.get_characteristic(CHAR_FIRMWARE_REVISION).value
        )
    ).to_be(True)
    expect(isinstance(acc.to_HAP(), dict)).to_be(True)


@test
async def accessory_with_hardware_revision(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test HomeAccessory class with hardware revision."""
    entity_id = "sensor.accessory"
    hass.states.async_set(entity_id, "on")
    acc = HomeAccessory(
        hass,
        hk_driver,
        "Home Accessory",
        entity_id,
        3,
        {
            ATTR_MODEL: None,
            ATTR_MANUFACTURER: None,
            ATTR_SW_VERSION: None,
            ATTR_HW_VERSION: "1.2.3",
            ATTR_INTEGRATION: None,
        },
    )
    acc.driver = hk_driver
    serv = acc.get_service(SERV_ACCESSORY_INFO)
    expect(serv.get_characteristic(CHAR_NAME).value).to_equal("Home Accessory")
    expect(serv.get_characteristic(CHAR_MANUFACTURER).value).to_equal(
        "Home Assistant Sensor"
    )
    expect(serv.get_characteristic(CHAR_MODEL).value).to_equal("Sensor")
    expect(serv.get_characteristic(CHAR_SERIAL_NUMBER).value).to_equal(entity_id)
    expect(
        format_version(hass_version).startswith(
            serv.get_characteristic(CHAR_FIRMWARE_REVISION).value
        )
    ).to_be(True)
    expect(serv.get_characteristic(CHAR_HARDWARE_REVISION).value).to_equal("1.2.3")
    expect(isinstance(acc.to_HAP(), dict)).to_be(True)


@test
async def home_bridge(
    _t: HomeAssistant = Depends(_trigger_executor),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test HomeBridge class."""
    bridge = HomeBridge("hass", hk_driver, BRIDGE_NAME)
    expect(bridge.hass).to_equal("hass")
    expect(bridge.display_name).to_equal(BRIDGE_NAME)
    expect(bridge.category).to_be(2)  # Category.BRIDGE
    expect(len(bridge.services)).to_be(2)
    serv = bridge.services[0]  # SERV_ACCESSORY_INFO
    expect(serv.display_name).to_equal(SERV_ACCESSORY_INFO)
    expect(serv.get_characteristic(CHAR_NAME).value).to_equal(BRIDGE_NAME)
    expect(
        format_version(hass_version).startswith(
            serv.get_characteristic(CHAR_FIRMWARE_REVISION).value
        )
    ).to_be(True)
    expect(serv.get_characteristic(CHAR_MANUFACTURER).value).to_equal(MANUFACTURER)
    expect(serv.get_characteristic(CHAR_MODEL).value).to_equal(BRIDGE_MODEL)
    expect(serv.get_characteristic(CHAR_SERIAL_NUMBER).value).to_equal(
        BRIDGE_SERIAL_NUMBER
    )


@test
async def home_bridge_setup_message(
    _t: HomeAssistant = Depends(_trigger_executor),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test HomeBridge setup message."""
    bridge = HomeBridge("hass", hk_driver, "test_name")
    expect(bridge.display_name).to_equal("test_name")
    expect(len(bridge.services)).to_be(2)
    bridge.setup_message()


@test
async def home_driver(
    _t: HomeAssistant = Depends(_trigger_executor),
    iid_storage: AccessoryIIDStorage = Depends(iid_storage_fixture),
) -> None:
    """Test HomeDriver class."""
    ip_address = "127.0.0.1"
    port = 51826
    path = ".homekit.state"
    pin = b"123-45-678"

    with patch("pyhap.accessory_driver.AccessoryDriver.__init__") as mock_driver:
        driver = HomeDriver(
            "hass",
            "entry_id",
            "name",
            "title",
            iid_storage=iid_storage,
            address=ip_address,
            port=port,
            persist_file=path,
        )

    mock_driver.assert_called_with(
        address=ip_address, port=port, persist_file=path, mac=EMPTY_MAC
    )
    driver.state = Mock(pincode=pin, paired=False)
    xhm_uri_mock = Mock(return_value="X-HM://0")
    driver.accessory = Mock(display_name="any", xhm_uri=xhm_uri_mock)

    # pair
    with (
        patch("pyhap.accessory_driver.AccessoryDriver.pair") as mock_pair,
        patch(
            "homeassistant.components.homekit.accessories.async_dismiss_setup_message"
        ) as mock_dismiss_msg,
    ):
        driver.pair("client_uuid", "client_public", b"1")

    mock_pair.assert_called_with("client_uuid", "client_public", b"1")
    mock_dismiss_msg.assert_called_with("hass", "entry_id")

    # unpair
    with (
        patch("pyhap.accessory_driver.AccessoryDriver.unpair") as mock_unpair,
        patch(
            "homeassistant.components.homekit.accessories.async_show_setup_message"
        ) as mock_show_msg,
    ):
        driver.unpair("client_uuid")

    mock_unpair.assert_called_with("client_uuid")
    expect(mock_show_msg.called).to_be(True)


@test.skip("port deferred — large async test_home_accessory body (~130 LOC)")
async def home_accessory() -> None:
    """Stub for test_home_accessory."""


@test.skip("port deferred — battery service test exercises HomeAccessory state-dispatch internals")
async def battery_service() -> None:
    """Stub for test_battery_service."""


@test.skip("port deferred — linked battery sensor test exercises state-dispatch internals")
async def linked_battery_sensor() -> None:
    """Stub for test_linked_battery_sensor."""


@test.skip("port deferred — linked battery charging sensor test exercises state-dispatch internals")
async def linked_battery_charging_sensor() -> None:
    """Stub for test_linked_battery_charging_sensor."""


@test.skip("port deferred — linked battery + charging sensor combination test")
async def linked_battery_sensor_and_linked_battery_charging_sensor() -> None:
    """Stub for test_linked_battery_sensor_and_linked_battery_charging_sensor."""


@test.skip("port deferred — missing linked battery charging sensor test")
async def missing_linked_battery_charging_sensor() -> None:
    """Stub for test_missing_linked_battery_charging_sensor."""


@test.skip("port deferred — missing linked battery sensor test")
async def missing_linked_battery_sensor() -> None:
    """Stub for test_missing_linked_battery_sensor."""


@test.skip("port deferred — battery_appears_after_startup state-dispatch test")
async def battery_appears_after_startup() -> None:
    """Stub for test_battery_appears_after_startup."""


@test.skip("port deferred — call_service test exercises HomeAssistant service dispatch")
async def call_service() -> None:
    """Stub for test_call_service."""
