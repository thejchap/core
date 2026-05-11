"""Tests for the Fully Kiosk Browser integration."""

from unittest.mock import MagicMock

from fullykiosk import FullyKioskError
from tryke import Depends, expect, fixture, test

from homeassistant.components.fully_kiosk.const import DOMAIN
from homeassistant.components.fully_kiosk.entity import valid_global_mac_address
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_config_entry as mock_config_entry_fixture,
    mock_fully_kiosk as mock_fully_kiosk_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@test
def domain_const_importable() -> None:
    """Smoke test: the fully_kiosk integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.fully_kiosk.const import DOMAIN  # noqa: PLC0415

    expect(DOMAIN).to_equal("fully_kiosk")


@test
def valid_global_mac_address_check() -> None:
    """Test valid_global_mac_address function."""
    expect(bool(valid_global_mac_address("a1:bb:cc:dd:ee:ff"))).to_be(True)
    expect(bool(valid_global_mac_address("02:00:00:00:00:00"))).to_be(False)
    expect(bool(valid_global_mac_address(None))).to_be(False)
    expect(bool(valid_global_mac_address("foobar"))).to_be(False)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def load_unload_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_fully_kiosk: MagicMock = Depends(mock_fully_kiosk_fixture),
) -> None:
    """Test the Fully Kiosk Browser configuration entry loading/unloading."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(mock_fully_kiosk.getDeviceInfo.mock_calls)).to_equal(1)
    expect(len(mock_fully_kiosk.getSettings.mock_calls)).to_equal(1)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(hass.data.get(DOMAIN)).to_be(None)
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case("fully_kiosk_error", side_effect=FullyKioskError("error", "status")),
    test.case("timeout_error", side_effect=TimeoutError()),
)
async def config_entry_not_ready(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_fully_kiosk: MagicMock = Depends(mock_fully_kiosk_fixture),
    *,
    side_effect: Exception,
) -> None:
    """Test the Fully Kiosk Browser configuration entry not ready."""
    mock_fully_kiosk.getDeviceInfo.side_effect = side_effect

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.skip("multiple_kiosk_with_empty_mac entity_ids need translation injection")
async def multiple_kiosk_with_empty_mac() -> None:
    """Stub for test_multiple_kiosk_with_empty_mac."""
