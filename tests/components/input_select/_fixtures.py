"""Tryke fixtures for the input_select integration tests."""

from collections.abc import Awaitable, Callable
from typing import Any

from tryke import Depends, fixture

from homeassistant.components.input_select import (
    DOMAIN,
    STORAGE_VERSION,
    STORAGE_VERSION_MINOR,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
)
from tests.hass_tryke_helpers import setup_recorder_mock


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
        minor_version: int = STORAGE_VERSION_MINOR,
    ) -> bool:
        if items is None:
            hass_storage[DOMAIN] = {
                "key": DOMAIN,
                "version": STORAGE_VERSION,
                "minor_version": minor_version,
                "data": {
                    "items": [
                        {
                            "id": "from_storage",
                            "name": "from storage",
                            "options": ["storage option 1", "storage option 2"],
                        }
                    ]
                },
            }
        else:
            hass_storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "minor_version": minor_version,
                "data": {"items": items},
            }
        if config is None:
            config = {DOMAIN: {}}
        return await async_setup_component(hass, DOMAIN, config)

    return _storage
