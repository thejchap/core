"""Test the HDFury config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock, patch

from hdfury import HDFuryError
from tryke import Depends, expect, fixture, test

from homeassistant.components.hdfury.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.hdfury._fixtures import (
    mock_config_entry,
    mock_hdfury_client,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.1.123"),
    ip_addresses=[ip_address("192.168.1.123")],
    hostname="VRROOM-02.local.",
    name="VRROOM-02._http._tcp.local.",
    port=80,
    type="_http._tcp.local.",
    properties={
        "path": "/",
    },
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
async def async_step_user_gets_form_and_creates_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_hdfury_client: AsyncMock = Depends(mock_hdfury_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that we can view the form and that the config flow creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.123"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.123"})
    expect(result["result"].unique_id).to_equal("000123456789")


@test
async def abort_if_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_hdfury_client: AsyncMock = Depends(mock_hdfury_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that we abort if we attempt to submit the same entry twice."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.123"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def successful_recovery_after_connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_hdfury_client: AsyncMock = Depends(mock_hdfury_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test error shown when connection fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    mock_hdfury_client.get_board.side_effect = HDFuryError()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.123"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_hdfury_client.get_board.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.123"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.123"})
    expect(result["result"].unique_id).to_equal("000123456789")


@test
async def zeroconf_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_hdfury_client: AsyncMock = Depends(mock_hdfury_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.123"})
    expect(result["result"].unique_id).to_equal("000123456789")


@test
async def zeroconf_flow_failure(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_hdfury_client: AsyncMock = Depends(mock_hdfury_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf flow failure."""
    mock_hdfury_client.get_board.side_effect = HDFuryError()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def zeroconf_flow_abort_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_hdfury_client: AsyncMock = Depends(mock_hdfury_client),
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


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_hdfury_client: AsyncMock = Depends(mock_hdfury_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({})

    expect(mock_config_entry.data[CONF_HOST]).to_equal("192.168.1.123")
    expect(mock_config_entry.unique_id).to_equal("000123456789")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.124"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(mock_config_entry.data[CONF_HOST]).to_equal("192.168.1.124")
    expect(mock_config_entry.unique_id).to_equal("000123456789")


@test
async def reconfigure_flow_no_change(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_hdfury_client: AsyncMock = Depends(mock_hdfury_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration without changing values."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({})

    expect(mock_config_entry.data[CONF_HOST]).to_equal("192.168.1.123")
    expect(mock_config_entry.unique_id).to_equal("000123456789")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.123"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(mock_config_entry.data[CONF_HOST]).to_equal("192.168.1.123")
    expect(mock_config_entry.unique_id).to_equal("000123456789")


@test
async def reconfigure_flow_abort_incorrect_device(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_hdfury_client: AsyncMock = Depends(mock_hdfury_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test ip of other device with different serial."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({})

    mock_hdfury_client.get_board.return_value = {
        "hostname": "VRROOM-21",
        "ipaddress": "192.168.1.124",
        "serial": "000987654321",
        "pcbv": "3",
        "version": "FW: 0.61",
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.124"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("incorrect_device")

    expect(mock_config_entry.data[CONF_HOST]).to_equal("192.168.1.123")
    expect(mock_config_entry.unique_id).to_equal("000123456789")


@test
async def reconfigure_flow_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_hdfury_client: AsyncMock = Depends(mock_hdfury_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration fails with cannot connect."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({})

    mock_hdfury_client.get_board.side_effect = HDFuryError()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.124"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})
    expect(result["data_schema"]({})).to_equal({CONF_HOST: "192.168.1.123"})

    mock_hdfury_client.get_board.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.124"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(mock_config_entry.data[CONF_HOST]).to_equal("192.168.1.124")
    expect(mock_config_entry.unique_id).to_equal("000123456789")
