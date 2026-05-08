"""Tests for the Uptime Kuma integration."""

from unittest.mock import AsyncMock

from pythonkuma import (
    UptimeKumaAuthenticationException,
    UptimeKumaException,
    UptimeKumaParseException,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.uptime_kuma.const import DOMAIN
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_pythonkuma

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local anchor fixture (tryke discovery quirk)."""


@test
async def entry_setup_unload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _kuma: AsyncMock = Depends(mock_pythonkuma),
) -> None:
    """Test integration setup and unload."""
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "auth_error",
        exception=UptimeKumaAuthenticationException,
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "kuma_error",
        exception=UptimeKumaException,
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "parse_error",
        exception=UptimeKumaParseException,
        state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def config_entry_not_ready(
    *,
    exception: type[Exception],
    state: ConfigEntryState,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    kuma: AsyncMock = Depends(mock_pythonkuma),
) -> None:
    """Test config entry not ready."""
    kuma.metrics.side_effect = exception
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(state)


@test
async def config_reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    kuma: AsyncMock = Depends(mock_pythonkuma),
) -> None:
    """Test config entry auth error starts reauth flow."""
    kuma.metrics.side_effect = UptimeKumaAuthenticationException
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    flow = flows[0]
    expect(flow.get("step_id")).to_equal("reauth_confirm")
    expect(flow.get("handler")).to_equal(DOMAIN)

    expect("context" in flow).to_be(True)
    expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
    expect(flow["context"].get("entry_id")).to_equal(config_entry.entry_id)


@test.skip("uptime_kuma device-removal tests use hass_ws_client (port deferred)")
async def remove_stale_device() -> None:
    """Stub for test_remove_stale_device (port deferred)."""


@test.skip("uptime_kuma device-removal tests use hass_ws_client (port deferred)")
async def remove_current_device() -> None:
    """Stub for test_remove_current_device (port deferred)."""


@test.skip("uptime_kuma device-removal tests use hass_ws_client (port deferred)")
async def remove_entry_device() -> None:
    """Stub for test_remove_entry_device (port deferred)."""
