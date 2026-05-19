"""Tests for Lovelace system health."""

from typing import Any
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.lovelace import dashboard
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import mock_onboarding_done as mock_onboarding_done_fx

from tests.common import get_system_health_info
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
)


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def system_health_info_autogen(
    hass: HomeAssistant = Depends(hass_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test system health info endpoint."""
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)
    expect(await async_setup_component(hass, "system_health", {})).to_be(True)
    info = await get_system_health_info(hass, "lovelace")
    expect(info).to_equal({"dashboards": 1, "mode": "auto-gen", "resources": 0})


@test
async def system_health_info_storage_migration(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test system health info endpoint after migration from old storage."""
    expect(await async_setup_component(hass, "system_health", {})).to_be(True)
    # Pre-populate old storage format (triggers migration)
    hass_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT] = {
        "key": "lovelace",
        "version": 1,
        "data": {"config": {"resources": [], "views": []}},
    }
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)
    await hass.async_block_till_done()
    info = await get_system_health_info(hass, "lovelace")
    # After migration: default dashboard (auto-gen) + migrated "lovelace" dashboard (storage with data)
    expect(info).to_equal(
        {"dashboards": 2, "mode": "storage", "resources": 0, "views": 0}
    )


@test
async def system_health_info_yaml(
    hass: HomeAssistant = Depends(hass_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test system health info endpoint."""
    expect(await async_setup_component(hass, "system_health", {})).to_be(True)
    expect(
        await async_setup_component(hass, "lovelace", {"lovelace": {"mode": "YAML"}})
    ).to_be(True)
    await hass.async_block_till_done()
    with patch(
        "homeassistant.components.lovelace.dashboard.load_yaml_dict",
        return_value={"views": [{"cards": []}]},
    ):
        info = await get_system_health_info(hass, "lovelace")
    # 2 dashboards: default storage (None) + yaml "lovelace" dashboard
    expect(info).to_equal(
        {"dashboards": 2, "mode": "yaml", "resources": 0, "views": 1}
    )


@test
async def system_health_info_yaml_not_found(
    hass: HomeAssistant = Depends(hass_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test system health info endpoint."""
    expect(await async_setup_component(hass, "system_health", {})).to_be(True)
    expect(
        await async_setup_component(hass, "lovelace", {"lovelace": {"mode": "YAML"}})
    ).to_be(True)
    await hass.async_block_till_done()
    info = await get_system_health_info(hass, "lovelace")
    # 2 dashboards: default storage (None) + yaml "lovelace" dashboard
    expect(info).to_equal(
        {
            "dashboards": 2,
            "mode": "yaml",
            "error": f"{hass.config.path('ui-lovelace.yaml')} not found",
            "resources": 0,
        }
    )
