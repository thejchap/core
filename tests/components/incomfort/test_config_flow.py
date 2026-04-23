"""Tests for the Intergas InComfort config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientResponseError
from incomfortclient import InvalidGateway, InvalidHeaterList
from tryke import Depends, expect, fixture, test

from homeassistant.components.incomfort.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.common import MockConfigEntry
from tests.components.incomfort._fixtures import (
    MOCK_CONFIG,
    MOCK_CONFIG_DHCP,
    mock_incomfort,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

DHCP_SERVICE_INFO = DhcpServiceInfo(
    hostname="rfgateway",
    ip="192.168.1.12",
    macaddress=dr.format_mac("00:04:A3:DE:AD:FF").replace(":", ""),
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
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_incomfort: MagicMock = Depends(mock_incomfort),
) -> None:
    """Test we get the full form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_CONFIG
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Intergas InComfort/Intouch Lan2RF gateway")
    expect(result["data"]).to_equal(MOCK_CONFIG)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def entry_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_incomfort: MagicMock = Depends(mock_incomfort),
) -> None:
    """Test aborting if the entry is already configured."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_CONFIG[CONF_HOST]},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("invalid_gateway", exc=InvalidGateway, error="auth_error"),
    test.case("invalid_heater_list", exc=InvalidHeaterList, error="no_heaters"),
    test.case(
        "client_response_error",
        exc=ClientResponseError(None, None, status=500),
        error="unknown",
    ),
    test.case("timeout", exc=TimeoutError, error="timeout_error"),
    test.case("value_error", exc=ValueError, error="unknown"),
)
async def form_validation(
    exc: type[Exception] | Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_incomfort: MagicMock = Depends(mock_incomfort),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test form validation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_incomfort().heaters.side_effect = exc
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_CONFIG
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_incomfort().heaters.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_CONFIG
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def dhcp_flow_wih_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_incomfort: MagicMock = Depends(mock_incomfort),
) -> None:
    """Test dhcp flow for with authentication."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_SERVICE_INFO
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("dhcp_confirm")

    with patch.object(
        mock_incomfort(),
        "heaters",
        side_effect=InvalidGateway,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "192.168.1.12"}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("dhcp_auth")
    expect(result["errors"]).to_equal({"base": "auth_error"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_CONFIG_DHCP
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Intergas InComfort/Intouch Lan2RF gateway")
    expect(result["data"]).to_equal(MOCK_CONFIG)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
