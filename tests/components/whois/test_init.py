"""Tests for the Whois integration."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test
from whois.exceptions import (
    FailedParsingWhoisOutput,
    UnknownDateFormat,
    UnknownTld,
    WhoisCommandFailed,
)

from homeassistant.components.whois.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_whois

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local anchor fixture (tryke discovery quirk)."""


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    whois_mock: MagicMock = Depends(mock_whois),
) -> None:
    """Test the Whois configuration entry loading/unloading."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(whois_mock.mock_calls)).to_equal(1)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(bool(hass.data.get(DOMAIN))).to_be(False)
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case("failed_parsing", side_effect=FailedParsingWhoisOutput),
    test.case("unknown_date_format", side_effect=UnknownDateFormat),
    test.case("unknown_tld", side_effect=UnknownTld),
    test.case("whois_command_failed", side_effect=WhoisCommandFailed),
)
async def error_handling(
    *,
    side_effect: type[Exception],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    whois_mock: MagicMock = Depends(mock_whois),
) -> None:
    """Test the Whois threw an error."""
    config_entry.add_to_hass(hass)
    whois_mock.side_effect = side_effect

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    expect(len(whois_mock.mock_calls)).to_equal(1)
