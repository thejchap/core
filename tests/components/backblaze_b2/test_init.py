"""Test the Backblaze B2 storage integration."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from b2sdk.v2 import exception
from tryke import Depends, expect, fixture, test

from homeassistant.components.backblaze_b2.const import CONF_APPLICATION_KEY
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import b2_fixture, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def load_unload_config_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test loading and unloading the integration."""
    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def setup_entry_invalid_auth(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setup entry with invalid auth."""
    mock_config = MockConfigEntry(
        entry_id=mock_config_entry.entry_id,
        title=mock_config_entry.title,
        domain=mock_config_entry.domain,
        data={
            **mock_config_entry.data,
            CONF_APPLICATION_KEY: "invalid_key_id",
        },
    )

    await setup_integration(hass, mock_config)

    expect(mock_config.state).to_be(ConfigEntryState.SETUP_ERROR)


@test.cases(
    test.case(
        "unauthorized",
        exc=exception.Unauthorized("msg", "code"),
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "restricted_bucket",
        exc=exception.RestrictedBucket("testBucket"),
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "non_existent_bucket",
        exc=exception.NonExistentBucket(),
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "connection_reset",
        exc=exception.ConnectionReset(),
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "bad_request",
        exc=exception.BadRequest("test", "bad_request"),
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "missing_account_data",
        exc=exception.MissingAccountData("key"),
        state=ConfigEntryState.SETUP_ERROR,
    ),
)
async def setup_entry_restricted_bucket(
    exc: Exception,
    state: ConfigEntryState,
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setup entry with restricted bucket."""
    with patch(
        "b2sdk.v2.RawSimulator.get_bucket_by_name",
        side_effect=exc,
    ):
        await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(state)


@test
async def periodic_issue_check(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test periodic issue check functionality."""
    captured_callback = None

    def capture_callback(hass, callback, interval):
        nonlocal captured_callback
        captured_callback = callback
        return MagicMock()

    with (
        patch(
            "homeassistant.components.backblaze_b2.async_check_for_repair_issues",
            new_callable=AsyncMock,
        ) as mock_check,
        patch(
            "homeassistant.components.backblaze_b2.async_track_time_interval",
            side_effect=capture_callback,
        ),
    ):
        await setup_integration(hass, mock_config_entry)
        expect(captured_callback).not_.to_be(None)
        await captured_callback(datetime.now())

        expect(mock_check.call_count).to_equal(2)
        mock_check.assert_called_with(hass, mock_config_entry)
