"""BleBox devices setup tests."""

import logging

import blebox_uniapi
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .conftest import mock_config, patch_product_identify, setup_product_mock

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def setup_failure(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that setup failure is handled and logged."""
    patch_product_identify(None, side_effect=blebox_uniapi.error.ClientError)

    entry = mock_config()
    entry.add_to_hass(hass)

    caplog.set_level(logging.ERROR)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect("Identify failed at 172.100.123.4:80 ()" in caplog.text).to_be(True)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_failure_on_connection(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that setup failure is handled and logged."""
    patch_product_identify(None, side_effect=blebox_uniapi.error.ConnectionError)

    entry = mock_config()
    entry.add_to_hass(hass)

    caplog.set_level(logging.ERROR)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect("Identify failed at 172.100.123.4:80 ()" in caplog.text).to_be(True)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that unloading works properly."""
    setup_product_mock("switches", [])

    entry = mock_config()
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(hasattr(entry, "runtime_data")).to_be(True)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    expect(hasattr(entry, "runtime_data")).to_be(False)

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
