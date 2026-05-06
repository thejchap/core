"""Tests for the Abode module."""

from http import HTTPStatus
from unittest.mock import patch

from jaraco.abode.exceptions import (
    AuthenticationException as AbodeAuthenticationException,
    Exception as AbodeException,
)
import requests_mock
from tryke import Depends, expect, fixture, test

from homeassistant.components.abode.const import DOMAIN
from homeassistant.components.alarm_control_panel import DOMAIN as ALARM_DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant

from ._fixtures import requests_mock_fixture
from .common import setup_platform

from tests.hass_fixtures import hass as hass_fixture


@fixture
def _abode_setup(
    _requests: requests_mock.Mocker = Depends(requests_mock_fixture),
) -> None:
    """Provide module-local executor entry that wires the requests mock."""


@test
async def change_settings(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test change_setting service."""
    await setup_platform(hass, ALARM_DOMAIN)

    with patch("jaraco.abode.client.Client.set_setting") as mock_set_setting:
        await hass.services.async_call(
            DOMAIN,
            "change_setting",
            {"setting": "confirm_snd", "value": "loud"},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_setting.assert_called_once()


@test
async def add_unique_id(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test unique_id is set to Abode username."""
    mock_entry = await setup_platform(hass, ALARM_DOMAIN)
    # Set unique_id to None to match previous config entries
    hass.config_entries.async_update_entry(entry=mock_entry, unique_id=None)
    await hass.async_block_till_done()

    expect(mock_entry.unique_id).to_be(None)

    await hass.config_entries.async_reload(mock_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_entry.unique_id).to_equal(mock_entry.data[CONF_USERNAME])


@test
async def unload_entry(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test unloading the Abode entry."""
    mock_entry = await setup_platform(hass, ALARM_DOMAIN)

    with (
        patch("jaraco.abode.client.Client.logout") as mock_logout,
        patch("jaraco.abode.event_controller.EventController.stop") as mock_events_stop,
    ):
        expect(await hass.config_entries.async_unload(mock_entry.entry_id)).to_be(True)
    mock_logout.assert_called_once()
    mock_events_stop.assert_called_once()


@test
async def invalid_credentials(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Abode credentials changing."""
    with patch(
        "homeassistant.components.abode.Abode",
        side_effect=AbodeAuthenticationException(
            (HTTPStatus.BAD_REQUEST, "auth error")
        ),
    ):
        config_entry = await setup_platform(hass, ALARM_DOMAIN)
        await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["step_id"]).to_equal("reauth_confirm")

    hass.config_entries.flow.async_abort(flows[0]["flow_id"])
    expect(hass.config_entries.flow.async_progress()).to_equal([])


@test
async def raise_config_entry_not_ready_when_offline(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Config entry state is SETUP_RETRY when abode is offline."""
    with patch(
        "homeassistant.components.abode.Abode",
        side_effect=AbodeException("any"),
    ):
        config_entry = await setup_platform(hass, ALARM_DOMAIN)
        await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)

    expect(hass.config_entries.flow.async_progress()).to_equal([])
