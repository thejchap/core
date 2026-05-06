"""Tests for the auth store."""

import asyncio
from typing import Any
from unittest.mock import PropertyMock, patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.auth import auth_store
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import freezer, hass, hass_storage


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


MOCK_STORAGE_DATA = {
    "version": 1,
    "data": {
        "credentials": [],
        "users": [
            {
                "id": "user-id",
                "is_active": True,
                "is_owner": True,
                "name": "Paulus",
                "system_generated": False,
            },
            {
                "id": "system-id",
                "is_active": True,
                "is_owner": True,
                "name": "Hass.io",
                "system_generated": True,
            },
        ],
        "refresh_tokens": [
            {
                "access_token_expiration": 1800.0,
                "client_id": "http://localhost:8123/",
                "created_at": "2018-10-03T13:43:19.774637+00:00",
                "id": "user-token-id",
                "jwt_key": "some-key",
                "last_used_at": "2018-10-03T13:43:19.774712+00:00",
                "token": "some-token",
                "user_id": "user-id",
                "version": "1.2.3",
            },
            {
                "access_token_expiration": 1800.0,
                "client_id": None,
                "created_at": "2018-10-03T13:43:19.774637+00:00",
                "id": "system-token-id",
                "jwt_key": "some-key",
                "last_used_at": "2018-10-03T13:43:19.774712+00:00",
                "token": "some-token",
                "user_id": "system-id",
            },
            {
                "access_token_expiration": 1800.0,
                "client_id": "http://localhost:8123/",
                "created_at": "2018-10-03T13:43:19.774637+00:00",
                "id": "hidden-because-no-jwt-id",
                "last_used_at": "2018-10-03T13:43:19.774712+00:00",
                "token": "some-token",
                "user_id": "user-id",
            },
        ],
    },
}


@test
async def loading_no_group_data_format(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test we correctly load old data without any groups."""
    hass_storage[auth_store.STORAGE_KEY] = MOCK_STORAGE_DATA

    store = auth_store.AuthStore(hass)
    await store.async_load()
    groups = await store.async_get_groups()
    expect(len(groups)).to_equal(3)
    admin_group = groups[0]
    expect(admin_group.name).to_equal(auth_store.GROUP_NAME_ADMIN)
    expect(admin_group.system_generated).to_be(True)
    expect(admin_group.id).to_equal(auth_store.GROUP_ID_ADMIN)
    read_group = groups[1]
    expect(read_group.name).to_equal(auth_store.GROUP_NAME_READ_ONLY)
    expect(read_group.system_generated).to_be(True)
    expect(read_group.id).to_equal(auth_store.GROUP_ID_READ_ONLY)
    user_group = groups[2]
    expect(user_group.name).to_equal(auth_store.GROUP_NAME_USER)
    expect(user_group.system_generated).to_be(True)
    expect(user_group.id).to_equal(auth_store.GROUP_ID_USER)

    users = await store.async_get_users()
    expect(len(users)).to_equal(2)

    owner, system = users

    expect(owner.system_generated).to_be(False)
    expect(owner.groups).to_equal([admin_group])
    expect(len(owner.refresh_tokens)).to_equal(1)
    owner_token = list(owner.refresh_tokens.values())[0]
    expect(owner_token.id).to_equal("user-token-id")
    expect(owner_token.version).to_equal("1.2.3")

    expect(system.system_generated).to_be(True)
    expect(system.groups).to_equal([])
    expect(len(system.refresh_tokens)).to_equal(1)
    system_token = list(system.refresh_tokens.values())[0]
    expect(system_token.id).to_equal("system-token-id")
    expect(system_token.version is None).to_be(True)


@test
async def loading_all_access_group_data_format(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test we correctly load old data with single group."""
    hass_storage[auth_store.STORAGE_KEY] = MOCK_STORAGE_DATA

    store = auth_store.AuthStore(hass)
    await store.async_load()
    groups = await store.async_get_groups()
    expect(len(groups)).to_equal(3)
    admin_group = groups[0]
    expect(admin_group.name).to_equal(auth_store.GROUP_NAME_ADMIN)
    expect(admin_group.system_generated).to_be(True)
    expect(admin_group.id).to_equal(auth_store.GROUP_ID_ADMIN)
    read_group = groups[1]
    expect(read_group.name).to_equal(auth_store.GROUP_NAME_READ_ONLY)
    expect(read_group.system_generated).to_be(True)
    expect(read_group.id).to_equal(auth_store.GROUP_ID_READ_ONLY)
    user_group = groups[2]
    expect(user_group.name).to_equal(auth_store.GROUP_NAME_USER)
    expect(user_group.system_generated).to_be(True)
    expect(user_group.id).to_equal(auth_store.GROUP_ID_USER)

    users = await store.async_get_users()
    expect(len(users)).to_equal(2)

    owner, system = users

    expect(owner.system_generated).to_be(False)
    expect(owner.groups).to_equal([admin_group])
    expect(len(owner.refresh_tokens)).to_equal(1)
    owner_token = list(owner.refresh_tokens.values())[0]
    expect(owner_token.id).to_equal("user-token-id")
    expect(owner_token.version).to_equal("1.2.3")

    expect(system.system_generated).to_be(True)
    expect(system.groups).to_equal([])
    expect(len(system.refresh_tokens)).to_equal(1)
    system_token = list(system.refresh_tokens.values())[0]
    expect(system_token.id).to_equal("system-token-id")
    expect(system_token.version is None).to_be(True)


@test
async def loading_empty_data(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test we correctly load with no existing data."""
    store = auth_store.AuthStore(hass)
    await store.async_load()
    groups = await store.async_get_groups()
    expect(len(groups)).to_equal(3)
    admin_group = groups[0]
    expect(admin_group.name).to_equal(auth_store.GROUP_NAME_ADMIN)
    expect(admin_group.system_generated).to_be(True)
    expect(admin_group.id).to_equal(auth_store.GROUP_ID_ADMIN)
    user_group = groups[1]
    expect(user_group.name).to_equal(auth_store.GROUP_NAME_USER)
    expect(user_group.system_generated).to_be(True)
    expect(user_group.id).to_equal(auth_store.GROUP_ID_USER)
    read_group = groups[2]
    expect(read_group.name).to_equal(auth_store.GROUP_NAME_READ_ONLY)
    expect(read_group.system_generated).to_be(True)
    expect(read_group.id).to_equal(auth_store.GROUP_ID_READ_ONLY)

    users = await store.async_get_users()
    expect(len(users)).to_equal(0)


@test
async def system_groups_store_id_and_name(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test that for system groups we store the ID and name."""
    store = auth_store.AuthStore(hass)
    await store.async_load()
    data = store._data_to_save()
    expect(len(data["users"])).to_equal(0)
    expect(data["groups"]).to_equal(
        [
            {"id": auth_store.GROUP_ID_ADMIN, "name": auth_store.GROUP_NAME_ADMIN},
            {"id": auth_store.GROUP_ID_USER, "name": auth_store.GROUP_NAME_USER},
            {"id": auth_store.GROUP_ID_READ_ONLY, "name": auth_store.GROUP_NAME_READ_ONLY},
        ]
    )


@test
async def loading_only_once(hass: HomeAssistant = Depends(hass)) -> None:
    """Test only one storage load is allowed."""
    store = auth_store.AuthStore(hass)
    with (
        patch("homeassistant.helpers.entity_registry.async_get") as mock_ent_registry,
        patch("homeassistant.helpers.device_registry.async_get") as mock_dev_registry,
        patch(
            "homeassistant.helpers.storage.Store.async_load", return_value=None
        ) as mock_load,
    ):
        await store.async_load()
        try:
            await store.async_load()
        except RuntimeError as err:
            expect("Auth storage is already loaded" in str(err)).to_be(True)
        else:
            raise AssertionError("Expected RuntimeError to be raised")

        results = await asyncio.gather(store.async_get_users(), store.async_get_users())

        mock_ent_registry.assert_called_once_with(hass)
        mock_dev_registry.assert_called_once_with(hass)
        mock_load.assert_called_once_with()
        expect(results[0]).to_equal(results[1])


@test
async def dont_change_expire_at_on_load(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test we correctly don't modify expired_at store load."""
    hass_storage[auth_store.STORAGE_KEY] = {
        "version": 1,
        "data": {
            "credentials": [],
            "users": [
                {
                    "id": "user-id",
                    "is_active": True,
                    "is_owner": True,
                    "name": "Paulus",
                    "system_generated": False,
                },
                {
                    "id": "system-id",
                    "is_active": True,
                    "is_owner": True,
                    "name": "Hass.io",
                    "system_generated": True,
                },
            ],
            "refresh_tokens": [
                {
                    "access_token_expiration": 1800.0,
                    "client_id": "http://localhost:8123/",
                    "created_at": "2018-10-03T13:43:19.774637+00:00",
                    "id": "user-token-id",
                    "jwt_key": "some-key",
                    "token": "some-token",
                    "user_id": "user-id",
                    "version": "1.2.3",
                },
                {
                    "access_token_expiration": 1800.0,
                    "client_id": "http://localhost:8123/",
                    "created_at": "2018-10-03T13:43:19.774637+00:00",
                    "id": "user-token-id2",
                    "jwt_key": "some-key2",
                    "token": "some-token",
                    "user_id": "user-id",
                    "expire_at": 1724133771.079745,
                },
            ],
        },
    }

    store = auth_store.AuthStore(hass)
    await store.async_load()

    users = await store.async_get_users()

    expect(len(users[0].refresh_tokens)).to_equal(2)
    token1, token2 = users[0].refresh_tokens.values()
    expect(bool(token1.expire_at)).to_be(False)
    expect(token2.expire_at).to_equal(1724133771.079745)


@test
async def loading_does_not_write_right_away(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Test after calling load we wait five minutes to write."""
    hass_storage[auth_store.STORAGE_KEY] = MOCK_STORAGE_DATA

    store = auth_store.AuthStore(hass)
    await store.async_load()

    # Wipe storage so we can verify if it was written.
    hass_storage[auth_store.STORAGE_KEY] = {}

    freezer.tick(auth_store.DEFAULT_SAVE_DELAY)
    await hass.async_block_till_done()
    expect(hass_storage[auth_store.STORAGE_KEY]).to_equal({})
    freezer.tick(auth_store.INITIAL_LOAD_SAVE_DELAY)
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    expect(hass_storage[auth_store.STORAGE_KEY] != {}).to_be(True)


@test
async def duplicate_uuid(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test we don't override user if we have a duplicate user ID."""
    hass_storage[auth_store.STORAGE_KEY] = MOCK_STORAGE_DATA
    store = auth_store.AuthStore(hass)
    await store.async_load()
    with patch("uuid.UUID.hex", new_callable=PropertyMock) as hex_mock:
        hex_mock.side_effect = ["user-id", "new-id"]
        user = await store.async_create_user("Test User")
    expect(len(hex_mock.mock_calls)).to_equal(2)
    expect(user.id).to_equal("new-id")


@test
async def add_remove_user_affects_tokens(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test adding and removing a user removes the tokens."""
    store = auth_store.AuthStore(hass)
    await store.async_load()
    user = await store.async_create_user("Test User")
    expect(user.name).to_equal("Test User")
    refresh_token = await store.async_create_refresh_token(
        user, "client_id", "access_token_expiration"
    )
    expect(user.refresh_tokens).to_equal({refresh_token.id: refresh_token})
    expect(await store.async_get_user(user.id)).to_equal(user)
    expect(store.async_get_refresh_token(refresh_token.id)).to_equal(refresh_token)
    expect(store.async_get_refresh_token_by_token(refresh_token.token)).to_equal(
        refresh_token
    )
    await store.async_remove_user(user)
    expect(store.async_get_refresh_token(refresh_token.id) is None).to_be(True)
    expect(store.async_get_refresh_token_by_token(refresh_token.token) is None).to_be(
        True
    )
    expect(user.refresh_tokens).to_equal({})


@test
async def set_expiry_date(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Test set expiry date of a refresh token."""
    hass_storage[auth_store.STORAGE_KEY] = {
        "version": 1,
        "data": {
            "credentials": [],
            "users": [
                {
                    "id": "user-id",
                    "is_active": True,
                    "is_owner": True,
                    "name": "Paulus",
                    "system_generated": False,
                },
            ],
            "refresh_tokens": [
                {
                    "access_token_expiration": 1800.0,
                    "client_id": "http://localhost:8123/",
                    "created_at": "2018-10-03T13:43:19.774637+00:00",
                    "id": "user-token-id",
                    "jwt_key": "some-key",
                    "token": "some-token",
                    "user_id": "user-id",
                    "expire_at": 1724133771.079745,
                },
            ],
        },
    }

    store = auth_store.AuthStore(hass)
    await store.async_load()

    users = await store.async_get_users()

    expect(len(users[0].refresh_tokens)).to_equal(1)
    (token,) = users[0].refresh_tokens.values()
    expect(token.expire_at).to_equal(1724133771.079745)

    store.async_set_expiry(token, enable_expiry=False)
    expect(token.expire_at is None).to_be(True)

    freezer.tick(auth_store.DEFAULT_SAVE_DELAY * 2)
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    expect(
        hass_storage[auth_store.STORAGE_KEY]["data"]["refresh_tokens"][0]["expire_at"]
        is None
    ).to_be(True)

    store.async_set_expiry(token, enable_expiry=True)
    expect(token.expire_at is not None).to_be(True)
