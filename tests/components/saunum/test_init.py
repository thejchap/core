"""Test Saunum Leil integration setup and teardown."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pysaunum import SaunumConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_saunum_client as mock_saunum_client_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def setup_and_unload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    _mock_saunum_client: MagicMock = Depends(mock_saunum_client_fx),
) -> None:
    """Test integration setup and unload."""
    mock_config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(mock_config_entry.entry_id)).to_be(
        True
    )
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(mock_config_entry.entry_id)).to_be(
        True
    )
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def async_setup_entry_connection_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    _mock_saunum_client: MagicMock = Depends(mock_saunum_client_fx),
) -> None:
    """Test integration setup fails when connection cannot be established."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.saunum.SaunumClient.create",
        side_effect=SaunumConnectionError("Connection failed"),
    ):
        expect(
            await hass.config_entries.async_setup(mock_config_entry.entry_id)
        ).to_be(False)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.skip("syrupy snapshot (device_entry)")
async def device_entry() -> None:
    """Stub for test_device_entry (port deferred)."""
