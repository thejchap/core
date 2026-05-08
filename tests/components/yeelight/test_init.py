"""Test Yeelight (tryke port)."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test
from yeelight import BulbException, BulbType

from homeassistant.components.yeelight.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from . import MODULE, _mocked_bulb

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test.skip("yeelight: sibling test pending tryke port")
async def ip_changes_fallback_discovery() -> None:
    """Stub for test_ip_changes_fallback_discovery."""


@test
async def ip_changes_id_missing_cannot_fallback(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Yeelight ip changes and we fallback to discovery."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "5.5.5.5"})
    config_entry.add_to_hass(hass)

    mocked_bulb = _mocked_bulb(True)
    mocked_bulb.bulb_type = BulbType.WhiteTempMood
    mocked_bulb.async_listen = AsyncMock(side_effect=[BulbException, None, None, None])

    with patch(f"{MODULE}.AsyncBulb", return_value=mocked_bulb):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(
            False
        )
        await hass.async_block_till_done()

    expect(config_entry.state is ConfigEntryState.SETUP_RETRY).to_be(True)


@test.skip("yeelight: sibling test pending tryke port")
async def setup_discovery() -> None:
    """Stub for test_setup_discovery."""


@test.skip("yeelight: sibling test pending tryke port")
async def setup_discovery_with_manually_configured_network_adapter() -> None:
    """Stub for test_setup_discovery_with_manually_configured_network_adapter."""


@test.skip("yeelight: sibling test pending tryke port")
async def setup_discovery_with_manually_configured_network_adapter_one_fails() -> None:
    """Stub for test_setup_discovery_with_manually_configured_network_adapter_one_fails."""


@test.skip("yeelight: sibling test pending tryke port")
async def setup_import() -> None:
    """Stub for test_setup_import."""


@test.skip("yeelight: sibling test pending tryke port")
async def unique_ids_device() -> None:
    """Stub for test_unique_ids_device."""


@test.skip("yeelight: sibling test pending tryke port")
async def unique_ids_entry() -> None:
    """Stub for test_unique_ids_entry."""


@test.skip("yeelight: sibling test pending tryke port")
async def bulb_off_while_adding_in_ha() -> None:
    """Stub for test_bulb_off_while_adding_in_ha."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_listen_error_late_discovery() -> None:
    """Stub for test_async_listen_error_late_discovery."""


@test.skip("yeelight: sibling test pending tryke port")
async def fail_to_fetch_initial_state() -> None:
    """Stub for test_fail_to_fetch_initial_state."""


@test.skip("yeelight: sibling test pending tryke port")
async def unload_before_discovery() -> None:
    """Stub for test_unload_before_discovery."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_listen_error_has_host_with_id() -> None:
    """Stub for test_async_listen_error_has_host_with_id."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_listen_error_has_host_without_id() -> None:
    """Stub for test_async_listen_error_has_host_without_id."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_setup_with_missing_id() -> None:
    """Stub for test_async_setup_with_missing_id."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_setup_with_missing_unique_id() -> None:
    """Stub for test_async_setup_with_missing_unique_id."""


@test.skip("yeelight: sibling test pending tryke port")
async def connection_dropped_resyncs_properties() -> None:
    """Stub for test_connection_dropped_resyncs_properties."""


@test.skip("yeelight: sibling test pending tryke port")
async def oserror_on_first_update_results_in_unavailable() -> None:
    """Stub for test_oserror_on_first_update_results_in_unavailable."""


@test.skip("yeelight: sibling test pending tryke port")
async def non_oserror_exception_on_first_update() -> None:
    """Stub for test_non_oserror_exception_on_first_update."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_setup_with_discovery_not_working() -> None:
    """Stub for test_async_setup_with_discovery_not_working."""


@test.skip("yeelight: sibling test pending tryke port")
async def async_setup_retries_with_wrong_device() -> None:
    """Stub for test_async_setup_retries_with_wrong_device."""
