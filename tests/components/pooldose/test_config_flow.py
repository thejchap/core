"""Test the PoolDose config flow."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components.pooldose.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from .conftest import RequestStatus

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    freezer as freezer_fx,
    hass as hass_fixture,
    mock_network,
)

from ._fixtures import (
    device_info as device_info_fx,
    mock_async_zeroconf as mock_async_zeroconf_fx,
    mock_config_entry as mock_config_entry_fx,
    mock_pooldose_client as mock_pooldose_client_fx,
    mock_setup_entry as mock_setup_entry_fx,
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zc: MagicMock = Depends(mock_async_zeroconf_fx),
    _client: MagicMock = Depends(mock_pooldose_client_fx),
) -> None:
    """Wire mock_network, mock_async_zeroconf, mock_pooldose_client for every test."""


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test the full config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("PoolDose TEST123456789")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.100"})
    expect(result["result"].unique_id).to_equal("TEST123456789")


@test
async def device_unreachable(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that the form shows error when device is unreachable."""
    mock_pooldose_client.is_connected = False
    mock_pooldose_client.connect.return_value = RequestStatus.HOST_UNREACHABLE

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_pooldose_client.is_connected = True
    mock_pooldose_client.connect.return_value = RequestStatus.SUCCESS

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def api_version_unsupported(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that the form shows error when API version is unsupported."""
    mock_pooldose_client.check_apiversion_supported.return_value = (
        RequestStatus.API_VERSION_UNSUPPORTED,
        {"api_version_is": "v0.9", "api_version_should": "v1.0"},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "api_not_supported"})

    mock_pooldose_client.is_connected = True
    mock_pooldose_client.check_apiversion_supported.return_value = (
        RequestStatus.SUCCESS,
        {},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def form_no_device_info(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    device_info: dict[str, Any] = Depends(device_info_fx),
) -> None:
    """Test that the form shows error when device_info is None."""
    mock_pooldose_client.device_info = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "no_device_info"})

    mock_pooldose_client.device_info = device_info

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("host_unreachable", RequestStatus.HOST_UNREACHABLE, "cannot_connect"),
    test.case(
        "params_fetch_failed", RequestStatus.PARAMS_FETCH_FAILED, "params_fetch_failed"
    ),
    test.case("unknown_error", RequestStatus.UNKNOWN_ERROR, "cannot_connect"),
)
async def connection_errors(
    client_status: RequestStatus,
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that the form shows appropriate errors for various connection issues."""
    mock_pooldose_client.connect.return_value = client_status

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    mock_pooldose_client.connect.return_value = RequestStatus.SUCCESS

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def api_no_data(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that the form shows error when API returns NO_DATA."""
    mock_pooldose_client.check_apiversion_supported.return_value = (
        RequestStatus.NO_DATA,
        {},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "api_not_set"})

    mock_pooldose_client.check_apiversion_supported.return_value = (
        RequestStatus.SUCCESS,
        {},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def form_no_serial_number(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    device_info: dict[str, Any] = Depends(device_info_fx),
) -> None:
    """Test that the form shows error when device_info has no serial number."""
    mock_pooldose_client.device_info = {"NAME": "Pool Device", "MODEL": "POOL DOSE"}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "no_serial_number"})

    mock_pooldose_client.device_info = device_info

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate_entry_aborts(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test that the flow aborts if the device is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def dhcp_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test the full DHCP config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.0.123", hostname="kommspot", macaddress="a4e57caabbcc"
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("dhcp_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("PoolDose TEST123456789")
    expect(result["data"][CONF_HOST]).to_equal("192.168.0.123")
    expect(result["data"][CONF_MAC]).to_equal("a4e57caabbcc")
    expect(result["result"].unique_id).to_equal("TEST123456789")


@test
async def dhcp_no_serial_number(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that the DHCP flow aborts if no serial number is found."""
    mock_pooldose_client.device_info = {"NAME": "Pool Device", "MODEL": "POOL DOSE"}

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.0.123", hostname="kommspot", macaddress="a4e57caabbcc"
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_serial_number")


@test.cases(
    test.case("host_unreachable", RequestStatus.HOST_UNREACHABLE),
    test.case("params_fetch_failed", RequestStatus.PARAMS_FETCH_FAILED),
    test.case("unknown_error", RequestStatus.UNKNOWN_ERROR),
)
async def dhcp_connection_errors(
    client_status: RequestStatus,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that the DHCP flow aborts on connection errors."""
    mock_pooldose_client.connect.return_value = client_status

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.0.123", hostname="kommspot", macaddress="a4e57caabbcc"
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_serial_number")


@test.cases(
    test.case("no_data", RequestStatus.NO_DATA),
    test.case("api_version_unsupported", RequestStatus.API_VERSION_UNSUPPORTED),
)
async def dhcp_api_errors(
    api_status: RequestStatus,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that the DHCP flow aborts on API errors."""
    mock_pooldose_client.check_apiversion_supported.return_value = (api_status, {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.0.123", hostname="kommspot", macaddress="a4e57caabbcc"
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_serial_number")


@test
async def dhcp_updates_host(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that DHCP discovery updates the host if it has changed."""
    mock_config_entry.add_to_hass(hass)
    expect(mock_config_entry.data[CONF_HOST]).to_equal("192.168.1.100")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.0.123", hostname="kommspot", macaddress="a4e57caabbcc"
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(mock_config_entry.data[CONF_HOST]).to_equal("192.168.0.123")


@test
async def dhcp_adds_mac_if_not_present(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that DHCP flow adds MAC address if not already in config entry data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="TEST123456789",
        data={CONF_HOST: "192.168.1.100"},
    )
    entry.add_to_hass(hass)
    expect(CONF_MAC in entry.data).to_be(False)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.0.123", hostname="kommspot", macaddress="a4e57caabbcc"
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal("192.168.0.123")
    expect(entry.data[CONF_MAC]).to_equal("a4e57caabbcc")


@test
async def dhcp_preserves_existing_mac(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that DHCP flow preserves existing MAC in config entry data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="TEST123456789",
        data={
            CONF_HOST: "192.168.1.100",
            CONF_MAC: "existing11aabb",
        },
    )
    entry.add_to_hass(hass)
    expect(entry.data[CONF_MAC]).to_equal("existing11aabb")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.0.123", hostname="kommspot", macaddress="different22ccdd"
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal("192.168.0.123")
    expect(entry.data[CONF_MAC]).to_equal("existing11aabb")


async def _start_reconfigure_flow(
    hass: HomeAssistant, entry: MockConfigEntry, host_ip: str
) -> Any:
    """Initialize a reconfigure flow for PoolDose and submit new host."""
    entry.add_to_hass(hass)
    reconfigure_result = await entry.start_reconfigure_flow(hass)
    expect(reconfigure_result["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_result["step_id"]).to_equal("reconfigure")
    return await hass.config_entries.flow.async_configure(
        reconfigure_result["flow_id"], {CONF_HOST: host_ip}
    )


@test
async def reconfigure_flow_success(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test successful reconfigure updates host and reloads entry."""
    mock_pooldose_client.device_info = {"SERIAL_NUMBER": mock_config_entry.unique_id}

    result = await _start_reconfigure_flow(hass, mock_config_entry, "192.168.0.200")

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data.get(CONF_HOST)).to_equal("192.168.0.200")

    freezer.tick(timedelta(seconds=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
    expect(entry is not None).to_be(True)
    expect(entry.data.get(CONF_HOST)).to_equal("192.168.0.200")


@test
async def reconfigure_flow_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfigure shows cannot_connect when device unreachable."""
    mock_pooldose_client.connect.return_value = RequestStatus.HOST_UNREACHABLE

    result = await _start_reconfigure_flow(hass, mock_config_entry, "192.168.0.200")

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def reconfigure_flow_wrong_device(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pooldose_client: MagicMock = Depends(mock_pooldose_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfigure aborts when serial number doesn't match existing entry."""
    mock_pooldose_client.device_info = {"SERIAL_NUMBER": "OTHER123"}

    result = await _start_reconfigure_flow(hass, mock_config_entry, "192.168.0.200")

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_device")
