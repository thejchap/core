"""Tests for the binary sensor platform of the Pterodactyl integration."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, patch

from requests.exceptions import ConnectionError as RequestsConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.const import STATE_ON, STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_pterodactyl as mock_pterodactyl_fx,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import freezer as freezer_fx, hass as hass_fixture

_FAKE_TRANSLATIONS = {
    "component.pterodactyl.entity.binary_sensor.status.name": "Status",
}


async def _fake_get_translations(
    hass: Any, language: Any, category: Any, integrations: Any = None,
    config_flow: Any = None,
) -> dict[str, str]:
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(
    hass: Any, language: Any, category: Any, integration: Any = None,
) -> dict[str, str]:
    return _FAKE_TRANSLATIONS


@contextmanager
def _patch_translations():
    with (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        yield


@fixture
def _trigger_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot (snapshot_platform)")
async def binary_sensor() -> None:
    """Stub for test_binary_sensor (port deferred — uses snapshot_platform)."""


@test
async def binary_sensor_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    _mock_pterodactyl: AsyncMock = Depends(mock_pterodactyl_fx),
    freezer=Depends(freezer_fx),
) -> None:
    """Test binary sensor update."""
    with _patch_translations():
        await setup_integration(hass, mock_config_entry)

    freezer.tick(timedelta(seconds=90))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all(Platform.BINARY_SENSOR))).to_equal(2)
    expect(
        hass.states.get(f"{Platform.BINARY_SENSOR}.test_server_1_status").state
    ).to_equal(STATE_ON)
    expect(
        hass.states.get(f"{Platform.BINARY_SENSOR}.test_server_2_status").state
    ).to_equal(STATE_ON)


@test
async def binary_sensor_update_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_pterodactyl: AsyncMock = Depends(mock_pterodactyl_fx),
    freezer=Depends(freezer_fx),
) -> None:
    """Test failed binary sensor update."""
    with _patch_translations():
        await setup_integration(hass, mock_config_entry)

    mock_pterodactyl.client.servers.get_server.side_effect = RequestsConnectionError(
        "Simulated connection error"
    )

    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    expect(len(hass.states.async_all(Platform.BINARY_SENSOR))).to_equal(2)
    expect(
        hass.states.get(f"{Platform.BINARY_SENSOR}.test_server_1_status").state
    ).to_equal(STATE_UNAVAILABLE)
    expect(
        hass.states.get(f"{Platform.BINARY_SENSOR}.test_server_2_status").state
    ).to_equal(STATE_UNAVAILABLE)
