"""Tests for the Home Assistant auth module."""

from datetime import timedelta
import time
from typing import Any
from unittest.mock import patch

from freezegun import freeze_time
import jwt
import voluptuous as vol

from tryke import Depends, expect, fixture, test

from homeassistant import auth, data_entry_flow
from homeassistant.auth import (
    EVENT_USER_UPDATED,
    InvalidAuthError,
    auth_store,
    const as auth_const,
    models as auth_models,
)
from homeassistant.auth.const import GROUP_ID_ADMIN, MFA_SESSION_EXPIRATION
from homeassistant.auth.models import Credentials
from homeassistant.auth.providers import homeassistant as ha_auth_provider
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from tests.common import (
    CLIENT_ID,
    MockUser,
    async_capture_events,
    async_fire_time_changed,
    ensure_auth_manager_loaded,
    flush_store,
)
from tests.hass_fixtures import hass, hass_storage


@fixture
def mock_hass(hass: HomeAssistant = Depends(hass)) -> HomeAssistant:
    """Home Assistant mock with minimum amount of data set to make it work with auth."""
    return hass


@fixture
async def local_auth(
    hass: HomeAssistant = Depends(hass),
) -> ha_auth_provider.HassAuthProvider:
    """Load local auth provider."""
    prv = ha_auth_provider.HassAuthProvider(
        hass, hass.auth._store, {"type": "homeassistant"}
    )
    await prv.async_initialize()
    hass.auth._providers[(prv.type, prv.id)] = prv
    return prv


@fixture
async def hass_admin_credential(
    hass: HomeAssistant = Depends(hass),
    local_auth: ha_auth_provider.HassAuthProvider = Depends(local_auth),
) -> Credentials:
    """Provide credentials for admin user."""
    return Credentials(
        id="mock-credential-id",
        auth_provider_type="homeassistant",
        auth_provider_id=None,
        data={"username": "admin"},
        is_new=False,
    )


@fixture
async def hass_admin_user(
    hass: HomeAssistant = Depends(hass),
    local_auth: ha_auth_provider.HassAuthProvider = Depends(local_auth),
) -> MockUser:
    """Return a Home Assistant admin user."""
    admin_group = await hass.auth.async_get_group(GROUP_ID_ADMIN)
    return MockUser(groups=[admin_group]).add_to_hass(hass)


@test
async def auth_manager_from_config_validates_config(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test get auth providers."""
    try:
        await auth.auth_manager_from_config(
            mock_hass,
            [
                {"name": "Test Name", "type": "insecure_example", "users": []},
                {
                    "name": "Invalid configuration because no users",
                    "type": "insecure_example",
                    "id": "invalid_config",
                },
            ],
            [],
        )
    except vol.Invalid:
        pass
    else:
        raise AssertionError("expected vol.Invalid")

    manager = await auth.auth_manager_from_config(
        mock_hass,
        [
            {"name": "Test Name", "type": "insecure_example", "users": []},
            {
                "name": "Test Name 2",
                "type": "insecure_example",
                "id": "another",
                "users": [],
            },
        ],
        [],
    )

    providers = [
        {"name": provider.name, "id": provider.id, "type": provider.type}
        for provider in manager.auth_providers
    ]

    expect(providers).to_equal(
        [
            {"name": "Test Name", "type": "insecure_example", "id": None},
            {"name": "Test Name 2", "type": "insecure_example", "id": "another"},
        ]
    )


@test
async def auth_manager_from_config_auth_modules(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test get auth modules."""
    try:
        await auth.auth_manager_from_config(
            mock_hass,
            [
                {"name": "Test Name", "type": "insecure_example", "users": []},
                {
                    "name": "Test Name 2",
                    "type": "insecure_example",
                    "id": "another",
                    "users": [],
                },
            ],
            [
                {"name": "Module 1", "type": "insecure_example", "data": []},
                {
                    "name": "Invalid configuration because no data",
                    "type": "insecure_example",
                    "id": "another",
                },
            ],
        )
    except vol.Invalid:
        pass
    else:
        raise AssertionError("expected vol.Invalid")

    manager = await auth.auth_manager_from_config(
        mock_hass,
        [
            {"name": "Test Name", "type": "insecure_example", "users": []},
            {
                "name": "Test Name 2",
                "type": "insecure_example",
                "id": "another",
                "users": [],
            },
        ],
        [
            {"name": "Module 1", "type": "insecure_example", "data": []},
            {
                "name": "Module 2",
                "type": "insecure_example",
                "id": "another",
                "data": [],
            },
        ],
    )
    providers = [
        {"name": provider.name, "type": provider.type, "id": provider.id}
        for provider in manager.auth_providers
    ]
    expect(providers).to_equal(
        [
            {"name": "Test Name", "type": "insecure_example", "id": None},
            {"name": "Test Name 2", "type": "insecure_example", "id": "another"},
        ]
    )

    modules = [
        {"name": module.name, "type": module.type, "id": module.id}
        for module in manager.auth_mfa_modules
    ]
    expect(modules).to_equal(
        [
            {"name": "Module 1", "type": "insecure_example", "id": "insecure_example"},
            {"name": "Module 2", "type": "insecure_example", "id": "another"},
        ]
    )


@test
async def create_new_user(hass: HomeAssistant = Depends(hass)) -> None:
    """Test creating new user."""
    events = []

    @callback
    def user_added(event):
        events.append(event)

    hass.bus.async_listen("user_added", user_added)

    manager = await auth.auth_manager_from_config(
        hass,
        [
            {
                "type": "insecure_example",
                "users": [
                    {
                        "username": "test-user",
                        "password": "test-pass",
                        "name": "Test Name",
                    }
                ],
            }
        ],
        [],
    )

    step = await manager.login_flow.async_init(("insecure_example", None))
    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "test-user", "password": "test-pass"}
    )
    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    credential = step["result"]
    expect(credential is not None).to_be(True)

    user = await manager.async_get_or_create_user(credential)
    expect(user is not None).to_be(True)
    expect(user.is_owner).to_be(False)
    expect(user.name).to_equal("Test Name")

    await hass.async_block_till_done()
    expect(len(events)).to_equal(1)
    expect(events[0].data["user_id"]).to_equal(user.id)


@test
async def login_as_existing_user(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test login as existing user."""
    manager = await auth.auth_manager_from_config(
        mock_hass,
        [
            {
                "type": "insecure_example",
                "users": [
                    {
                        "username": "test-user",
                        "password": "test-pass",
                        "name": "Test Name",
                    }
                ],
            }
        ],
        [],
    )
    mock_hass.auth = manager
    ensure_auth_manager_loaded(manager)

    user = MockUser(
        id="mock-user2", is_owner=False, is_active=False, name="Not user"
    ).add_to_auth_manager(manager)
    user.credentials.append(
        auth_models.Credentials(
            id="mock-id2",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "other-user"},
            is_new=False,
        )
    )

    user = MockUser(
        id="mock-user", is_owner=False, is_active=False, name="Paulus"
    ).add_to_auth_manager(manager)
    user.credentials.append(
        auth_models.Credentials(
            id="mock-id",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "test-user"},
            is_new=False,
        )
    )

    step = await manager.login_flow.async_init(("insecure_example", None))
    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "test-user", "password": "test-pass"}
    )
    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)

    credential = step["result"]
    user = await manager.async_get_user_by_credentials(credential)
    expect(user is not None).to_be(True)
    expect(user.id).to_equal("mock-user")
    expect(user.is_owner).to_be(False)
    expect(user.is_active).to_be(False)
    expect(user.name).to_equal("Paulus")


@test
async def linking_user_to_two_auth_providers(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test linking user to two auth providers."""
    manager = await auth.auth_manager_from_config(
        hass,
        [
            {
                "type": "insecure_example",
                "users": [{"username": "test-user", "password": "test-pass"}],
            },
            {
                "type": "insecure_example",
                "id": "another-provider",
                "users": [{"username": "another-user", "password": "another-password"}],
            },
        ],
        [],
    )

    step = await manager.login_flow.async_init(("insecure_example", None))
    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "test-user", "password": "test-pass"}
    )
    credential = step["result"]
    user = await manager.async_get_or_create_user(credential)
    expect(user is not None).to_be(True)

    step = await manager.login_flow.async_init(
        ("insecure_example", "another-provider"), context={"credential_only": True}
    )
    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "another-user", "password": "another-password"}
    )
    new_credential = step["result"]
    await manager.async_link_user(user, new_credential)
    expect(len(user.credentials)).to_equal(2)

    await manager.async_link_user(user, new_credential)
    expect(len(user.credentials)).to_equal(2)

    user_2 = await manager.async_create_user("User 2")
    try:
        await manager.async_link_user(user_2, new_credential)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    expect(len(user_2.credentials)).to_equal(0)


@test
async def saving_loading(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test storing and saving data."""
    manager = await auth.auth_manager_from_config(
        hass,
        [
            {
                "type": "insecure_example",
                "users": [{"username": "test-user", "password": "test-pass"}],
            }
        ],
        [],
    )

    step = await manager.login_flow.async_init(("insecure_example", None))
    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "test-user", "password": "test-pass"}
    )
    credential = step["result"]
    user = await manager.async_get_or_create_user(credential)

    await manager.async_activate_user(user)
    refresh_token = await manager.async_create_refresh_token(
        user, CLIENT_ID, credential=credential
    )
    manager.async_create_access_token(refresh_token, "192.168.0.1")
    await manager.async_create_refresh_token(
        user, "dummy-client", credential=credential
    )

    await flush_store(manager._store._store)

    store2 = auth_store.AuthStore(hass)
    await store2.async_load()
    users = await store2.async_get_users()
    expect(len(users)).to_equal(1)
    expect(users[0].permissions).to_equal(user.permissions)
    expect(users[0]).to_equal(user)
    expect(len(users[0].refresh_tokens)).to_equal(2)
    for r_token in users[0].refresh_tokens.values():
        if r_token.client_id == CLIENT_ID:
            expect(r_token.last_used_at is not None).to_be(True)
            expect(r_token.last_used_ip).to_equal("192.168.0.1")
        elif r_token.client_id == "dummy-client":
            expect(r_token.last_used_at is None).to_be(True)
            expect(r_token.last_used_ip is None).to_be(True)
        else:
            raise AssertionError(f"Unknown client_id: {r_token.client_id}")


@test
async def cannot_retrieve_expired_access_token(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that we cannot retrieve expired access tokens."""
    manager = await auth.auth_manager_from_config(hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    refresh_token = await manager.async_create_refresh_token(user, CLIENT_ID)
    expect(refresh_token.user.id is user.id).to_be(True)
    expect(refresh_token.client_id).to_equal(CLIENT_ID)

    access_token = manager.async_create_access_token(refresh_token)
    expect(manager.async_validate_access_token(access_token) is refresh_token).to_be(
        True
    )

    with patch(
        "homeassistant.auth.time.time",
        return_value=time.time()
        - auth_const.ACCESS_TOKEN_EXPIRATION.total_seconds()
        - 11,
    ):
        access_token = manager.async_create_access_token(refresh_token)

    expect(manager.async_validate_access_token(access_token) is None).to_be(True)


@test
async def generating_system_user(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we can add a system user."""
    events = []

    @callback
    def user_added(event):
        events.append(event)

    hass.bus.async_listen("user_added", user_added)

    manager = await auth.auth_manager_from_config(hass, [], [])
    user = await manager.async_create_system_user("Hass.io")
    token = await manager.async_create_refresh_token(user)
    expect(user.system_generated).to_be(True)
    expect(user.groups).to_equal([])
    expect(user.local_only).to_be(False)
    expect(token is not None).to_be(True)
    expect(token.client_id is None).to_be(True)
    expect(token.token_type).to_equal(auth.models.TOKEN_TYPE_SYSTEM)
    expect(token.expire_at is None).to_be(True)

    await hass.async_block_till_done()
    expect(len(events)).to_equal(1)
    expect(events[0].data["user_id"]).to_equal(user.id)

    user = await manager.async_create_system_user(
        "Hass.io", group_ids=[GROUP_ID_ADMIN], local_only=True
    )
    token = await manager.async_create_refresh_token(user)
    expect(user.system_generated).to_be(True)
    expect(user.is_admin).to_be(True)
    expect(user.local_only).to_be(True)
    expect(token is not None).to_be(True)
    expect(token.client_id is None).to_be(True)
    expect(token.token_type).to_equal(auth.models.TOKEN_TYPE_SYSTEM)
    expect(token.expire_at is None).to_be(True)

    await hass.async_block_till_done()
    expect(len(events)).to_equal(2)
    expect(events[1].data["user_id"]).to_equal(user.id)


@test
async def refresh_token_requires_client_for_user(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test create refresh token for a user with client_id."""
    manager = await auth.auth_manager_from_config(hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    expect(user.system_generated).to_be(False)

    try:
        await manager.async_create_refresh_token(user)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")

    token = await manager.async_create_refresh_token(user, CLIENT_ID)
    expect(token is not None).to_be(True)
    expect(token.client_id).to_equal(CLIENT_ID)
    expect(token.token_type).to_equal(auth_models.TOKEN_TYPE_NORMAL)
    expect(token.access_token_expiration).to_equal(auth_const.ACCESS_TOKEN_EXPIRATION)


@test
async def refresh_token_not_requires_client_for_system_user(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test create refresh token for a system user w/o client_id."""
    manager = await auth.auth_manager_from_config(hass, [], [])
    user = await manager.async_create_system_user("Hass.io")
    expect(user.system_generated).to_be(True)

    try:
        await manager.async_create_refresh_token(user, CLIENT_ID)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")

    token = await manager.async_create_refresh_token(user)
    expect(token is not None).to_be(True)
    expect(token.client_id is None).to_be(True)
    expect(token.token_type).to_equal(auth_models.TOKEN_TYPE_SYSTEM)


@test
async def refresh_token_with_specific_access_token_expiration(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test create a refresh token with specific access token expiration."""
    manager = await auth.auth_manager_from_config(hass, [], [])
    user = MockUser().add_to_auth_manager(manager)

    token = await manager.async_create_refresh_token(
        user, CLIENT_ID, access_token_expiration=timedelta(days=100)
    )
    expect(token is not None).to_be(True)
    expect(token.client_id).to_equal(CLIENT_ID)
    expect(token.access_token_expiration).to_equal(timedelta(days=100))
    expect(token.token_type).to_equal(auth.models.TOKEN_TYPE_NORMAL)
    expect(token.expire_at is not None).to_be(True)


@test
async def refresh_token_type(hass: HomeAssistant = Depends(hass)) -> None:
    """Test create a refresh token with token type."""
    manager = await auth.auth_manager_from_config(hass, [], [])
    user = MockUser().add_to_auth_manager(manager)

    try:
        await manager.async_create_refresh_token(
            user, CLIENT_ID, token_type=auth_models.TOKEN_TYPE_SYSTEM
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")

    token = await manager.async_create_refresh_token(
        user, CLIENT_ID, token_type=auth_models.TOKEN_TYPE_NORMAL
    )
    expect(token is not None).to_be(True)
    expect(token.client_id).to_equal(CLIENT_ID)
    expect(token.token_type).to_equal(auth_models.TOKEN_TYPE_NORMAL)


@test
async def refresh_token_type_long_lived_access_token(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test create a refresh token has long-lived access token type."""
    manager = await auth.auth_manager_from_config(hass, [], [])
    user = MockUser().add_to_auth_manager(manager)

    try:
        await manager.async_create_refresh_token(
            user, token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")

    token = await manager.async_create_refresh_token(
        user,
        client_name="GPS LOGGER",
        client_icon="mdi:home",
        token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
    )
    expect(token is not None).to_be(True)
    expect(token.client_id is None).to_be(True)
    expect(token.client_name).to_equal("GPS LOGGER")
    expect(token.client_icon).to_equal("mdi:home")
    expect(token.token_type).to_equal(auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN)
    expect(token.expire_at is None).to_be(True)


@test
async def refresh_token_provider_validation(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test that creating access token from refresh token checks with provider."""
    manager = await auth.auth_manager_from_config(
        mock_hass,
        [
            {
                "type": "insecure_example",
                "users": [{"username": "test-user", "password": "test-pass"}],
            }
        ],
        [],
    )

    credential = auth_models.Credentials(
        id="mock-credential-id",
        auth_provider_type="insecure_example",
        auth_provider_id=None,
        data={"username": "test-user"},
        is_new=False,
    )

    user = MockUser().add_to_auth_manager(manager)
    user.credentials.append(credential)
    refresh_token = await manager.async_create_refresh_token(
        user, CLIENT_ID, credential=credential
    )
    ip = "127.0.0.1"

    expect(manager.async_create_access_token(refresh_token, ip) is not None).to_be(
        True
    )

    with patch(
        "homeassistant.auth.providers.insecure_example.ExampleAuthProvider.async_validate_refresh_token",
        side_effect=InvalidAuthError("Invalid access"),
    ) as call:
        expect(
            lambda: manager.async_create_access_token(refresh_token, ip)
        ).to_raise(InvalidAuthError)

    call.assert_called_with(refresh_token, ip)


@test
async def cannot_deactive_owner(mock_hass: HomeAssistant = Depends(mock_hass)) -> None:
    """Test that we cannot deactivate the owner."""
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    owner = MockUser(is_owner=True).add_to_auth_manager(manager)

    try:
        await manager.async_deactivate_user(owner)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


@test
async def deactivate_user_removes_refresh_tokens(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that deactivating a user removes their refresh tokens."""
    manager = await auth.auth_manager_from_config(hass, [], [])
    user = MockUser().add_to_auth_manager(manager)

    refresh_token1 = await manager.async_create_refresh_token(user, CLIENT_ID)
    refresh_token2 = await manager.async_create_refresh_token(user, "other-client")
    expect(len(user.refresh_tokens)).to_equal(2)
    expect(manager.async_get_refresh_token(refresh_token1.id)).to_equal(refresh_token1)
    expect(manager.async_get_refresh_token(refresh_token2.id)).to_equal(refresh_token2)

    await manager.async_deactivate_user(user)

    expect(user.is_active).to_be(False)
    expect(len(user.refresh_tokens)).to_equal(0)
    expect(manager.async_get_refresh_token(refresh_token1.id) is None).to_be(True)
    expect(manager.async_get_refresh_token(refresh_token2.id) is None).to_be(True)


@test
async def remove_refresh_token(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we can remove a refresh token."""
    manager = await auth.auth_manager_from_config(hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    refresh_token = await manager.async_create_refresh_token(user, CLIENT_ID)
    access_token = manager.async_create_access_token(refresh_token)

    manager.async_remove_refresh_token(refresh_token)

    expect(manager.async_get_refresh_token(refresh_token.id) is None).to_be(True)
    expect(manager.async_validate_access_token(access_token) is None).to_be(True)


@test
async def remove_expired_refresh_token(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that expired refresh tokens are deleted."""
    manager = await auth.auth_manager_from_config(hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    now = dt_util.utcnow()
    with freeze_time(now):
        refresh_token1 = await manager.async_create_refresh_token(user, CLIENT_ID)
        expect(refresh_token1.expire_at).to_equal(
            now.timestamp() + timedelta(days=90).total_seconds()
        )

    with freeze_time(now + timedelta(days=30)):
        async_fire_time_changed(hass, now + timedelta(days=30))
        refresh_token2 = await manager.async_create_refresh_token(user, CLIENT_ID)
        expect(refresh_token2.expire_at).to_equal(
            now.timestamp() + timedelta(days=120).total_seconds()
        )

    with freeze_time(now + timedelta(days=89, hours=23)):
        async_fire_time_changed(hass, now + timedelta(days=89, hours=23))
        await hass.async_block_till_done()
        expect(manager.async_get_refresh_token(refresh_token1.id) is not None).to_be(
            True
        )
        expect(manager.async_get_refresh_token(refresh_token2.id) is not None).to_be(
            True
        )

    with freeze_time(now + timedelta(days=90, seconds=5)):
        async_fire_time_changed(hass, now + timedelta(days=90, seconds=5))
        await hass.async_block_till_done()
        expect(manager.async_get_refresh_token(refresh_token1.id) is None).to_be(True)
        expect(manager.async_get_refresh_token(refresh_token2.id) is not None).to_be(
            True
        )

    with freeze_time(now + timedelta(days=120, seconds=5)):
        async_fire_time_changed(hass, now + timedelta(days=120, seconds=5))
        await hass.async_block_till_done()
        expect(manager.async_get_refresh_token(refresh_token1.id) is None).to_be(True)
        expect(manager.async_get_refresh_token(refresh_token2.id) is None).to_be(True)


@test
async def update_expire_at_refresh_token(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that expire at is updated when refresh token is used."""
    manager = await auth.auth_manager_from_config(hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    now = dt_util.utcnow()
    with freeze_time(now):
        refresh_token = await manager.async_create_refresh_token(user, CLIENT_ID)
        expect(refresh_token.expire_at).to_equal(
            now.timestamp() + timedelta(days=90).total_seconds()
        )

    with freeze_time(now + timedelta(days=30)):
        async_fire_time_changed(hass, now + timedelta(days=30))
        await hass.async_block_till_done()
        expect(manager.async_create_access_token(refresh_token) is not None).to_be(
            True
        )
        await hass.async_block_till_done()
        expect(refresh_token.expire_at).to_equal(
            now.timestamp()
            + timedelta(days=30).total_seconds()
            + timedelta(days=90).total_seconds()
        )


@test
async def register_revoke_token_callback(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test that a registered revoke token callback is called."""
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    refresh_token = await manager.async_create_refresh_token(user, CLIENT_ID)

    called = False

    def cb():
        nonlocal called
        called = True

    manager.async_register_revoke_token_callback(refresh_token.id, cb)
    manager.async_remove_refresh_token(refresh_token)
    expect(called).to_be(True)


@test
async def unregister_revoke_token_callback(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test that a revoke token callback can be unregistered."""
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    refresh_token = await manager.async_create_refresh_token(user, CLIENT_ID)

    called = False

    def cb():
        nonlocal called
        called = True

    unregister = manager.async_register_revoke_token_callback(refresh_token.id, cb)
    unregister()

    manager.async_remove_refresh_token(refresh_token)
    expect(called).to_be(False)


@test
async def create_access_token(mock_hass: HomeAssistant = Depends(mock_hass)) -> None:
    """Test normal refresh_token's jwt_key keep same after used."""
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    refresh_token = await manager.async_create_refresh_token(user, CLIENT_ID)
    expect(refresh_token.token_type).to_equal(auth_models.TOKEN_TYPE_NORMAL)
    jwt_key = refresh_token.jwt_key
    access_token = manager.async_create_access_token(refresh_token)
    expect(access_token is not None).to_be(True)
    expect(refresh_token.jwt_key).to_equal(jwt_key)
    jwt_payload = jwt.decode(access_token, jwt_key, algorithms=["HS256"])
    expect(jwt_payload["iss"]).to_equal(refresh_token.id)
    expect(jwt_payload["exp"] - jwt_payload["iat"]).to_equal(
        timedelta(minutes=30).total_seconds()
    )


@test
async def create_long_lived_access_token(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test refresh_token's jwt_key changed for long-lived access token."""
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    refresh_token = await manager.async_create_refresh_token(
        user,
        client_name="GPS Logger",
        token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
        access_token_expiration=timedelta(days=300),
    )
    expect(refresh_token.token_type).to_equal(
        auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
    )
    access_token = manager.async_create_access_token(refresh_token)
    jwt_payload = jwt.decode(access_token, refresh_token.jwt_key, algorithms=["HS256"])
    expect(jwt_payload["iss"]).to_equal(refresh_token.id)
    expect(jwt_payload["exp"] - jwt_payload["iat"]).to_equal(
        timedelta(days=300).total_seconds()
    )


@test
async def one_long_lived_access_token_per_refresh_token(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test one refresh_token can only have one long-lived access token."""
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    refresh_token = await manager.async_create_refresh_token(
        user,
        client_name="GPS Logger",
        token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
        access_token_expiration=timedelta(days=3000),
    )
    expect(refresh_token.token_type).to_equal(
        auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
    )
    access_token = manager.async_create_access_token(refresh_token)
    jwt_key = refresh_token.jwt_key

    rt = manager.async_validate_access_token(access_token)
    expect(rt.id).to_equal(refresh_token.id)

    try:
        await manager.async_create_refresh_token(
            user,
            client_name="GPS Logger",
            token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
            access_token_expiration=timedelta(days=3000),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")

    manager.async_remove_refresh_token(refresh_token)
    expect(refresh_token.id not in user.refresh_tokens).to_be(True)
    rt = manager.async_validate_access_token(access_token)
    expect(rt is None).to_be(True)

    refresh_token_2 = await manager.async_create_refresh_token(
        user,
        client_name="GPS Logger",
        token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
        access_token_expiration=timedelta(days=3000),
    )
    expect(refresh_token_2.id != refresh_token.id).to_be(True)
    expect(refresh_token_2.token_type).to_equal(
        auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
    )
    access_token_2 = manager.async_create_access_token(refresh_token_2)
    jwt_key_2 = refresh_token_2.jwt_key

    expect(access_token != access_token_2).to_be(True)
    expect(jwt_key != jwt_key_2).to_be(True)

    rt = manager.async_validate_access_token(access_token_2)
    jwt_payload = jwt.decode(access_token_2, rt.jwt_key, algorithms=["HS256"])
    expect(jwt_payload["iss"]).to_equal(refresh_token_2.id)
    expect(jwt_payload["exp"] - jwt_payload["iat"]).to_equal(
        timedelta(days=3000).total_seconds()
    )


@test
async def login_with_auth_module(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test login as existing user with auth module."""
    manager = await auth.auth_manager_from_config(
        mock_hass,
        [
            {
                "type": "insecure_example",
                "users": [
                    {
                        "username": "test-user",
                        "password": "test-pass",
                        "name": "Test Name",
                    }
                ],
            }
        ],
        [
            {
                "type": "insecure_example",
                "data": [{"user_id": "mock-user", "pin": "test-pin"}],
            }
        ],
    )
    mock_hass.auth = manager
    ensure_auth_manager_loaded(manager)

    user = MockUser(
        id="mock-user", is_owner=False, is_active=False, name="Paulus"
    ).add_to_auth_manager(manager)
    user.credentials.append(
        auth_models.Credentials(
            id="mock-id",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "test-user"},
            is_new=False,
        )
    )

    step = await manager.login_flow.async_init(("insecure_example", None))
    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "test-user", "password": "test-pass"}
    )

    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(step["step_id"]).to_equal("mfa")

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"pin": "invalid-pin"}
    )

    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(step["step_id"]).to_equal("mfa")
    expect(step["errors"]).to_equal({"base": "invalid_code"})

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"pin": "test-pin"}
    )

    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(step["result"] is not None).to_be(True)
    expect(step["result"].id).to_equal("mock-id")


@test
async def login_with_multi_auth_module(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test login as existing user with multiple auth modules."""
    manager = await auth.auth_manager_from_config(
        mock_hass,
        [
            {
                "type": "insecure_example",
                "users": [
                    {
                        "username": "test-user",
                        "password": "test-pass",
                        "name": "Test Name",
                    }
                ],
            }
        ],
        [
            {
                "type": "insecure_example",
                "data": [{"user_id": "mock-user", "pin": "test-pin"}],
            },
            {
                "type": "insecure_example",
                "id": "module2",
                "data": [{"user_id": "mock-user", "pin": "test-pin2"}],
            },
        ],
    )
    mock_hass.auth = manager
    ensure_auth_manager_loaded(manager)

    user = MockUser(
        id="mock-user", is_owner=False, is_active=False, name="Paulus"
    ).add_to_auth_manager(manager)
    user.credentials.append(
        auth_models.Credentials(
            id="mock-id",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "test-user"},
            is_new=False,
        )
    )

    step = await manager.login_flow.async_init(("insecure_example", None))
    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "test-user", "password": "test-pass"}
    )

    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(step["step_id"]).to_equal("select_mfa_module")

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"multi_factor_auth_module": "module2"}
    )

    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(step["step_id"]).to_equal("mfa")

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"pin": "test-pin2"}
    )

    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(step["result"] is not None).to_be(True)
    expect(step["result"].id).to_equal("mock-id")


@test
async def auth_module_expired_session(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test login as existing user."""
    manager = await auth.auth_manager_from_config(
        mock_hass,
        [
            {
                "type": "insecure_example",
                "users": [
                    {
                        "username": "test-user",
                        "password": "test-pass",
                        "name": "Test Name",
                    }
                ],
            }
        ],
        [
            {
                "type": "insecure_example",
                "data": [{"user_id": "mock-user", "pin": "test-pin"}],
            }
        ],
    )
    mock_hass.auth = manager
    ensure_auth_manager_loaded(manager)

    user = MockUser(
        id="mock-user", is_owner=False, is_active=False, name="Paulus"
    ).add_to_auth_manager(manager)
    user.credentials.append(
        auth_models.Credentials(
            id="mock-id",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "test-user"},
            is_new=False,
        )
    )

    step = await manager.login_flow.async_init(("insecure_example", None))
    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "test-user", "password": "test-pass"}
    )

    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(step["step_id"]).to_equal("mfa")

    with freeze_time(dt_util.utcnow() + MFA_SESSION_EXPIRATION):
        step = await manager.login_flow.async_configure(
            step["flow_id"], {"pin": "test-pin"}
        )
        expect(step["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
        expect(step["reason"]).to_equal("login_expired")


@test
async def enable_mfa_for_user(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test enable mfa module for user."""
    manager = await auth.auth_manager_from_config(
        hass,
        [
            {
                "type": "insecure_example",
                "users": [{"username": "test-user", "password": "test-pass"}],
            }
        ],
        [{"type": "insecure_example", "data": []}],
    )

    step = await manager.login_flow.async_init(("insecure_example", None))
    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "test-user", "password": "test-pass"}
    )
    credential = step["result"]
    user = await manager.async_get_or_create_user(credential)
    expect(user is not None).to_be(True)

    modules = await manager.async_get_enabled_mfa(user)
    expect(len(modules)).to_equal(0)

    module = manager.get_auth_mfa_module("insecure_example")
    expect(bool(module._data)).to_be(False)

    await manager.async_enable_user_mfa(user, "insecure_example", {"pin": "test-pin"})
    expect(len(module._data)).to_equal(1)
    expect(module._data[0]).to_equal({"user_id": user.id, "pin": "test-pin"})

    modules = await manager.async_get_enabled_mfa(user)
    expect(len(modules)).to_equal(1)
    expect("insecure_example" in modules).to_be(True)

    await manager.async_enable_user_mfa(
        user, "insecure_example", {"pin": "test-pin-new"}
    )
    expect(len(module._data)).to_equal(1)
    expect(module._data[0]).to_equal({"user_id": user.id, "pin": "test-pin-new"})
    modules = await manager.async_get_enabled_mfa(user)
    expect(len(modules)).to_equal(1)
    expect("insecure_example" in modules).to_be(True)

    system_user = await manager.async_create_system_user("system-user")
    try:
        await manager.async_enable_user_mfa(
            system_user, "insecure_example", {"pin": "test-pin"}
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    expect(len(module._data)).to_equal(1)
    modules = await manager.async_get_enabled_mfa(system_user)
    expect(len(modules)).to_equal(0)

    await manager.async_disable_user_mfa(user, "insecure_example")
    expect(bool(module._data)).to_be(False)

    modules = await manager.async_get_enabled_mfa(user)
    expect(len(modules)).to_equal(0)

    await manager.async_disable_user_mfa(user, "insecure_example")


@test
async def async_remove_user(hass: HomeAssistant = Depends(hass)) -> None:
    """Test removing a user."""
    events = async_capture_events(hass, "user_removed")
    manager = await auth.auth_manager_from_config(
        hass,
        [
            {
                "type": "insecure_example",
                "users": [
                    {
                        "username": "test-user",
                        "password": "test-pass",
                        "name": "Test Name",
                    }
                ],
            }
        ],
        [],
    )
    hass.auth = manager
    ensure_auth_manager_loaded(manager)

    user = MockUser(
        id="mock-user", is_owner=False, is_active=False, name="Paulus"
    ).add_to_auth_manager(manager)
    user.credentials.append(
        auth_models.Credentials(
            id="mock-id",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "test-user"},
            is_new=False,
        )
    )
    expect(len(user.credentials)).to_equal(1)

    await hass.auth.async_remove_user(user)

    expect(len(await manager.async_get_users())).to_equal(0)
    expect(len(user.credentials)).to_equal(0)

    await hass.async_block_till_done()
    expect(len(events)).to_equal(1)
    expect(events[0].data["user_id"]).to_equal(user.id)


@test
async def async_remove_user_fail_if_remove_credential_fails(
    hass: HomeAssistant = Depends(hass),
    hass_admin_user: MockUser = Depends(hass_admin_user),
    hass_admin_credential: Credentials = Depends(hass_admin_credential),
) -> None:
    """Test removing a user."""
    await hass.auth.async_link_user(hass_admin_user, hass_admin_credential)

    async def _call() -> None:
        await hass.auth.async_remove_user(hass_admin_user)

    with patch.object(hass.auth, "async_remove_credentials", side_effect=ValueError):
        try:
            await _call()
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


@test
async def new_users(mock_hass: HomeAssistant = Depends(mock_hass)) -> None:
    """Test newly created users."""
    manager = await auth.auth_manager_from_config(
        mock_hass,
        [
            {
                "type": "insecure_example",
                "users": [
                    {
                        "username": "test-user",
                        "password": "test-pass",
                        "name": "Test Name",
                    },
                    {
                        "username": "test-user-2",
                        "password": "test-pass",
                        "name": "Test Name",
                    },
                    {
                        "username": "test-user-3",
                        "password": "test-pass",
                        "name": "Test Name",
                    },
                ],
            }
        ],
        [],
    )
    ensure_auth_manager_loaded(manager)

    user = await manager.async_create_user("Hello")
    expect(user.is_owner).to_be(True)
    expect(user.is_admin).to_be(True)
    expect(user.local_only).to_be(False)
    expect(user.groups).to_equal([])

    user = await manager.async_create_user("Hello 2")
    expect(user.is_admin).to_be(False)
    expect(user.groups).to_equal([])

    user = await manager.async_create_user(
        "Hello 3", group_ids=["system-admin"], local_only=True
    )
    expect(user.is_admin).to_be(True)
    expect(user.groups[0].id).to_equal("system-admin")
    expect(user.local_only).to_be(True)

    user_cred = await manager.async_get_or_create_user(
        auth_models.Credentials(
            id="mock-id",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "test-user"},
            is_new=True,
        )
    )
    expect(user_cred.is_admin).to_be(True)


@test
async def rename_does_not_change_refresh_token(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test that we can rename without changing refresh token."""
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    await manager.async_create_refresh_token(user, CLIENT_ID)

    expect(len(list(user.refresh_tokens.values()))).to_equal(1)
    token_before = list(user.refresh_tokens.values())[0]

    await manager.async_update_user(user, name="new name")
    expect(user.name).to_equal("new name")

    expect(len(list(user.refresh_tokens.values()))).to_equal(1)
    token_after = list(user.refresh_tokens.values())[0]

    expect(token_before).to_equal(token_after)


@test
async def event_user_updated_fires(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the user updated event fires."""
    manager = await auth.auth_manager_from_config(hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    await manager.async_create_refresh_token(user, CLIENT_ID)

    expect(len(list(user.refresh_tokens.values()))).to_equal(1)

    events = async_capture_events(hass, EVENT_USER_UPDATED)

    await manager.async_update_user(user, name="new name")
    expect(user.name).to_equal("new name")

    await hass.async_block_till_done()
    expect(len(events)).to_equal(1)


@test
async def access_token_with_invalid_signature(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test rejecting access tokens with an invalid signature."""
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    refresh_token = await manager.async_create_refresh_token(
        user,
        client_name="Good Client",
        token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
        access_token_expiration=timedelta(days=3000),
    )
    expect(refresh_token.token_type).to_equal(
        auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
    )
    access_token = manager.async_create_access_token(refresh_token)

    rt = manager.async_validate_access_token(access_token)
    expect(rt.id).to_equal(refresh_token.id)

    header, payload, signature = access_token.split(".")
    invalid_signature = "a" * len(signature)
    invalid_token = f"{header}.{payload}.{invalid_signature}"

    expect(access_token != invalid_token).to_be(True)

    result = manager.async_validate_access_token(invalid_token)
    expect(result is None).to_be(True)


@test
async def access_token_with_null_signature(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test rejecting access tokens with a null signature."""
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    refresh_token = await manager.async_create_refresh_token(
        user,
        client_name="Good Client",
        token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
        access_token_expiration=timedelta(days=3000),
    )
    expect(refresh_token.token_type).to_equal(
        auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
    )
    access_token = manager.async_create_access_token(refresh_token)

    rt = manager.async_validate_access_token(access_token)
    expect(rt.id).to_equal(refresh_token.id)

    header, payload, signature = access_token.split(".")
    invalid_signature = "\0" * len(signature)
    invalid_token = f"{header}.{payload}.{invalid_signature}"

    expect(access_token != invalid_token).to_be(True)

    result = manager.async_validate_access_token(invalid_token)
    expect(result is None).to_be(True)


@test
async def access_token_with_empty_signature(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test rejecting access tokens with an empty signature."""
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    refresh_token = await manager.async_create_refresh_token(
        user,
        client_name="Good Client",
        token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
        access_token_expiration=timedelta(days=3000),
    )
    expect(refresh_token.token_type).to_equal(
        auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
    )
    access_token = manager.async_create_access_token(refresh_token)

    rt = manager.async_validate_access_token(access_token)
    expect(rt.id).to_equal(refresh_token.id)

    header, payload, _ = access_token.split(".")
    invalid_token = f"{header}.{payload}."

    expect(access_token != invalid_token).to_be(True)

    result = manager.async_validate_access_token(invalid_token)
    expect(result is None).to_be(True)


@test
async def access_token_with_empty_key(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test rejecting access tokens with an empty key."""
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    refresh_token = await manager.async_create_refresh_token(
        user,
        client_name="Good Client",
        token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
        access_token_expiration=timedelta(days=3000),
    )
    expect(refresh_token.token_type).to_equal(
        auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
    )

    access_token = manager.async_create_access_token(refresh_token)

    manager.async_remove_refresh_token(refresh_token)

    expect(manager.async_validate_access_token(access_token) is None).to_be(True)


@test
async def reject_access_token_with_impossible_large_size(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test rejecting access tokens with impossible sizes."""
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    expect(manager.async_validate_access_token("a" * 10000) is None).to_be(True)


@test
async def reject_token_with_invalid_json_payload(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test rejecting access tokens with invalid json payload."""
    jws = jwt.PyJWS()
    token_with_invalid_json = jws.encode(
        b"invalid", b"invalid", "HS256", {"alg": "HS256", "typ": "JWT"}
    )
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    expect(manager.async_validate_access_token(token_with_invalid_json) is None).to_be(
        True
    )


@test
async def reject_token_with_not_dict_json_payload(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test rejecting access tokens with not a dict json payload."""
    jws = jwt.PyJWS()
    token_not_a_dict_json = jws.encode(
        b'["invalid"]', b"invalid", "HS256", {"alg": "HS256", "typ": "JWT"}
    )
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    expect(manager.async_validate_access_token(token_not_a_dict_json) is None).to_be(
        True
    )


@test
async def access_token_that_expires_soon(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test access token from refresh token that expires very soon."""
    now = dt_util.utcnow()
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    refresh_token = await manager.async_create_refresh_token(
        user,
        client_name="Token that expires very soon",
        token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
        access_token_expiration=timedelta(seconds=1),
    )
    expect(refresh_token.token_type).to_equal(
        auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
    )
    access_token = manager.async_create_access_token(refresh_token)

    rt = manager.async_validate_access_token(access_token)
    expect(rt.id).to_equal(refresh_token.id)

    with freeze_time(now + timedelta(minutes=1)):
        expect(manager.async_validate_access_token(access_token) is None).to_be(True)


@test
async def access_token_from_the_future(
    mock_hass: HomeAssistant = Depends(mock_hass),
) -> None:
    """Test we reject an access token from the future."""
    now = dt_util.utcnow()
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    with freeze_time(now + timedelta(days=365)):
        refresh_token = await manager.async_create_refresh_token(
            user,
            client_name="Token that expires very soon",
            token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
            access_token_expiration=timedelta(days=10),
        )
        expect(refresh_token.token_type).to_equal(
            auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
        )
        access_token = manager.async_create_access_token(refresh_token)

    expect(manager.async_validate_access_token(access_token) is None).to_be(True)

    with freeze_time(now + timedelta(days=365)):
        rt = manager.async_validate_access_token(access_token)
        expect(rt.id).to_equal(refresh_token.id)
