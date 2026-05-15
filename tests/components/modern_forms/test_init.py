"""Tests for the Modern Forms integration."""

from unittest.mock import patch

from aiomodernforms import ModernFormsConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import init_integration, modern_forms_no_light_call_mock

from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def config_entry_not_ready(
    hass: HomeAssistant = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test the Modern Forms configuration entry not ready."""
    with patch(
        "homeassistant.components.modern_forms.coordinator.ModernFormsDevice.update",
        side_effect=ModernFormsConnectionError,
    ):
        entry = await init_integration(hass, aioclient_mock)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test the Modern Forms configuration entry unloading."""
    entry = await init_integration(hass, aioclient_mock)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip("requires translation injection for fan/light entity_id slugs")
async def fan_only_device() -> None:
    """Stub for test_fan_only_device (port deferred)."""
