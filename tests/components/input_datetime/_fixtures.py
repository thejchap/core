"""Tryke fixtures for the input_datetime integration tests."""

from collections.abc import Awaitable, Callable
from typing import Any

from tryke import Depends, fixture

from homeassistant.components.input_datetime import (
    CONF_HAS_DATE,
    CONF_HAS_TIME,
    CONF_ID,
    CONF_INITIAL,
    CONF_NAME,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
)
from tests.hass_tryke_helpers import setup_recorder_mock

INITIAL_DATE = "2020-01-10"
INITIAL_TIME = "23:45:56"
INITIAL_DATETIME = f"{INITIAL_DATE} {INITIAL_TIME}"


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
                            CONF_ID: "from_storage",
                            CONF_NAME: "datetime from storage",
                            CONF_INITIAL: INITIAL_DATETIME,
                            CONF_HAS_DATE: True,
                            CONF_HAS_TIME: True,
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
