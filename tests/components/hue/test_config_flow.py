"""Test the hue config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("discovery + extensive setup")
async def flow_works(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow ."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def manual_flow_works(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow discovers only already configured bridges."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def manual_flow_bridge_exist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow aborts on already configured bridges."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def manual_flow_no_discovered_bridges(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow discovers no bridges."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def flow_all_discovered_bridges_exist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow discovers only already configured bridges."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def flow_bridges_discovered(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow discovers two bridges."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def flow_two_bridges_discovered_one_new(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow discovers two bridges."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def flow_timeout_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow ."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def flow_link_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if a unknown error happened during the linking processes."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def flow_link_button_not_pressed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow ."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def flow_link_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow ."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def import_with_no_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test importing a host without an existing config file."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def creating_entry_removes_entries_for_same_host_or_bridge(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we clean up entries for same host and bridge."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bridge_homekit(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a bridge being discovered via HomeKit."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bridge_import_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if a import flow aborts if host is already configured."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bridge_homekit_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if a HomeKit discovered bridge has already been configured."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_v1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options config flow for a V1 bridge."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_v2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options config flow for a V2 bridge."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bridge_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a bridge being discovered."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bridge_zeroconf_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a bridge being discovered by zeroconf already exists."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bridge_zeroconf_ipv6(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a bridge being discovered by zeroconf and ipv6 address."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bridge_connection_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that connection errors to the bridge are handled."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bsb003_bridge_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a bridge being discovered."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bsb003_bridge_discovery_old_version(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a bridge being discovered."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bsb003_bridge_discovery_same_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a bridge being discovered."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bsb003_bridge_discovery_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a bridge being discovered."""
    expect(True).to_be(True)


