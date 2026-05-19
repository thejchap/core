"""Tryke fixtures for input_text tests."""

from collections.abc import Awaitable, Callable
from typing import Any

from tryke import Depends, fixture

from homeassistant.components.input_text import (
    ATTR_MAX,
    ATTR_MIN,
    ATTR_MODE,
    DOMAIN,
    MODE_TEXT,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
)
from tests.hass_tryke_helpers import setup_recorder_mock

TEST_VAL_MIN = 2
TEST_VAL_MAX = 22


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
):
    """Set up the recorder for tests that need it."""
    return await setup_recorder_mock(hass)


@fixture
def storage_setup(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> Callable[..., Awaitable[bool]]:
    """Storage setup."""

    async def _storage(
        items: list[dict[str, Any]] | None = None,
        config: dict[str, Any] | None = None,
    ) -> bool:
        if items is None:
            hass_storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {
                    "items": [
                        {
                            "id": "from_storage",
                            "name": "from storage",
                            "initial": "loaded from storage",
                            ATTR_MAX: TEST_VAL_MAX,
                            ATTR_MIN: TEST_VAL_MIN,
                            ATTR_MODE: MODE_TEXT,
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
