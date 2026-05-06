"""Test Agent DVR integration."""

from unittest.mock import AsyncMock, patch

from agent import AgentError
from tryke import Depends, expect, fixture, test

from homeassistant.components.agent_dvr.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import CONF_DATA, create_entry, init_integration

from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


async def _create_mocked_agent(available: bool = True):
    mocked_agent = AsyncMock()
    mocked_agent.is_available = available
    return mocked_agent


def _patch_init_agent(mocked_agent):
    return patch(
        "homeassistant.components.agent_dvr.Agent",
        return_value=mocked_agent,
    )


@test
async def setup_config_and_unload(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup and unload."""
    entry = await init_integration(hass, aioclient_mock)
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.data).to_equal(CONF_DATA)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def async_setup_entry_not_ready(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    entry = create_entry(hass)
    with patch(
        "homeassistant.components.agent_dvr.Agent.update",
        side_effect=AgentError,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    with _patch_init_agent(await _create_mocked_agent(available=False)):
        await hass.config_entries.async_reload(entry.entry_id)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
