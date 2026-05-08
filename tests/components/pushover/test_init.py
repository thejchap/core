"""Test pushover integration."""

from __future__ import annotations

from unittest.mock import MagicMock

from pushover_complete import BadAPIRequestError
from requests_mock import Mocker
from tryke import Depends, expect, fixture, test
from urllib3.exceptions import MaxRetryError

from homeassistant.components.pushover.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import MOCK_CONFIG
from ._fixtures import mock_pushover as mock_pushover_fx

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import requests_mock_session


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def async_setup_entry_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_pushover: MagicMock = Depends(mock_pushover_fx),
) -> None:
    """Test pushover successful setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def unique_id_updated(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_pushover: MagicMock = Depends(mock_pushover_fx),
) -> None:
    """Test updating unique_id to new format."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, unique_id="MYUSERKEY")
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(entry.unique_id).to_be(None)


@test
async def async_setup_entry_failed_invalid_api_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pushover: MagicMock = Depends(mock_pushover_fx),
) -> None:
    """Test pushover failed setup due to invalid api key."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    mock_pushover.side_effect = BadAPIRequestError("400: application token is invalid")
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def async_setup_entry_failed_conn_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pushover: MagicMock = Depends(mock_pushover_fx),
) -> None:
    """Test pushover failed setup due to conn error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    mock_pushover.side_effect = BadAPIRequestError
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def async_setup_entry_failed_json_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock_fx: Mocker = Depends(requests_mock_session),
) -> None:
    """Test pushover failed setup due to bad json response from library."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    requests_mock_fx.post(
        "https://api.pushover.net/1/users/validate.json", status_code=204
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def async_setup_entry_failed_urrlib3_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pushover: MagicMock = Depends(mock_pushover_fx),
) -> None:
    """Test pushover failed setup due to conn error (urllib3)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    mock_pushover.side_effect = MaxRetryError(MagicMock(), MagicMock())
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
