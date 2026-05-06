"""Tests for the Altruist integration sensor platform."""

from datetime import timedelta
from unittest.mock import AsyncMock

from altruistclient import AltruistError
from tryke import Depends, expect, fixture, test

from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant

from ._fixtures import mock_altruist_client, mock_config_entry

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("uses syrupy snapshot")
async def all_entities() -> None:
    """Test all entities."""


@test
async def connection_error(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_altruist_client: AsyncMock = Depends(mock_altruist_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test coordinator error handling during update."""
    mock_config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(mock_config_entry.entry_id)).to_be(
        True
    )
    await hass.async_block_till_done()

    mock_altruist_client.fetch_data.side_effect = AltruistError()

    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(
        hass.states.get("sensor.5366960e8b18_bme280_temperature").state
    ).to_equal(STATE_UNAVAILABLE)
