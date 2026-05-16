"""Tryke fixtures for shopping_list tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.shopping_list import intent as sl_intent
from homeassistant.components.shopping_list.common import PERSISTENCE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, tmp_path as tmp_path_fixture


@fixture
def shopping_list_tmp_path(
    tmp_path: Path = Depends(tmp_path_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[None]:
    """Use a unique temp directory for shopping list storage per test."""
    orig_path = hass.config.path

    def _mock_path(*args: str) -> str:
        if args == (PERSISTENCE,):
            return str(tmp_path / PERSISTENCE)
        return orig_path(*args)

    with patch.object(hass.config, "path", _mock_path):
        yield


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Config Entry fixture."""
    return MockConfigEntry(domain="shopping_list")


@fixture
async def sl_setup(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _tmp_path: None = Depends(shopping_list_tmp_path),
) -> AsyncGenerator[None]:
    """Set up the shopping list."""
    mock_config_entry.add_to_hass(hass)

    # Pre-register the entity in the entity registry with the expected
    # entity_id. Without translations pre-loaded the platform falls back
    # to a UUID-suffixed slug; pre-registering pins the canonical
    # ``todo.shopping_list`` slug regardless of translation state.
    entity_registry = er.async_get(hass)
    entity_registry.async_get_or_create(
        domain="todo",
        platform="shopping_list",
        unique_id=mock_config_entry.entry_id,
        suggested_object_id="shopping_list",
    )

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await sl_intent.async_setup_intents(hass)
    yield
