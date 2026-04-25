"""Test the Medcom Inspector BLE config flow."""

from unittest.mock import patch

from bleak import BleakError
from medcom_ble import MedcomBleDevice
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.medcom_ble.const import DOMAIN
from homeassistant.config_entries import SOURCE_IGNORE
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    MEDCOM_DEVICE_INFO,
    MEDCOM_SERVICE_INFO,
    UNKNOWN_SERVICE_INFO,
    patch_async_ble_device_from_address,
    patch_async_setup_entry,
    patch_medcom_ble,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


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
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=MEDCOM_SERVICE_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    expect(result["description_placeholders"]).to_equal({"name": "InspectorBLE-D9A0"})

    with (
        patch_async_ble_device_from_address(MEDCOM_SERVICE_INFO),
        patch_medcom_ble(
            MedcomBleDevice(
                manufacturer="International Medcom",
                model="Inspector BLE",
                model_raw="Inspector-BLE",
                name="Inspector BLE",
                identifier="a0d95a570b00",
            )
        ),
    ):
        with patch_async_setup_entry():
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input={"not": "empty"}
            )
        await hass.async_block_till_done()
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("InspectorBLE-D9A0")
        expect(result["result"].unique_id).to_equal("a0:d9:5a:57:0b:00")


@test
async def bluetooth_discovery_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device when already setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="a0:d9:5a:57:0b:00",
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=MEDCOM_DEVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form."""
    with patch(
        "homeassistant.components.medcom_ble.config_flow.async_discovered_service_info",
        return_value=[MEDCOM_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)
    expect(result["data_schema"] is not None).to_be(True)
    schema = result["data_schema"].schema

    expect(schema.get(CONF_ADDRESS).container).to_equal(
        {"a0:d9:5a:57:0b:00": "InspectorBLE-D9A0"}
    )

    with (
        patch_async_ble_device_from_address(MEDCOM_SERVICE_INFO),
        patch_medcom_ble(
            MedcomBleDevice(
                manufacturer="International Medcom",
                model="Inspector BLE",
                model_raw="Inspector-BLE",
                name="Inspector BLE",
                identifier="a0d95a570b00",
            )
        ),
        patch(
            "homeassistant.components.medcom_ble.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: "a0:d9:5a:57:0b:00"}
        )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("InspectorBLE-D9A0")
    expect(result["result"].unique_id).to_equal("a0:d9:5a:57:0b:00")


@test
async def user_setup_no_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form without any device detected."""
    with patch(
        "homeassistant.components.medcom_ble.config_flow.async_discovered_service_info",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
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
        unique_id="00:cc:cc:cc:cc:cc",
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.medcom_ble.config_flow.async_discovered_service_info",
        return_value=[UNKNOWN_SERVICE_INFO, MEDCOM_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_be(None)
        expect(result["data_schema"] is not None).to_be(True)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: "a0:d9:5a:57:0b:00"}
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")


@test
async def user_setup_unknown_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form with only unknown devices."""
    with patch(
        "homeassistant.components.medcom_ble.config_flow.async_discovered_service_info",
        return_value=[UNKNOWN_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("no_devices_found")


@test
async def user_setup_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form with an unknown error."""
    with patch(
        "homeassistant.components.medcom_ble.config_flow.async_discovered_service_info",
        return_value=[MEDCOM_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)
    expect(result["data_schema"] is not None).to_be(True)

    with (
        patch_async_ble_device_from_address(MEDCOM_SERVICE_INFO),
        patch_medcom_ble(None, Exception()),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: "a0:d9:5a:57:0b:00"}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def user_setup_unable_to_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form with a device that's failing connection."""
    with patch(
        "homeassistant.components.medcom_ble.config_flow.async_discovered_service_info",
        return_value=[MEDCOM_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)
    expect(result["data_schema"] is not None).to_be(True)
    schema = result["data_schema"].schema

    expect(schema.get(CONF_ADDRESS).container).to_equal(
        {"a0:d9:5a:57:0b:00": "InspectorBLE-D9A0"}
    )

    with (
        patch_async_ble_device_from_address(MEDCOM_SERVICE_INFO),
        patch_medcom_ble(side_effect=BleakError("An error")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: "a0:d9:5a:57:0b:00"}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def user_setup_replaces_ignored_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="a0:d9:5a:57:0b:00",
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.medcom_ble.config_flow.async_discovered_service_info",
        return_value=[MEDCOM_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    # Verify the ignored device is in the dropdown.
    expect(
        "a0:d9:5a:57:0b:00" in result["data_schema"].schema[CONF_ADDRESS].container
    ).to_be(True)

    with (
        patch_async_ble_device_from_address(MEDCOM_SERVICE_INFO),
        patch_medcom_ble(
            MedcomBleDevice(
                manufacturer="International Medcom",
                model="Inspector BLE",
                model_raw="Inspector-BLE",
                name="Inspector BLE",
                identifier="a0d95a570b00",
            )
        ),
        patch(
            "homeassistant.components.medcom_ble.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: "a0:d9:5a:57:0b:00"}
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("InspectorBLE-D9A0")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("a0:d9:5a:57:0b:00")
