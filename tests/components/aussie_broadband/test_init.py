"""Test the Aussie Broadband init."""

from unittest.mock import patch

from aiohttp import ClientConnectionError
from aussiebb.exceptions import AuthenticationException, UnrecognisedServiceType
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .common import setup_platform

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def unload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test unload."""
    entry = await setup_platform(hass)
    expect(bool(await hass.config_entries.async_unload(entry.entry_id))).to_be(True)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def auth_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init with an authentication failure."""
    with patch(
        "homeassistant.components.aussie_broadband.config_flow.AussieBroadbandConfigFlow.async_step_reauth",
        return_value={
            "type": FlowResultType.FORM,
            "flow_id": "mock_flow",
            "step_id": "reauth_confirm",
            "description_placeholders": {"username": "test", "name": "test"},
            "data_schema": None,
        },
    ) as mock_async_step_reauth:
        await setup_platform(hass, side_effect=AuthenticationException())
        mock_async_step_reauth.assert_called_once()


@test
async def net_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init with a network failure."""
    entry = await setup_platform(hass, side_effect=ClientConnectionError())
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def service_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init with a invalid service."""
    entry = await setup_platform(hass, usage_effect=UnrecognisedServiceType())
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
