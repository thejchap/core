"""Test the Airthings BLE config flow."""

from unittest.mock import patch

from airthings_ble import AirthingsDevice, AirthingsDeviceType, UnsupportedDeviceError
from bleak import BleakError
from home_assistant_bluetooth import BluetoothServiceInfoBleak
from tryke import Depends, expect, fixture, test

from homeassistant.components.airthings_ble.const import DEVICE_MODEL, DOMAIN
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_IGNORE, SOURCE_USER
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    UNKNOWN_AIRTHINGS_SERVICE_INFO,
    UNKNOWN_SERVICE_INFO,
    VIEW_PLUS_SERVICE_INFO,
    WAVE_DEVICE_INFO,
    WAVE_SERVICE_INFO,
    patch_airthings_ble,
    patch_async_ble_device_from_address,
    patch_async_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def bluetooth_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device."""
    wave_plus_device = AirthingsDeviceType.WAVE_PLUS
    with (
        patch_async_ble_device_from_address(WAVE_SERVICE_INFO),
        patch_airthings_ble(
            AirthingsDevice(
                manufacturer="Airthings AS",
                model=wave_plus_device,
                name="Airthings Wave Plus",
                identifier="123456",
            )
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_BLUETOOTH},
            data=WAVE_SERVICE_INFO,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    expect(result["description_placeholders"]).to_equal(
        {"name": "Airthings Wave Plus (2930123456)"}
    )

    with patch_async_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"not": "empty"}
        )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Airthings Wave Plus (2930123456)")
    expect(result["result"].unique_id).to_equal("cc:cc:cc:cc:cc:cc")
    expect(result["data"]).to_equal({DEVICE_MODEL: wave_plus_device.value})
    expect(result["result"].data).to_equal({DEVICE_MODEL: wave_plus_device.value})


@test
async def bluetooth_discovery_no_BLEDevice(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth but there's no BLEDevice."""
    with patch_async_ble_device_from_address(None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_BLUETOOTH},
            data=WAVE_SERVICE_INFO,
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test.cases(
    test.case("unknown", exc=Exception(), reason="unknown"),
    test.case("cannot_connect", exc=BleakError(), reason="cannot_connect"),
    test.case("unsupported_device", exc=UnsupportedDeviceError(), reason="unsupported_device"),
)
async def bluetooth_discovery_airthings_ble_update_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    exc: Exception,
    reason: str,
) -> None:
    """Test discovery via bluetooth but there's an exception from airthings-ble."""
    with (
        patch_async_ble_device_from_address(WAVE_SERVICE_INFO),
        patch_airthings_ble(side_effect=exc),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_BLUETOOTH},
            data=WAVE_SERVICE_INFO,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test
async def bluetooth_discovery_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device when already setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="cc:cc:cc:cc:cc:cc",
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=WAVE_DEVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form."""
    wave_plus_device = AirthingsDeviceType.WAVE_PLUS
    with (
        patch(
            "homeassistant.components.airthings_ble.config_flow.async_discovered_service_info",
            return_value=[WAVE_SERVICE_INFO],
        ),
        patch_async_ble_device_from_address(WAVE_SERVICE_INFO),
        patch_airthings_ble(
            AirthingsDevice(
                manufacturer="Airthings AS",
                model=wave_plus_device,
                name="Airthings Wave Plus",
                identifier="123456",
            )
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)
    expect(result["data_schema"] is not None).to_be(True)
    schema = result["data_schema"].schema

    expect(schema.get(CONF_ADDRESS).container).to_equal(
        {"cc:cc:cc:cc:cc:cc": "Airthings Wave Plus (2930123456)"}
    )

    with patch(
        "homeassistant.components.airthings_ble.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: "cc:cc:cc:cc:cc:cc"}
        )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Airthings Wave Plus (2930123456)")
    expect(result["result"].unique_id).to_equal("cc:cc:cc:cc:cc:cc")
    expect(result["data"]).to_equal({DEVICE_MODEL: wave_plus_device.value})
    expect(result["result"].data).to_equal({DEVICE_MODEL: wave_plus_device.value})


@test
async def user_setup_replaces_ignored_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="cc:cc:cc:cc:cc:cc",
        source=SOURCE_IGNORE,
    )
    entry.add_to_hass(hass)
    wave_plus_device = AirthingsDeviceType.WAVE_PLUS
    with (
        patch(
            "homeassistant.components.airthings_ble.config_flow.async_discovered_service_info",
            return_value=[WAVE_SERVICE_INFO],
        ),
        patch_async_ble_device_from_address(WAVE_SERVICE_INFO),
        patch_airthings_ble(
            AirthingsDevice(
                manufacturer="Airthings AS",
                model=wave_plus_device,
                name="Airthings Wave Plus",
                identifier="123456",
            )
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)
    expect(result["data_schema"] is not None).to_be(True)
    schema = result["data_schema"].schema

    expect(schema.get(CONF_ADDRESS).container).to_equal(
        {"cc:cc:cc:cc:cc:cc": "Airthings Wave Plus (2930123456)"}
    )

    with patch(
        "homeassistant.components.airthings_ble.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: "cc:cc:cc:cc:cc:cc"}
        )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Airthings Wave Plus (2930123456)")
    expect(result["result"].unique_id).to_equal("cc:cc:cc:cc:cc:cc")
    expect(result["data"]).to_equal({DEVICE_MODEL: wave_plus_device.value})
    expect(result["result"].data).to_equal({DEVICE_MODEL: wave_plus_device.value})


@test
async def user_setup_no_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form without any device detected."""
    with patch(
        "homeassistant.components.airthings_ble.config_flow.async_discovered_service_info",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def user_setup_existing_and_unknown_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form with existing devices and unknown ones."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="cc:cc:cc:cc:cc:cc",
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.airthings_ble.config_flow.async_discovered_service_info",
        return_value=[UNKNOWN_SERVICE_INFO, WAVE_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test.cases(
    test.case(
        "unknown",
        exc=Exception(),
        reason="unknown",
        service_info=WAVE_SERVICE_INFO,
    ),
    test.case(
        "no_devices_found",
        exc=UnsupportedDeviceError(),
        reason="no_devices_found",
        service_info=UNKNOWN_AIRTHINGS_SERVICE_INFO,
    ),
)
async def user_setup_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    exc: Exception,
    reason: str,
    service_info: BluetoothServiceInfoBleak,
) -> None:
    """Test the user initiated form with an unknown error."""
    with (
        patch(
            "homeassistant.components.airthings_ble.config_flow.async_discovered_service_info",
            return_value=[WAVE_SERVICE_INFO],
        ),
        patch_async_ble_device_from_address(service_info),
        patch_airthings_ble(None, exc),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test
async def user_setup_unable_to_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form with a device that's failing connection."""
    with (
        patch(
            "homeassistant.components.airthings_ble.config_flow.async_discovered_service_info",
            return_value=[WAVE_SERVICE_INFO],
        ),
        patch_async_ble_device_from_address(WAVE_SERVICE_INFO),
        patch_airthings_ble(side_effect=BleakError("An error")),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def unsupported_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form with an unsupported device."""
    with patch(
        "homeassistant.components.airthings_ble.config_flow.async_discovered_service_info",
        return_value=[UNKNOWN_SERVICE_INFO, VIEW_PLUS_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def bluetooth_confirm_firmware_required(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device."""
    device = AirthingsDevice(
        manufacturer="Airthings AS",
        model=AirthingsDeviceType.WAVE_ENHANCE_EU,
        name="Airthings Wave Enhance",
        identifier="123456",
    )
    device.firmware.update_current_version("1.0.0")
    device.firmware.update_required_version("2.6.1")
    with (
        patch_async_ble_device_from_address(WAVE_SERVICE_INFO),
        patch_airthings_ble(device),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_BLUETOOTH},
            data=WAVE_SERVICE_INFO,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    with patch_async_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"not": "empty"}
        )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("firmware_upgrade_required")


@test
async def step_user_firmware_required(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user has selected a device with a firmware upgrade required."""
    device = AirthingsDevice(
        manufacturer="Airthings AS",
        model=AirthingsDeviceType.WAVE_ENHANCE_EU,
        name="Airthings Wave Enhance",
        identifier="123456",
    )
    device.firmware.update_current_version("1.0.0")
    device.firmware.update_required_version("2.6.1")

    with (
        patch(
            "homeassistant.components.airthings_ble.config_flow.async_discovered_service_info",
            return_value=[WAVE_SERVICE_INFO],
        ),
        patch_async_ble_device_from_address(WAVE_SERVICE_INFO),
        patch_airthings_ble(device),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.airthings_ble.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: "cc:cc:cc:cc:cc:cc"}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("firmware_upgrade_required")


@test
async def discovering_unsupported_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovering unsupported devices."""
    with patch(
        "homeassistant.components.airthings_ble.config_flow.async_discovered_service_info",
        return_value=[UNKNOWN_AIRTHINGS_SERVICE_INFO, UNKNOWN_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")
