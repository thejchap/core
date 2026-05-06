"""Test init of acaia integration."""

from datetime import timedelta
from unittest.mock import MagicMock

from aioacaia.exceptions import AcaiaDeviceNotFound, AcaiaError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import init_integration, mock_config_entry, mock_scale

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import freezer as freezer_fixture, hass as hass_fixture


@fixture
def _ensure_executor() -> None:
    """Force tryke to build a per-module HookExecutor for this file.

    Tryke statically discovers ``@fixture``-decorated names within the
    test module; if a module only consumes fixtures via imports, the
    executor is never built and ``Depends`` defaults are not resolved.
    """


@test
async def load_unload_config_entry(
    _setup: MockConfigEntry = Depends(init_integration),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test loading and unloading the integration."""
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case("AcaiaError", exception=AcaiaError()),
    test.case("AcaiaDeviceNotFound", exception=AcaiaDeviceNotFound("Boom")),
    test.case("TimeoutError", exception=TimeoutError()),
)
async def update_exception_leads_to_active_disconnect(
    exception: Exception,
    _setup: MockConfigEntry = Depends(init_integration),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_scale: MagicMock = Depends(mock_scale),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test scale gets disconnected on exception."""
    mock_scale.connect.side_effect = exception
    mock_scale.connected = False

    freezer.tick(timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    mock_scale.device_disconnected_handler.assert_called_once()


@test.skip("uses syrupy snapshot")
async def device() -> None:
    """Snapshot the device from registry."""
