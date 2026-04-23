"""Test the Altruist config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.altruist.const import CONF_HOST, DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.altruist._fixtures import (
    mock_altruist_client,
    mock_altruist_client_fails_once,
    mock_config_entry,
    mock_setup_entry,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.1.100"),
    ip_addresses=[ip_address("192.168.1.100")],
    hostname="altruist-purple.local.",
    name="altruist-purple._altruist._tcp.local.",
    port=80,
    type="_altruist._tcp.local.",
    properties={
        "PATH": "/config",
    },
)


@test
async def form_user_step_success(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_altruist_client: AsyncMock = Depends(mock_altruist_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user step shows form and succeeds with valid input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.100"},
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("5366960e8b18")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.100"})
    expect(result["result"].unique_id).to_equal("5366960e8b18")


@test
async def form_user_step_cannot_connect_then_recovers(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_altruist_client: AsyncMock = Depends(mock_altruist_client),
    _mock_altruist_client_fails_once: None = Depends(mock_altruist_client_fails_once),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle connection error and allow recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.100"},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "no_device_found"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.100"},
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("5366960e8b18")
    expect(result["result"].unique_id).to_equal("5366960e8b18")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.100"})


@test
async def form_user_step_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_altruist_client: AsyncMock = Depends(mock_altruist_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we abort if already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.100"},
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_discovery(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_altruist_client: AsyncMock = Depends(mock_altruist_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("5366960e8b18")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.100"})
    expect(result["result"].unique_id).to_equal("5366960e8b18")


@test
async def zeroconf_discovery_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_altruist_client: AsyncMock = Depends(mock_altruist_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf discovery when already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_discovery_cant_create_client(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_altruist_client_fails_once: AsyncMock = Depends(
        mock_altruist_client_fails_once
    ),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf discovery when client cannot be created."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("no_device_found")
