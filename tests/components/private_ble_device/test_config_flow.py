"""Tests for private bluetooth device config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.private_ble_device import const
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType
from homeassistant.helpers.service_info.bluetooth import BluetoothServiceInfo

from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_with_bluetooth(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
) -> None:
    """Apply enable_bluetooth via this trigger."""


def assert_form_error(result: FlowResult, key: str, value: str) -> None:
    """Assert that a flow returned a form error."""
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(True)
    expect(result["errors"][key]).to_equal(value)


@test.skip("requires mock_bluetooth_adapters without enable_bluetooth; module fixtures conflict")
async def setup_user_no_bluetooth(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up via user interaction when bluetooth is not enabled."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("bluetooth_not_available")


@test
async def invalid_irk(
    _trigger: None = Depends(_trigger_with_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test invalid irk."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"irk": "irk:000000"}
    )
    assert_form_error(result, "irk", "irk_not_valid")


@test
async def invalid_irk_base64(
    _trigger: None = Depends(_trigger_with_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test invalid irk."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"irk": "Ucredacted4T8n!!ZZZ=="}
    )
    assert_form_error(result, "irk", "irk_not_valid")


@test
async def invalid_irk_hex(
    _trigger: None = Depends(_trigger_with_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test invalid irk."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"irk": "irk:abcdefghi"}
    )
    assert_form_error(result, "irk", "irk_not_valid")


@test
async def irk_not_found(
    _trigger: None = Depends(_trigger_with_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test irk not found."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"irk": "irk:00000000000000000000000000000000"},
    )
    assert_form_error(result, "irk", "irk_not_found")


@test
async def flow_works(
    _trigger: None = Depends(_trigger_with_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow works."""

    inject_bluetooth_service_info(
        hass,
        BluetoothServiceInfo(
            name="Test Test Test",
            address="40:01:02:0a:c4:a6",
            rssi=-63,
            service_data={},
            manufacturer_data={},
            service_uuids=[],
            source="local",
        ),
    )

    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    # Check you can finish the flow.
    with patch(
        "homeassistant.components.private_ble_device.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"irk": "irk:00000000000000000000000000000000"},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test Test Test")
    expect(result["data"]).to_equal({"irk": "00000000000000000000000000000000"})
    expect(result["result"].unique_id).to_equal("00000000000000000000000000000000")


@test
async def flow_works_by_base64(
    _trigger: None = Depends(_trigger_with_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow works."""

    inject_bluetooth_service_info(
        hass,
        BluetoothServiceInfo(
            name="Test Test Test",
            address="40:01:02:0a:c4:a6",
            rssi=-63,
            service_data={},
            manufacturer_data={},
            service_uuids=[],
            source="local",
        ),
    )

    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    # Check you can finish the flow.
    with patch(
        "homeassistant.components.private_ble_device.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"irk": "AAAAAAAAAAAAAAAAAAAAAA=="},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test Test Test")
    expect(result["data"]).to_equal({"irk": "00000000000000000000000000000000"})
    expect(result["result"].unique_id).to_equal("00000000000000000000000000000000")
