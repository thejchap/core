"""Tests for Victron Remote Monitoring integration setup and auth handling."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test
from victron_vrm.exceptions import AuthenticationError, VictronVRMError

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_vrm_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local anchor fixture (tryke discovery quirk)."""


@test.cases(
    test.case(
        "auth_error_starts_reauth",
        side_effect=AuthenticationError("bad", status_code=401),
        expected_state=ConfigEntryState.SETUP_ERROR,
        expects_reauth=True,
    ),
    test.case(
        "vrm_error_retries",
        side_effect=VictronVRMError("boom", status_code=500, response_data={}),
        expected_state=ConfigEntryState.SETUP_RETRY,
        expects_reauth=False,
    ),
)
async def setup_auth_or_connection_error_starts_retry_or_reauth(
    *,
    side_effect: Exception,
    expected_state: ConfigEntryState,
    expects_reauth: bool,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    vrm_client: AsyncMock = Depends(mock_vrm_client),
) -> None:
    """Auth errors initiate reauth flow; other errors set entry to retry."""
    config_entry.add_to_hass(hass)
    vrm_client.installations.stats.side_effect = side_effect

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(expected_state)
    flows_list = list(config_entry.async_get_active_flows(hass, {SOURCE_REAUTH}))
    expect(bool(flows_list)).to_be(expects_reauth)
