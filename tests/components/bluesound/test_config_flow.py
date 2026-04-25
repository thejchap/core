"""Test the Bluesound config flow."""

from ipaddress import IPv4Address, IPv6Address
from unittest.mock import AsyncMock

from pyblu.errors import PlayerUnreachableError
from tryke import Depends, expect, fixture, test

from homeassistant.components.bluesound.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import PlayerMocks, config_entry, mock_setup_entry, player_mocks

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _player_mocks: PlayerMocks = Depends(player_mocks),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("player-name1111")
    expect(result["data"]).to_equal({CONF_HOST: "1.1.1.1", CONF_PORT: 11000})
    expect(result["result"].unique_id).to_equal("ff:ff:01:01:01:01-11000")

    setup_entry.assert_called_once()


@test
async def user_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    player_mocks_value: PlayerMocks = Depends(player_mocks),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    player_mocks_value.player_data.sync_status_long_polling_mock.set_error(
        PlayerUnreachableError("Player not reachable")
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})
    expect(result["step_id"]).to_equal("user")

    player_mocks_value.player_data.sync_status_long_polling_mock.set_error(None)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("player-name1111")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 11000,
        }
    )

    setup_entry.assert_called_once()


@test
async def user_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    player_mocks_value: PlayerMocks = Depends(player_mocks),
    config_entry_value: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test we handle already configured."""
    config_entry_value.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.2",
            CONF_PORT: 11000,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(config_entry_value.data[CONF_HOST]).to_equal("1.1.1.2")

    player_mocks_value.player_data_for_already_configured.player.sync_status.assert_called_once()


@test
async def zeroconf_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    player_mocks_value: PlayerMocks = Depends(player_mocks),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=IPv4Address("1.1.1.1"),
            ip_addresses=[IPv4Address("1.1.1.1")],
            port=11000,
            hostname="player-name1111",
            type="_musc._tcp.local.",
            name="player-name._musc._tcp.local.",
            properties={},
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    setup_entry.assert_not_called()
    player_mocks_value.player_data.player.sync_status.assert_called_once()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("player-name1111")
    expect(result["data"]).to_equal({CONF_HOST: "1.1.1.1", CONF_PORT: 11000})
    expect(result["result"].unique_id).to_equal("ff:ff:01:01:01:01-11000")

    setup_entry.assert_called_once()


@test
async def zeroconf_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    player_mocks_value: PlayerMocks = Depends(player_mocks),
) -> None:
    """Test we handle cannot connect error."""
    player_mocks_value.player_data.player.sync_status.side_effect = (
        PlayerUnreachableError("Player not reachable")
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=IPv4Address("1.1.1.1"),
            ip_addresses=[IPv4Address("1.1.1.1")],
            port=11000,
            hostname="player-name1111",
            type="_musc._tcp.local.",
            name="player-name._musc._tcp.local.",
            properties={},
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")

    player_mocks_value.player_data.player.sync_status.assert_called_once()


@test
async def zeroconf_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    player_mocks_value: PlayerMocks = Depends(player_mocks),
    config_entry_value: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test we handle already configured and update the host."""
    config_entry_value.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=IPv4Address("1.1.1.2"),
            ip_addresses=[IPv4Address("1.1.1.2")],
            port=11000,
            hostname="player-name1112",
            type="_musc._tcp.local.",
            name="player-name._musc._tcp.local.",
            properties={},
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(config_entry_value.data[CONF_HOST]).to_equal("1.1.1.2")

    player_mocks_value.player_data_for_already_configured.player.sync_status.assert_called_once()


@test
async def zeroconf_flow_no_ipv4_address(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test abort flow when no ipv4 address is found in zeroconf data."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=IPv6Address("2001:db8::1"),
            ip_addresses=[IPv6Address("2001:db8::1")],
            port=11000,
            hostname="player-name1112",
            type="_musc._tcp.local.",
            name="player-name._musc._tcp.local.",
            properties={},
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_ipv4_address")
