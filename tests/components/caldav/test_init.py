"""Unit tests for the CalDav integration."""

from unittest.mock import patch

from caldav.lib.error import AuthorizationError, DAVError
import requests
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import config_entry as config_entry_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@fixture
def add_to_hass(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> MockConfigEntry:
    """Add the config_entry to hass."""
    config_entry.add_to_hass(hass)
    return config_entry


@test
async def load_unload(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(add_to_hass),
) -> None:
    """Test loading and unloading of the config entry."""
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)

    with patch("homeassistant.components.caldav.config_flow.caldav.DAVClient"):
        await hass.config_entries.async_setup(config_entry.entry_id)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "exception",
        side_effect=Exception(),
        expected_state=ConfigEntryState.SETUP_ERROR,
        expected_flows=[],
    ),
    test.case(
        "connection_error",
        side_effect=requests.ConnectionError(),
        expected_state=ConfigEntryState.SETUP_RETRY,
        expected_flows=[],
    ),
    test.case(
        "dav_error",
        side_effect=DAVError(),
        expected_state=ConfigEntryState.SETUP_RETRY,
        expected_flows=[],
    ),
    test.case(
        "auth_unauthorized",
        side_effect=AuthorizationError(reason="Unauthorized"),
        expected_state=ConfigEntryState.SETUP_ERROR,
        expected_flows=["reauth_confirm"],
    ),
    test.case(
        "auth_other",
        side_effect=AuthorizationError(reason="Other"),
        expected_state=ConfigEntryState.SETUP_ERROR,
        expected_flows=[],
    ),
)
async def client_failure(
    *,
    side_effect: Exception,
    expected_state: ConfigEntryState,
    expected_flows: list[str],
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(add_to_hass),
) -> None:
    """Test CalDAV client failures in setup."""
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)

    with patch(
        "homeassistant.components.caldav.config_flow.caldav.DAVClient"
    ) as mock_client:
        mock_client.return_value.principal.side_effect = side_effect
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    expect(config_entry.state).to_equal(expected_state)

    flows = hass.config_entries.flow.async_progress()
    expect([flow.get("step_id") for flow in flows]).to_equal(expected_flows)
