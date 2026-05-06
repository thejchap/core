"""Test the sma config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from pysma import SmaAuthenticationException, SmaConnectionException, SmaReadException
from pysma.helpers import DeviceInfo
from tryke import Depends, expect, fixture, test

from homeassistant.components.sma.const import CONF_GROUP, DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_SSL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from . import (
    MOCK_DEVICE,
    MOCK_DHCP_DISCOVERY,
    MOCK_DHCP_DISCOVERY_INPUT,
    MOCK_USER_INPUT,
    MOCK_USER_REAUTH,
    MOCK_USER_RECONFIGURE,
)
from ._fixtures import mock_config_entry, mock_setup_entry, mock_sma_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DHCP_DISCOVERY = DhcpServiceInfo(
    ip="1.1.1.1",
    hostname="SMA123456",
    macaddress="0015bb00abcd",
)

DHCP_DISCOVERY_DUPLICATE = DhcpServiceInfo(
    ip="1.1.1.1",
    hostname="SMA123456789",
    macaddress="0015bb00abcd",
)

DHCP_DISCOVERY_DUPLICATE_001 = DhcpServiceInfo(
    ip="1.1.1.1",
    hostname="SMA123456789-001",
    macaddress="0015bb00abcd",
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    sma_client: MagicMock = Depends(mock_sma_client),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCK_USER_INPUT["host"])
    expect(result["data"]).to_equal(MOCK_USER_INPUT)

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("connection", exception=SmaConnectionException, error="cannot_connect"),
    test.case(
        "auth", exception=SmaAuthenticationException, error="invalid_auth"
    ),
    test.case(
        "read",
        exception=SmaReadException,
        error="cannot_retrieve_device_info",
    ),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def form_exceptions(
    *,
    exception: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.sma.config_flow.SMAWebConnect.new_session",
        side_effect=exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_INPUT,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _sma_client: MagicMock = Depends(mock_sma_client),
) -> None:
    """Test starting a flow by user when already configured."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT, unique_id="123456789")
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def dhcp_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _sma_client: MagicMock = Depends(mock_sma_client),
) -> None:
    """Test we can setup from dhcp discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_DISCOVERY,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_DHCP_DISCOVERY_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCK_DHCP_DISCOVERY["host"])
    expect(result["data"]).to_equal(MOCK_DHCP_DISCOVERY)
    expect(result["result"].unique_id).to_equal(
        DHCP_DISCOVERY.hostname.replace("SMA", "")
    )


@test
async def dhcp_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test starting a flow by dhcp when already configured."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_DISCOVERY_DUPLICATE
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def dhcp_already_configured_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _sma_client: MagicMock = Depends(mock_sma_client),
) -> None:
    """Test DHCP when already configured and MAC is added."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(CONF_MAC not in config_entry.data).to_be(True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_DISCOVERY_DUPLICATE_001,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    await hass.async_block_till_done()

    expect(config_entry.data.get(CONF_MAC)).to_equal(
        format_mac(DHCP_DISCOVERY_DUPLICATE_001.macaddress)
    )


@test.cases(
    test.case("connection", exception=SmaConnectionException, error="cannot_connect"),
    test.case("auth", exception=SmaAuthenticationException, error="invalid_auth"),
    test.case(
        "read",
        exception=SmaReadException,
        error="cannot_retrieve_device_info",
    ),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def dhcp_exceptions(
    *,
    exception: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _sma_client: MagicMock = Depends(mock_sma_client),
) -> None:
    """Test we handle cannot connect error in DHCP flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_DISCOVERY,
    )

    with patch("homeassistant.components.sma.config_flow.SMAWebConnect") as mock_sma:
        mock_sma_instance = mock_sma.return_value
        mock_sma_instance.new_session = AsyncMock(side_effect=exception)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_DHCP_DISCOVERY_INPUT,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    with patch("homeassistant.components.sma.config_flow.SMAWebConnect") as mock_sma:
        mock_sma_instance = mock_sma.return_value
        mock_sma_instance.new_session = AsyncMock(return_value=True)
        mock_sma_instance.device_info = AsyncMock(return_value=MOCK_DEVICE)
        mock_sma_instance.close_session = AsyncMock(return_value=True)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_DHCP_DISCOVERY_INPUT,
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCK_DHCP_DISCOVERY["host"])
    expect(result["data"]).to_equal(MOCK_DHCP_DISCOVERY)
    expect(result["result"].unique_id).to_equal(
        DHCP_DISCOVERY.hostname.replace("SMA", "")
    )


@test
async def full_flow_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _sma_client: MagicMock = Depends(mock_sma_client),
) -> None:
    """Test the full flow of the config flow."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT, unique_id="123456789")
    entry.add_to_hass(hass)
    await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_REAUTH,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("connection", exception=SmaConnectionException, error="cannot_connect"),
    test.case("auth", exception=SmaAuthenticationException, error="invalid_auth"),
    test.case(
        "read",
        exception=SmaReadException,
        error="cannot_retrieve_device_info",
    ),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def reauth_flow_exceptions(
    *,
    exception: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_entry_obj: MockConfigEntry = Depends(mock_config_entry),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle errors during reauth flow properly."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT, unique_id="123456789")
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    with patch("homeassistant.components.sma.config_flow.SMAWebConnect") as mock_sma:
        mock_sma_instance = mock_sma.return_value
        mock_sma_instance.new_session = AsyncMock(side_effect=exception)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_REAUTH,
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": error})
        expect(result["step_id"]).to_equal("reauth_confirm")

        mock_sma_instance.new_session = AsyncMock(return_value=True)
        mock_sma_instance.device_info = AsyncMock(return_value=MOCK_DEVICE)
        mock_sma_instance.close_session = AsyncMock(return_value=True)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_REAUTH,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def full_flow_reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _sma_client: MagicMock = Depends(mock_sma_client),
) -> None:
    """Test the full flow of the config flow."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT, unique_id="123456789")
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_HOST]).to_equal("1.1.1.2")
    expect(entry.data[CONF_SSL]).to_be(True)
    expect(entry.data[CONF_VERIFY_SSL]).to_be(False)
    expect(entry.data[CONF_GROUP]).to_equal("user")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("connection", exception=SmaConnectionException, error="cannot_connect"),
    test.case("auth", exception=SmaAuthenticationException, error="invalid_auth"),
    test.case(
        "read",
        exception=SmaReadException,
        error="cannot_retrieve_device_info",
    ),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def full_flow_reconfigure_exceptions(
    *,
    exception: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    sma_client: MagicMock = Depends(mock_sma_client),
) -> None:
    """Test we handle cannot connect error and recover from it."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT, unique_id="123456789")
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    sma_client.new_session.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    sma_client.new_session.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_HOST]).to_equal("1.1.1.2")
    expect(entry.data[CONF_SSL]).to_be(True)
    expect(entry.data[CONF_VERIFY_SSL]).to_be(False)
    expect(entry.data[CONF_GROUP]).to_equal("user")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def reconfigure_mismatch_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    sma_client: MagicMock = Depends(mock_sma_client),
) -> None:
    """Test when a mismatch happens during reconfigure."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT, unique_id="123456789")
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    different_device = DeviceInfo(
        manufacturer="SMA",
        name="Different SMA Device",
        type="Sunny Boy 5.0",
        serial=987654321,
        sw_version="2.0.0",
    )
    sma_client.device_info = AsyncMock(return_value=different_device)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")
