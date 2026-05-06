"""Define tests for the Dune HD config flow."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.dunehd.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.dunehd._fixtures import mock_zeroconf
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


CONFIG_HOSTNAME = {CONF_HOST: "dunehd-host"}
CONFIG_IP = {CONF_HOST: "10.10.10.12"}

DUNEHD_STATE = {"protocol_version": "4", "player_state": "navigator"}


@test
async def user_invalid_host(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that errors are shown when the host is invalid."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "invalid/host"}
    )

    expect(result["errors"]).to_equal({CONF_HOST: "invalid_host"})


@test
async def user_very_long_host(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that errors are shown when the host is longer than 253 chars."""
    long_host = (
        "very_long_host_very_long_host_very_long_host_very_long_host_very_long_"
        "host_very_long_host_very_long_host_very_long_host_very_long_host_very_long_"
        "host_very_long_host_very_long_host_very_long_host_very_long_host_very_long_"
        "host_very_long_host_very_long_host"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: long_host}
    )

    expect(result["errors"]).to_equal({CONF_HOST: "invalid_host"})


@test
async def user_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that errors are shown when cannot connect to the host."""
    with patch("pdunehd.DuneHDPlayer.update_state", return_value={}):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG_IP
        )

        expect(result["errors"]).to_equal({CONF_HOST: "cannot_connect"})


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that errors are shown when duplicates are added."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_HOSTNAME,
        title="dunehd-host",
    )
    config_entry.add_to_hass(hass)

    with patch("pdunehd.DuneHDPlayer.update_state", return_value=DUNEHD_STATE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG_HOSTNAME
        )

        expect(result["errors"]).to_equal({CONF_HOST: "already_configured"})


@test
async def create_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that the user step works."""
    with (
        patch("homeassistant.components.dunehd.async_setup_entry"),
        patch("pdunehd.DuneHDPlayer.update_state", return_value=DUNEHD_STATE),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG_HOSTNAME
        )

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["title"]).to_equal("dunehd-host")
        expect(result["data"]).to_equal({CONF_HOST: "dunehd-host"})


@test
async def create_entry_with_ipv6_address(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that the user step works with device IPv6 address.."""
    with (
        patch("homeassistant.components.dunehd.async_setup_entry"),
        patch("pdunehd.DuneHDPlayer.update_state", return_value=DUNEHD_STATE),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_HOST: "2001:db8::1428:57ab"},
        )

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["title"]).to_equal("2001:db8::1428:57ab")
        expect(result["data"]).to_equal({CONF_HOST: "2001:db8::1428:57ab"})
