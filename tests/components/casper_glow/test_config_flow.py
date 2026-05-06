"""Test the Casper Glow config flow."""

from unittest.mock import MagicMock, patch

from bluetooth_data_tools import human_readable_name
from pycasperglow import CasperGlowError
from tryke import Depends, expect, fixture, test

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.components.casper_glow.const import DOMAIN
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.device_registry import format_mac

from . import CASPER_GLOW_DISCOVERY_INFO, NOT_CASPER_GLOW_DISCOVERY_INFO
from ._fixtures import mock_casper_glow, mock_config_entry

from tests.common import MockConfigEntry
from tests.components.bluetooth import (
    generate_advertisement_data,
    generate_ble_device,
    inject_bluetooth_service_info,
)
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
async def bluetooth_step_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _glow: MagicMock = Depends(mock_casper_glow),
) -> None:
    """Test bluetooth discovery step success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=CASPER_GLOW_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    inject_bluetooth_service_info(hass, CASPER_GLOW_DISCOVERY_INFO)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(
        human_readable_name(
            None, CASPER_GLOW_DISCOVERY_INFO.name, CASPER_GLOW_DISCOVERY_INFO.address
        )
    )
    expect(result["data"]).to_equal(
        {CONF_ADDRESS: CASPER_GLOW_DISCOVERY_INFO.address}
    )
    expect(result["result"].unique_id).to_equal(
        format_mac(CASPER_GLOW_DISCOVERY_INFO.address)
    )


@test.cases(
    test.case("cannot_connect", side_effect=CasperGlowError, reason="cannot_connect"),
    test.case("unknown", side_effect=RuntimeError, reason="unknown"),
)
async def bluetooth_confirm_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    reason: str,
) -> None:
    """Test bluetooth confirm step error handling."""
    with patch(
        "homeassistant.components.casper_glow.config_flow.CasperGlow.handshake",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_BLUETOOTH},
            data=CASPER_GLOW_DISCOVERY_INFO,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test
async def user_step_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _glow: MagicMock = Depends(mock_casper_glow),
) -> None:
    """Test user step success path."""
    with patch(
        "homeassistant.components.casper_glow.config_flow.async_discovered_service_info",
        return_value=[NOT_CASPER_GLOW_DISCOVERY_INFO, CASPER_GLOW_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    inject_bluetooth_service_info(hass, CASPER_GLOW_DISCOVERY_INFO)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ADDRESS: CASPER_GLOW_DISCOVERY_INFO.address,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(
        human_readable_name(
            None, CASPER_GLOW_DISCOVERY_INFO.name, CASPER_GLOW_DISCOVERY_INFO.address
        )
    )
    expect(result["data"]).to_equal(
        {CONF_ADDRESS: CASPER_GLOW_DISCOVERY_INFO.address}
    )
    expect(result["result"].unique_id).to_equal(
        format_mac(CASPER_GLOW_DISCOVERY_INFO.address)
    )


@test
async def user_step_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step with no devices found."""
    with patch(
        "homeassistant.components.casper_glow.config_flow.async_discovered_service_info",
        return_value=[NOT_CASPER_GLOW_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test.cases(
    test.case(
        "cannot_connect",
        side_effect=CasperGlowError,
        expected_error="cannot_connect",
    ),
    test.case("unknown", side_effect=RuntimeError, expected_error="unknown"),
)
async def user_step_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    expected_error: str,
) -> None:
    """Test user step error handling."""
    with patch(
        "homeassistant.components.casper_glow.config_flow.async_discovered_service_info",
        return_value=[CASPER_GLOW_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.casper_glow.config_flow.CasperGlow.handshake",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: CASPER_GLOW_DISCOVERY_INFO.address},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": expected_error})


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test already configured device."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=CASPER_GLOW_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_step_skips_unrecognized_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that devices without a matching local name prefix are skipped."""
    unrecognized_discovery = BluetoothServiceInfoBleak(
        name="",
        address="AA:BB:CC:DD:EE:11",
        rssi=-60,
        manufacturer_data={},
        service_uuids=[],
        service_data={},
        source="local",
        device=generate_ble_device(address="AA:BB:CC:DD:EE:11", name=""),
        advertisement=generate_advertisement_data(service_uuids=[]),
        time=0,
        connectable=True,
        tx_power=-127,
    )
    with patch(
        "homeassistant.components.casper_glow.config_flow.async_discovered_service_info",
        return_value=[unrecognized_discovery],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")
