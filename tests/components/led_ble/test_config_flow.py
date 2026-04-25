"""Test the LED BLE Bluetooth config flow."""

from unittest.mock import patch

from bleak import BleakError
from led_ble import CharacteristicMissingError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.led_ble.const import DOMAIN
from homeassistant.config_entries import SOURCE_IGNORE
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    LED_BLE_DISCOVERY_INFO,
    NOT_LED_BLE_DISCOVERY_INFO,
    UNSUPPORTED_LED_BLE_DISCOVERY_INFO,
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
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def user_step_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step success path."""
    with patch(
        "homeassistant.components.led_ble.config_flow.async_discovered_service_info",
        return_value=[NOT_LED_BLE_DISCOVERY_INFO, LED_BLE_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with (
        patch("homeassistant.components.led_ble.config_flow.LEDBLE.update"),
        patch(
            "homeassistant.components.led_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(LED_BLE_DISCOVERY_INFO.name)
    expect(result2["data"]).to_equal({CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address})
    expect(result2["result"].unique_id).to_equal(LED_BLE_DISCOVERY_INFO.address)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_step_no_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step with no devices found."""
    with patch(
        "homeassistant.components.led_ble.config_flow.async_discovered_service_info",
        return_value=[NOT_LED_BLE_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def user_step_no_new_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step with only existing devices found."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address},
        unique_id=LED_BLE_DISCOVERY_INFO.address,
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.led_ble.config_flow.async_discovered_service_info",
        return_value=[LED_BLE_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def user_step_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step and we cannot connect."""
    with patch(
        "homeassistant.components.led_ble.config_flow.async_discovered_service_info",
        return_value=[LED_BLE_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.led_ble.config_flow.LEDBLE.update",
        side_effect=BleakError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    with (
        patch("homeassistant.components.led_ble.config_flow.LEDBLE.update"),
        patch(
            "homeassistant.components.led_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address},
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal(LED_BLE_DISCOVERY_INFO.name)
    expect(result3["data"]).to_equal({CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address})
    expect(result3["result"].unique_id).to_equal(LED_BLE_DISCOVERY_INFO.address)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_step_unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step with an unknown exception."""
    with patch(
        "homeassistant.components.led_ble.config_flow.async_discovered_service_info",
        return_value=[NOT_LED_BLE_DISCOVERY_INFO, LED_BLE_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.led_ble.config_flow.LEDBLE.update",
        side_effect=RuntimeError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "unknown"})

    with (
        patch("homeassistant.components.led_ble.config_flow.LEDBLE.update"),
        patch(
            "homeassistant.components.led_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address},
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal(LED_BLE_DISCOVERY_INFO.name)
    expect(result3["data"]).to_equal({CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address})
    expect(result3["result"].unique_id).to_equal(LED_BLE_DISCOVERY_INFO.address)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_step_not_supported(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step with a non supported device."""
    with patch(
        "homeassistant.components.led_ble.config_flow.async_discovered_service_info",
        return_value=[LED_BLE_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.led_ble.config_flow.LEDBLE.update",
        side_effect=CharacteristicMissingError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("not_supported")


@test
async def bluetooth_step_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth step success path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=LED_BLE_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with (
        patch("homeassistant.components.led_ble.config_flow.LEDBLE.update"),
        patch(
            "homeassistant.components.led_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(LED_BLE_DISCOVERY_INFO.name)
    expect(result2["data"]).to_equal({CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address})
    expect(result2["result"].unique_id).to_equal(LED_BLE_DISCOVERY_INFO.address)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def bluetooth_unsupported_model(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth step with an unsupported model path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=UNSUPPORTED_LED_BLE_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_supported")


@test
async def user_setup_replaces_ignored_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AA:BB:CC:DD:EE:FF",
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.led_ble.config_flow.async_discovered_service_info",
        return_value=[LED_BLE_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    # Verify the ignored device is in the dropdown
    expect(
        "AA:BB:CC:DD:EE:FF" in result["data_schema"].schema["address"].container
    ).to_be(True)

    with (
        patch("homeassistant.components.led_ble.config_flow.LEDBLE.update"),
        patch(
            "homeassistant.components.led_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(LED_BLE_DISCOVERY_INFO.name)
    expect(result2["data"]).to_equal({CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address})
    expect(result2["result"].unique_id).to_equal(LED_BLE_DISCOVERY_INFO.address)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
