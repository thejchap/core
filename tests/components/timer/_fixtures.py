"""Tryke fixtures for the timer tests."""

from __future__ import annotations

from collections.abc import Callable, Coroutine, Generator
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.timer import (
    ATTR_DURATION,
    ATTR_RESTORE,
    DOMAIN,
)
from homeassistant.const import ATTR_ID, ATTR_NAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.components.common import target_entities
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
)


@fixture
def enable_labs_preview_features() -> Generator[None]:
    """Enable labs preview features."""
    with patch(
        "homeassistant.components.labs.async_is_preview_feature_enabled",
        return_value=True,
    ):
        yield


@fixture
async def target_timers(
    hass: HomeAssistant = Depends(hass_fixture),
) -> dict[str, list[str]]:
    """Create multiple timer entities associated with different targets."""
    return await target_entities(hass, DOMAIN)


@fixture
def storage_setup(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> Callable[..., Coroutine[Any, Any, bool]]:
    """Storage setup."""

    async def _storage(items=None, config=None):
        if items is None:
            hass_storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {
                    "items": [
                        {
                            ATTR_ID: "from_storage",
                            ATTR_NAME: "timer from storage",
                            ATTR_DURATION: "0:00:00",
                            ATTR_RESTORE: False,
                        }
                    ]
                },
            }
        else:
            hass_storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {"items": items},
            }
        if config is None:
            config = {DOMAIN: {}}
        return await async_setup_component(hass, DOMAIN, config)

    return _storage
