"""Test the PoolDose config flow."""

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from freezegun.api import FrozenDateTimeFactory
from pooldose.request_status import RequestStatus
from tryke import Depends, expect, fixture, test

from homeassistant.components.pooldose.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import (
    device_info,
    mock_config_entry,
    mock_pooldose_client,
    mock_setup_entry,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import freezer, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _client: MagicMock = Depends(mock_pooldose_client),
) -> None:
    """Module-local fixture executor anchor — autouse mock_pooldose_client."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the form shows error when device is unreachable."""
    client.is_connected = False
    client.connect.return_value = RequestStatus.HOST_UNREACHABLE

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

    client.is_connected = True
    client.connect.return_value = RequestStatus.SUCCESS

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def api_version_unsupported(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the form shows error when API version is unsupported."""
    client.check_apiversion_supported.return_value = (
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

    client.is_connected = True
    client.check_apiversion_supported.return_value = (RequestStatus.SUCCESS, {})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def form_no_device_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    info: dict[str, Any] = Depends(device_info),
) -> None:
    """Test that the form shows error when device_info is None."""
    client.device_info = None

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

    client.device_info = info

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("host_unreachable", client_status=RequestStatus.HOST_UNREACHABLE, expected_error="cannot_connect"),
    test.case("params_fetch_failed", client_status=RequestStatus.PARAMS_FETCH_FAILED, expected_error="params_fetch_failed"),
    test.case("unknown_error", client_status=RequestStatus.UNKNOWN_ERROR, expected_error="cannot_connect"),
)
async def connection_errors(
    *,
    client_status: str,
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the form shows appropriate errors for various connection issues."""
    client.connect.return_value = client_status

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

    client.connect.return_value = RequestStatus.SUCCESS

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def api_no_data(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the form shows error when API returns NO_DATA."""
    client.check_apiversion_supported.return_value = (RequestStatus.NO_DATA, {})

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

    client.check_apiversion_supported.return_value = (RequestStatus.SUCCESS, {})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def form_no_serial_number(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    info: dict[str, Any] = Depends(device_info),
) -> None:
    """Test that the form shows error when device_info has no serial number."""
    client.device_info = {"NAME": "Pool Device", "MODEL": "POOL DOSE"}

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

    client.device_info = info

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate_entry_aborts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the flow aborts if the device is already configured."""
    config_entry.add_to_hass(hass)

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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the DHCP flow aborts if no serial number is found."""
    client.device_info = {"NAME": "Pool Device", "MODEL": "POOL DOSE"}

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
    test.case("host_unreachable", client_status=RequestStatus.HOST_UNREACHABLE),
    test.case("params_fetch_failed", client_status=RequestStatus.PARAMS_FETCH_FAILED),
    test.case("unknown_error", client_status=RequestStatus.UNKNOWN_ERROR),
)
async def dhcp_connection_errors(
    *,
    client_status: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the DHCP flow aborts on connection errors."""
    client.connect.return_value = client_status

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
    test.case("no_data", api_status=RequestStatus.NO_DATA),
    test.case("api_version_unsupported", api_status=RequestStatus.API_VERSION_UNSUPPORTED),
)
async def dhcp_api_errors(
    *,
    api_status: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the DHCP flow aborts on API errors."""
    client.check_apiversion_supported.return_value = (api_status, {})

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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that DHCP discovery updates the host if it has changed."""
    config_entry.add_to_hass(hass)

    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.100")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.0.123", hostname="kommspot", macaddress="a4e57caabbcc"
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.0.123")


@test
async def dhcp_adds_mac_if_not_present(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that DHCP flow adds MAC address if not already in config entry data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="TEST123456789",
        data={CONF_HOST: "192.168.1.100"},
    )
    entry.add_to_hass(hass)

    expect(CONF_MAC not in entry.data).to_be(True)

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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
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


@test
async def reconfigure_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    freeze: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Test successful reconfigure updates host and reloads entry."""
    client.device_info = {"SERIAL_NUMBER": config_entry.unique_id}

    config_entry.add_to_hass(hass)
    reconfigure_result = await config_entry.start_reconfigure_flow(hass)
    expect(reconfigure_result["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_result["step_id"]).to_equal("reconfigure")
    result = await hass.config_entries.flow.async_configure(
        reconfigure_result["flow_id"], {CONF_HOST: "192.168.0.200"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data.get(CONF_HOST)).to_equal("192.168.0.200")

    freeze.tick(timedelta(seconds=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(entry is not None).to_be(True)
    expect(entry.data.get(CONF_HOST)).to_equal("192.168.0.200")


@test
async def reconfigure_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure shows cannot_connect when device unreachable."""
    client.connect.return_value = RequestStatus.HOST_UNREACHABLE

    config_entry.add_to_hass(hass)
    reconfigure_result = await config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        reconfigure_result["flow_id"], {CONF_HOST: "192.168.0.200"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def reconfigure_flow_wrong_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_pooldose_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure aborts when serial number doesn't match existing entry."""
    client.device_info = {"SERIAL_NUMBER": "OTHER123"}

    config_entry.add_to_hass(hass)
    reconfigure_result = await config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        reconfigure_result["flow_id"], {CONF_HOST: "192.168.0.200"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_device")
