"""Test Cloud preferences."""

from typing import Any
from unittest.mock import ANY, patch

from tryke import Depends, expect, fixture, test

from homeassistant.auth.const import GROUP_ID_ADMIN
from homeassistant.components.cloud.prefs import STORAGE_KEY, CloudPreferences
from homeassistant.core import HomeAssistant

from ._fixtures import load_homeassistant

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _load_homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def set_username(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we clear config if we set different username."""
    prefs = CloudPreferences(hass)
    await prefs.async_initialize()

    expect(prefs.google_enabled).to_be(True)

    await prefs.async_update(google_enabled=False)

    expect(prefs.google_enabled).to_be(False)

    await prefs.async_set_username("new-username")

    expect(prefs.google_enabled).to_be(True)


@test
async def erase_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test erasing config."""
    prefs = CloudPreferences(hass)
    await prefs.async_initialize()
    expect(prefs._prefs).to_equal(
        {
            **prefs._empty_config(""),
            "google_local_webhook_id": ANY,
            "instance_id": ANY,
        }
    )

    await prefs.async_update(google_enabled=False)
    expect(prefs._prefs).to_equal(
        {
            **prefs._empty_config(""),
            "google_enabled": False,
            "google_local_webhook_id": ANY,
            "instance_id": ANY,
        }
    )

    await prefs.async_erase_config()
    expect(prefs._prefs).to_equal(
        {
            **prefs._empty_config(""),
            "google_local_webhook_id": ANY,
            "instance_id": ANY,
        }
    )


@test
async def set_username_migration(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we do not clear config if we had no username."""
    prefs = CloudPreferences(hass)

    with patch.object(prefs, "_empty_config", return_value=prefs._empty_config(None)):
        await prefs.async_initialize()

    expect(prefs.google_enabled).to_be(True)

    await prefs.async_update(google_enabled=False)

    expect(prefs.google_enabled).to_be(False)

    await prefs.async_set_username("new-username")

    expect(prefs.google_enabled).to_be(False)


@test
async def set_new_username(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test if setting new username returns true."""
    hass_storage[STORAGE_KEY] = {"version": 1, "data": {"username": "old-user"}}

    prefs = CloudPreferences(hass)
    await prefs.async_initialize()

    expect(await prefs.async_set_username("old-user")).to_be(False)

    expect(await prefs.async_set_username("new-user")).to_be(True)


@test
async def load_invalid_cloud_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test loading cloud user with invalid storage."""
    hass_storage[STORAGE_KEY] = {"version": 1, "data": {"cloud_user": "non-existing"}}

    prefs = CloudPreferences(hass)
    await prefs.async_initialize()

    cloud_user_id = await prefs.get_cloud_user()

    expect(cloud_user_id != "non-existing").to_be(True)

    cloud_user = await hass.auth.async_get_user(
        hass_storage[STORAGE_KEY]["data"]["cloud_user"]
    )

    expect(cloud_user is not None).to_be(True)
    expect(cloud_user.groups[0].id).to_equal(GROUP_ID_ADMIN)


@test
async def setup_remove_cloud_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test creating and removing cloud user."""
    hass_storage[STORAGE_KEY] = {"version": 1, "data": {"cloud_user": None}}

    prefs = CloudPreferences(hass)
    await prefs.async_initialize()
    await prefs.async_set_username("user1")

    cloud_user = await hass.auth.async_get_user(await prefs.get_cloud_user())

    expect(cloud_user is not None).to_be(True)
    expect(cloud_user.groups[0].id).to_equal(GROUP_ID_ADMIN)

    await prefs.async_set_username("user2")

    cloud_user2 = await hass.auth.async_get_user(await prefs.get_cloud_user())

    expect(cloud_user2 is not None).to_be(True)
    expect(cloud_user2.groups[0].id).to_equal(GROUP_ID_ADMIN)
    expect(cloud_user2.id != cloud_user.id).to_be(True)


@test.cases(
    test.case("empty_users", google_assistant_users=[], google_connected=False),
    test.case(
        "cloud_user", google_assistant_users=["cloud-user"], google_connected=True
    ),
    test.case(
        "other_user", google_assistant_users=["other-user"], google_connected=False
    ),
)
async def import_google_assistant_settings(
    *,
    google_assistant_users: list[str],
    google_connected: bool,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test importing from the google assistant store."""
    hass_storage[STORAGE_KEY] = {"version": 1, "data": {"username": "cloud-user"}}

    with patch(
        "homeassistant.components.cloud.prefs.async_get_google_assistant_users"
    ) as mock_get_users:
        mock_get_users.return_value = google_assistant_users
        prefs = CloudPreferences(hass)
        await prefs.async_initialize()
        expect(prefs.google_connected).to_be(google_connected)


@test.skip("requires cloud fixture (full hass_nabucasa.Cloud mock)")
async def tts_default_voice_legacy_gender() -> None:
    """Stub for test_tts_default_voice_legacy_gender."""
