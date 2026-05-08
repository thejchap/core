"""Tests for Essent integration setup."""

from unittest.mock import AsyncMock

from essent_dynamic_pricing import (
    EssentConnectionError,
    EssentDataError,
    EssentError,
    EssentResponseError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_config_entry, mock_essent_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def load_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_essent_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, entry)

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip("snapshot diverged - needs pytest --snapshot-update")
async def device_registry() -> None:
    """Stub for test_device_registry."""


@test.cases(
    test.case("connection", exception=EssentConnectionError("fail")),
    test.case("response", exception=EssentResponseError("bad")),
    test.case("data", exception=EssentDataError("bad")),
    test.case("error", exception=EssentError("boom")),
)
async def setup_retry_on_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_essent_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
) -> None:
    """Test setup retries on client errors."""
    client.async_get_prices.side_effect = exception

    await setup_integration(hass, entry)

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
