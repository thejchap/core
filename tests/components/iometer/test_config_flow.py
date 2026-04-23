"""Test the IOmeter config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock, patch

from iometer import IOmeterConnectionError, IOmeterNoReadingsError, IOmeterNoStatusError
from tryke import Depends, expect, fixture, test

from homeassistant.components.iometer.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.iometer._fixtures import (
    mock_config_entry,
    mock_iometer_client,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

IP_ADDRESS = "10.0.0.2"
IOMETER_DEVICE_ID = "658c2b34-2017-45f2-a12b-731235f8bb97"

ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address(IP_ADDRESS),
    ip_addresses=[ip_address(IP_ADDRESS)],
    hostname="IOmeter-EC63E8.local.",
    name="IOmeter-EC63E8",
    port=80,
    type="_iometer._tcp.",
    properties={},
)


@fixture
def _mock_zeroconf() -> MagicMock:
    """Patch zeroconf so tests don't require a real zeroconf instance."""
    from zeroconf import DNSCache

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch("homeassistant.components.zeroconf.discovery.AsyncServiceBrowser"),
    ):
        zc = mock_zc.return_value
        zc.async_add_service_listener = AsyncMock()
        zc.async_remove_service_listener = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_iometer_client: AsyncMock = Depends(mock_iometer_client),
) -> None:
    """Test full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: IP_ADDRESS},
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("IOmeter 1ISK0000000000")
    expect(result["data"]).to_equal({CONF_HOST: IP_ADDRESS})
    expect(result["result"].unique_id).to_equal(IOMETER_DEVICE_ID)


@test
async def zeroconf_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_iometer_client: AsyncMock = Depends(mock_iometer_client),
) -> None:
    """Test zeroconf flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("IOmeter 1ISK0000000000")
    expect(result["data"]).to_equal({CONF_HOST: IP_ADDRESS})
    expect(result["result"].unique_id).to_equal(IOMETER_DEVICE_ID)


@test
async def zeroconf_flow_abort_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf flow aborts with duplicate."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "status-connection",
        method_name="get_current_status",
        exception=IOmeterConnectionError(),
        reason="cannot_connect",
    ),
    test.case(
        "status-missing",
        method_name="get_current_status",
        exception=IOmeterNoStatusError(),
        reason="no_status",
    ),
    test.case(
        "reading-missing",
        method_name="get_current_reading",
        exception=IOmeterNoReadingsError(),
        reason="no_readings",
    ),
)
async def zeroconf_flow_abort_errors(
    method_name: str,
    exception: Exception,
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_iometer_client: AsyncMock = Depends(mock_iometer_client),
) -> None:
    """Test zeroconf flow aborts when the client raises an exception."""
    getattr(mock_iometer_client, method_name).side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test.cases(
    test.case(
        "status-connection",
        method_name="get_current_status",
        exception=IOmeterConnectionError(),
        error_key="cannot_connect",
    ),
    test.case(
        "status-missing",
        method_name="get_current_status",
        exception=IOmeterNoStatusError(),
        error_key="no_status",
    ),
    test.case(
        "reading-missing",
        method_name="get_current_reading",
        exception=IOmeterNoReadingsError(),
        error_key="no_readings",
    ),
)
async def user_flow_errors(
    method_name: str,
    exception: Exception,
    error_key: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_iometer_client: AsyncMock = Depends(mock_iometer_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow returns errors for client exceptions."""
    getattr(mock_iometer_client, method_name).side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: IP_ADDRESS},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_key})

    getattr(mock_iometer_client, method_name).side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: IP_ADDRESS},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def flow_abort_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_iometer_client: AsyncMock = Depends(mock_iometer_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: IP_ADDRESS},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
