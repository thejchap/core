"""Test the Russound RIO config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.russound_rio.const import DOMAIN, TYPE_SERIAL, TYPE_TCP
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import mock_config_entry, mock_russound_client, mock_setup_entry

from .const import (
    MOCK_RECONFIGURATION_SERIAL_ENTRY_DATA,
    MOCK_RECONFIGURATION_SERIAL_STEP_INPUT,
    MOCK_RECONFIGURATION_TCP_ENTRY_DATA,
    MOCK_RECONFIGURATION_TCP_STEP_INPUT,
    MOCK_SERIAL_CONFIG,
    MOCK_SERIAL_STEP_INPUT,
    MOCK_TCP_CONFIG,
    MOCK_TCP_STEP_INPUT,
    MODEL,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.20.17"),
    ip_addresses=[ip_address("192.168.20.17")],
    hostname="controller1.local.",
    name="controller1._stream-magic._tcp.local.",
    port=9621,
    type="_rio._tcp.local.",
    properties={
        "txtvers": "0",
        "productType": "2",
        "productId": "59",
        "version": "07.04.00",
        "buildDate": "Jul 8 2019",
        "localName": "0",
    },
)


@fixture
def _trigger_executor() -> None:
    """Present so tryke builds a fixture executor for this module."""


async def _start_reconfigure_flow(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> ConfigFlowResult:
    """Initialize reconfigure flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    return result


@test
async def user_flow_tcp_creates_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_russound_client),
) -> None:
    """Test TCP user flow creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_TCP},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("tcp")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_TCP_STEP_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MODEL)
    expect(result["data"]).to_equal(MOCK_TCP_CONFIG)
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(result["result"].unique_id).to_equal("00:11:22:33:44:55")


@test
async def tcp_flow_cannot_connect_then_recovers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_russound_client),
) -> None:
    """Test TCP flow handles cannot connect and recovers."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_TCP},
    )
    expect(result["step_id"]).to_equal("tcp")

    client.connect.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_TCP_STEP_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("tcp")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    client.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_TCP_STEP_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(MOCK_TCP_CONFIG)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def tcp_flow_duplicate_aborts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_russound_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate TCP flow aborts."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_TCP},
    )
    expect(result["step_id"]).to_equal("tcp")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_TCP_STEP_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_russound_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("MCA-C5")
    expect(result["data"]).to_equal(
        {
            CONF_TYPE: TYPE_TCP,
            CONF_HOST: "192.168.20.17",
            CONF_PORT: 9621,
        }
    )
    expect(result["result"].unique_id).to_equal("00:11:22:33:44:55")


@test
async def zeroconf_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_russound_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf flow errors."""
    client.connect.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")

    client.connect.side_effect = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_TYPE: TYPE_TCP,
            CONF_HOST: "192.168.20.17",
            CONF_PORT: 9621,
        }
    )


@test
async def zeroconf_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_russound_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf duplicate."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_duplicate_different_ip(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_russound_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf duplicate with IP update."""
    entry.add_to_hass(hass)

    zeroconf_discovery_different_ip = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.20.18"),
        ip_addresses=[ip_address("192.168.20.18")],
        hostname="controller1.local.",
        name="controller1._stream-magic._tcp.local.",
        port=9621,
        type="_rio._tcp.local.",
        properties={
            "txtvers": "0",
            "productType": "2",
            "productId": "59",
            "version": "07.04.00",
            "buildDate": "Jul 8 2019",
            "localName": "0",
        },
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=zeroconf_discovery_different_ip,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    new_entry = hass.config_entries.async_get_entry(entry.entry_id)
    expect(bool(new_entry)).to_be(True)
    expect(new_entry.data).to_equal(
        {
            CONF_TYPE: TYPE_TCP,
            CONF_HOST: "192.168.20.18",
            CONF_PORT: 9621,
        }
    )


@test
async def user_flow_after_zeroconf_started(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_russound_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow after zeroconf started."""
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(len(hass.config_entries.flow.async_progress(DOMAIN))).to_equal(2)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_TCP},
    )
    expect(result["step_id"]).to_equal("tcp")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_TCP_STEP_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(bool(hass.config_entries.flow.async_progress(DOMAIN))).to_be(False)


@test
async def reconfigure_tcp_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_russound_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test TCP reconfigure flow."""
    result = await _start_reconfigure_flow(hass, entry)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_TCP},
    )
    expect(result["step_id"]).to_equal("tcp")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_RECONFIGURATION_TCP_STEP_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    new_entry = hass.config_entries.async_get_entry(entry.entry_id)
    expect(bool(new_entry)).to_be(True)
    expect(new_entry.data).to_equal(MOCK_RECONFIGURATION_TCP_ENTRY_DATA)


@test
async def reconfigure_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_russound_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Ensure reconfigure flow aborts when the device changes."""
    client.controllers[1].mac_address = "different_mac"

    result = await _start_reconfigure_flow(hass, entry)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_TCP},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("tcp")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_RECONFIGURATION_TCP_STEP_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_device")


@test
async def user_flow_serial_creates_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_russound_client),
) -> None:
    """Test serial user flow creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_SERIAL},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("serial")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_SERIAL_STEP_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MODEL)
    expect(result["data"]).to_equal(MOCK_SERIAL_CONFIG)
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(result["result"].unique_id).to_equal("00:11:22:33:44:55")


@test
async def serial_flow_cannot_connect_then_recovers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_russound_client),
) -> None:
    """Test serial flow handles cannot connect and recovers."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_SERIAL},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("serial")

    client.connect.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_SERIAL_STEP_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("serial")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    client.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_SERIAL_STEP_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MODEL)
    expect(result["data"]).to_equal(MOCK_SERIAL_CONFIG)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def serial_flow_duplicate_aborts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_russound_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate serial flow aborts."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_SERIAL},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("serial")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_SERIAL_STEP_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure_serial_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_russound_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test serial reconfigure flow."""
    result = await _start_reconfigure_flow(hass, entry)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_SERIAL},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("serial")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_RECONFIGURATION_SERIAL_STEP_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    new_entry = hass.config_entries.async_get_entry(entry.entry_id)
    expect(bool(new_entry)).to_be(True)
    expect(new_entry.data).to_equal(MOCK_RECONFIGURATION_SERIAL_ENTRY_DATA)


@test
async def reconfigure_serial_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_russound_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Ensure serial reconfigure aborts when device changes."""
    client.controllers[1].mac_address = "different_mac"

    result = await _start_reconfigure_flow(hass, entry)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_SERIAL},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("serial")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_RECONFIGURATION_SERIAL_STEP_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_device")
