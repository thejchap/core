"""Tryke fixtures for the person integration tests."""

from typing import Any

from tryke import Depends, fixture

from homeassistant.components.person import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockUser
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fixture,
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
async def storage_setup(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Storage setup."""
    hass_storage[DOMAIN] = {
        "key": DOMAIN,
        "version": 1,
        "data": {
            "persons": [
                {
                    "id": "1234",
                    "name": "tracked person",
                    "user_id": hass_admin_user.id,
                    "device_trackers": ["device_tracker.test_tracker"],
                }
            ]
        },
    }
    assert await async_setup_component(hass, DOMAIN, {})
