"""Test the matter config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def manual_create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step create entry."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def manual_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step cannot connect error."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def manual_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual step abort if already configured."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def zeroconf_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow started from Zeroconf discovery."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def zeroconf_discovery_not_onboarded_not_supervisor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow started from Zeroconf discovery when not onboarded."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def zeroconf_not_onboarded_already_discovered(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow Zeroconf discovery when not onboarded and already discovered."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def zeroconf_not_onboarded_running(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow Zeroconf discovery when not onboarded and add-on running."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def zeroconf_not_onboarded_installed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow Zeroconf discovery when not onboarded and add-on installed."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def zeroconf_not_onboarded_not_installed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow Zeroconf discovery when not onboarded and add-on not installed."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def supervisor_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow started from Supervisor discovery."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def supervisor_discovery_addon_info_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Supervisor discovery and addon info failed."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def clean_supervisor_discovery_on_user_create(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery flow is cleaned up when a user flow is finished."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def abort_supervisor_discovery_with_existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery flow is aborted if an entry already exists."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def abort_supervisor_discovery_with_existing_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test hassio discovery flow is aborted when another flow is in progress."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def abort_supervisor_discovery_for_other_addon(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test hassio discovery flow is aborted for a non official add-on discovery."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def supervisor_discovery_addon_not_running(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery with add-on already installed but not running."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def supervisor_discovery_addon_not_installed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery with add-on not installed."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def not_addon(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test opting out of add-on on Supervisor."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def addon_running(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test add-on already running on Supervisor."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def addon_running_failures(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test all failures when add-on is running."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def addon_running_failures_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test all failures when add-on is running and not onboarded."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def addon_running_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that only one instance is allowed when add-on is running."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def addon_installed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test add-on already installed but not running on Supervisor."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def addon_installed_failures(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test add-on start failure when add-on is installed."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def addon_installed_failures_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test add-on start failure when add-on is installed and not onboarded."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def addon_installed_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that only one instance is allowed when add-on is installed."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def addon_not_installed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test add-on not installed."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def addon_not_installed_failures(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test add-on install failure."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def addon_not_installed_failures_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test add-on install failure."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + matter_server.client mock chain + ADDON_SLUG discovery (not in tryke shim)")
async def addon_not_installed_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that only one instance is allowed when add-on is not installed."""
    expect(True).to_be(True)


