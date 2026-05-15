"""Tests for derivative diagnostics."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from ._fixtures import derivative_config_entry

from tests.common import MockConfigEntry
from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    mock_network,
)
from tests.typing import ClientSessionGenerator


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def diagnostics(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    config_entry: MockConfigEntry = Depends(derivative_config_entry),
) -> None:
    """Test diagnostics for config entry."""
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await get_diagnostics_for_config_entry(hass, hass_client, config_entry)

    expect(isinstance(result, dict)).to_be(True)
    expect(result["config_entry"]["domain"]).to_equal("derivative")
    expect(result["config_entry"]["options"]["name"]).to_equal("My derivative")
    expect(result["entity"][0]["entity_id"]).to_equal("sensor.my_derivative")


_ = (derivative_config_entry,)
