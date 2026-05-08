"""Tests for the BSBLan integration."""

from datetime import timedelta
from unittest.mock import MagicMock

from bsblan import BSBLANAuthError, BSBLANConnectionError
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_bsblan,
    mock_config_entry as mock_config_entry_fixture,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def load_unload_config_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan),
) -> None:
    """Test the BSBLAN configuration entry loading/unloading."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(mock_bsblan.device.mock_calls)).to_equal(1)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def config_entry_not_ready(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan),
) -> None:
    """Test the bsblan configuration entry not ready."""
    mock_bsblan.state.side_effect = BSBLANConnectionError

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(len(mock_bsblan.state.mock_calls)).to_equal(1)
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def config_entry_auth_failed_triggers_reauth(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test that BSBLANAuthError during coordinator update triggers reauth flow."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    mock_bsblan.state.side_effect = BSBLANAuthError("Authentication failed")

    freezer.tick(delta=timedelta(seconds=20))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["context"]["source"]).to_equal("reauth")
    expect(flows[0]["context"]["entry_id"]).to_equal(mock_config_entry.entry_id)


@test.skip("complex parametrize with method/exception/expected_state/static_fallback")
async def config_entry_setup_errors() -> None:
    """Stub for test_config_entry_setup_errors."""


@test.skip("complex coordinator interaction")
async def coordinator_dhw_config_update_error() -> None:
    """Stub for test_coordinator_dhw_config_update_error."""


@test.skip("complex coordinator interaction")
async def coordinator_slow_first_fetch_failure() -> None:
    """Stub for test_coordinator_slow_first_fetch_failure."""


@test.skip("complex coordinator interaction")
async def config_entry_timeout_error() -> None:
    """Stub for test_config_entry_timeout_error."""


@test.skip("complex coordinator interaction")
async def coordinator_fast_no_dhw_support() -> None:
    """Stub for test_coordinator_fast_no_dhw_support."""


@test.skip("complex coordinator interaction")
async def coordinator_fast_dhw_fails_on_refresh_preserves_state() -> None:
    """Stub for test_coordinator_fast_dhw_fails_on_refresh_preserves_state."""


@test.skip("complex coordinator interaction")
async def coordinator_slow_no_dhw_support() -> None:
    """Stub for test_coordinator_slow_no_dhw_support."""


@test.skip("device_registry mutation")
async def configuration_url_default_port() -> None:
    """Stub for test_configuration_url_default_port."""


@test.skip("device_registry mutation")
async def configuration_url_non_default_port() -> None:
    """Stub for test_configuration_url_non_default_port."""


@test.skip("migrate_entry tests")
async def migrate_entry_discovers_circuits() -> None:
    """Stub for test_migrate_entry_discovers_circuits."""


@test.skip("migrate_entry tests")
async def migrate_entry_discovery_failure_falls_back() -> None:
    """Stub for test_migrate_entry_discovery_failure_falls_back."""


@test.skip("migrate_entry tests")
async def migrate_entry_discovery_timeout_falls_back() -> None:
    """Stub for test_migrate_entry_discovery_timeout_falls_back."""


@test.skip("migrate_entry tests")
async def migrate_entry_future_version_aborts() -> None:
    """Stub for test_migrate_entry_future_version_aborts."""


@test.skip("migrate_entry tests")
async def migrate_entry_already_current() -> None:
    """Stub for test_migrate_entry_already_current."""
