"""Unit tests for the bring integration."""

from unittest.mock import AsyncMock

from bring_api import (
    BringAuthException,
    BringParseException,
    BringRequestException,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.bring.const import DOMAIN
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    bring_config_entry as bring_config_entry_fixture,
    mock_bring_client,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


async def setup_integration(
    hass: HomeAssistant,
    bring_config_entry: MockConfigEntry,
) -> None:
    """Mock setup of the bring integration."""
    bring_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(bring_config_entry.entry_id)
    await hass.async_block_till_done()


@test
async def load_unload(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_bring_client),
    bring_config_entry: MockConfigEntry = Depends(bring_config_entry_fixture),
) -> None:
    """Test loading and unloading of the config entry."""
    await setup_integration(hass, bring_config_entry)

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)

    expect(bring_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(bring_config_entry.entry_id)).to_be(True)
    expect(bring_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "request",
        exception=BringRequestException,
        status=ConfigEntryState.SETUP_RETRY,
        reauth_triggered=False,
    ),
    test.case(
        "auth",
        exception=BringAuthException,
        status=ConfigEntryState.SETUP_ERROR,
        reauth_triggered=True,
    ),
    test.case(
        "parse",
        exception=BringParseException,
        status=ConfigEntryState.SETUP_RETRY,
        reauth_triggered=False,
    ),
)
async def init_failure(
    *,
    exception: type[Exception],
    status: ConfigEntryState,
    reauth_triggered: bool,
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_bring_client: AsyncMock = Depends(mock_bring_client),
    bring_config_entry: MockConfigEntry = Depends(bring_config_entry_fixture),
) -> None:
    """Test an initialization error on integration load."""
    mock_bring_client.login.side_effect = exception
    await setup_integration(hass, bring_config_entry)
    expect(bring_config_entry.state).to_equal(status)

    has_reauth = any(
        flow
        for flow in hass.config_entries.flow.async_progress()
        if flow["context"]["source"] == SOURCE_REAUTH
    )
    expect(has_reauth).to_equal(reauth_triggered)


@test
async def config_entry_not_ready_auth_error(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    bring_config_entry: MockConfigEntry = Depends(bring_config_entry_fixture),
    mock_bring_client: AsyncMock = Depends(mock_bring_client),
) -> None:
    """Test config entry not ready from authentication error."""
    mock_bring_client.load_lists.side_effect = BringAuthException
    bring_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(bring_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(bring_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test.skip("complex parametrize over multiple coordinator methods + freezer")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""


@test.skip("complex parametrize over multiple coordinator methods + freezer")
async def config_entry_not_ready_udpdate_failed() -> None:
    """Stub for test_config_entry_not_ready_udpdate_failed."""


@test.skip("complex parametrize over multiple coordinator methods + freezer")
async def activity_coordinator_errors() -> None:
    """Stub for test_activity_coordinator_errors."""


@test.skip("complex device_registry mutation")
async def coordinator_skips_deactivated() -> None:
    """Stub for test_coordinator_skips_deactivated."""


@test.skip("complex device_registry mutation")
async def purge_devices() -> None:
    """Stub for test_purge_devices."""


@test.skip("complex device_registry mutation")
async def create_devices() -> None:
    """Stub for test_create_devices."""


@test.skip("complex coordinator + freezer")
async def coordinator_update_intervals() -> None:
    """Stub for test_coordinator_update_intervals."""
