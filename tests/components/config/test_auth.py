"""Test config entries API."""

from tryke import Depends, expect, fixture, test

from homeassistant.auth import models as auth_models
from homeassistant.core import HomeAssistant

from ._fixtures import (
    hass_read_only_access_token as hass_read_only_access_token_fx,
    setup_config as setup_config_fx,
)

from tests.common import CLIENT_ID, MockGroup, MockUser
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_access_token as hass_access_token_fx,
    hass_admin_user as hass_admin_user_fx,
    hass_ws_client as hass_ws_client_fx,
)
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def list_requires_admin(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_read_only_access_token: str = Depends(hass_read_only_access_token_fx),
) -> None:
    """Test get users requires auth."""
    client = await hass_ws_client(hass, hass_read_only_access_token)

    await client.send_json({"id": 5, "type": "config/auth/list"})

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("unauthorized")


@test
async def list_test(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test get users."""
    group = MockGroup().add_to_hass(hass)

    owner = MockUser(
        id="abc", name="Test Owner", is_owner=True, groups=[group]
    ).add_to_hass(hass)

    owner.credentials.append(
        auth_models.Credentials(
            auth_provider_type="homeassistant",
            auth_provider_id=None,
            data={"username": "test-owner"},
        )
    )

    system = MockUser(id="efg", name="Test Hass.io", system_generated=True).add_to_hass(
        hass
    )

    inactive = MockUser(
        id="hij", name="Inactive User", is_active=False, groups=[group]
    ).add_to_hass(hass)

    refresh_token = await hass.auth.async_create_refresh_token(
        owner, CLIENT_ID, credential=owner.credentials[0]
    )
    access_token = hass.auth.async_create_access_token(refresh_token)

    client = await hass_ws_client(hass, access_token)
    await client.send_json({"id": 5, "type": "config/auth/list"})

    result = await client.receive_json()
    expect(result["success"]).to_be(True)
    data = result["result"]
    expect(data).to_have_length(5)
    expect(data[0]).to_equal(
        {
            "id": hass_admin_user.id,
            "username": "admin",
            "name": "Mock User",
            "is_owner": False,
            "is_active": True,
            "local_only": False,
            "system_generated": False,
            "group_ids": [group.id for group in hass_admin_user.groups],
            "credentials": [{"type": "homeassistant"}],
        }
    )
    expect(data[1]).to_equal(
        {
            "id": owner.id,
            "username": "test-owner",
            "name": "Test Owner",
            "is_owner": True,
            "is_active": True,
            "local_only": False,
            "system_generated": False,
            "group_ids": [group.id for group in owner.groups],
            "credentials": [{"type": "homeassistant"}],
        }
    )
    expect(data[2]).to_equal(
        {
            "id": system.id,
            "username": None,
            "name": "Test Hass.io",
            "is_owner": False,
            "is_active": True,
            "local_only": False,
            "system_generated": True,
            "group_ids": [],
            "credentials": [],
        }
    )
    expect(data[3]).to_equal(
        {
            "id": inactive.id,
            "username": None,
            "name": "Inactive User",
            "is_owner": False,
            "is_active": False,
            "local_only": False,
            "system_generated": False,
            "group_ids": [group.id for group in inactive.groups],
            "credentials": [],
        }
    )


@test
async def delete_requires_admin(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_read_only_access_token: str = Depends(hass_read_only_access_token_fx),
) -> None:
    """Test delete command requires an admin."""
    client = await hass_ws_client(hass, hass_read_only_access_token)

    await client.send_json({"id": 5, "type": "config/auth/delete", "user_id": "abcd"})

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("unauthorized")


@test
async def delete_unable_self_account(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test we cannot delete our own account."""
    client = await hass_ws_client(hass, hass_access_token)
    refresh_token = hass.auth.async_validate_access_token(hass_access_token)

    await client.send_json(
        {"id": 5, "type": "config/auth/delete", "user_id": refresh_token.user.id}
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("no_delete_self")


@test
async def delete_unknown_user(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test we cannot delete an unknown user."""
    client = await hass_ws_client(hass, hass_access_token)

    await client.send_json({"id": 5, "type": "config/auth/delete", "user_id": "abcd"})

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("not_found")


@test
async def delete_test(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test delete command works."""
    client = await hass_ws_client(hass, hass_access_token)
    test_user = MockUser(id="efg").add_to_hass(hass)

    cur_users = len(await hass.auth.async_get_users())

    await client.send_json(
        {"id": 5, "type": "config/auth/delete", "user_id": test_user.id}
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(True)
    expect(len(await hass.auth.async_get_users())).to_equal(cur_users - 1)


@test
async def create_test(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test create command works."""
    client = await hass_ws_client(hass, hass_access_token)

    cur_users = len(await hass.auth.async_get_users())

    await client.send_json({"id": 5, "type": "config/auth/create", "name": "Paulus"})

    result = await client.receive_json()
    expect(result["success"]).to_be(True)
    expect(len(await hass.auth.async_get_users())).to_equal(cur_users + 1)
    data_user = result["result"]["user"]
    user = await hass.auth.async_get_user(data_user["id"])
    expect(user is not None).to_be(True)
    expect(user.name).to_equal(data_user["name"])
    expect(user.is_active).to_be(True)
    expect(user.groups).to_equal([])
    expect(user.is_admin).to_be(False)
    expect(user.is_owner).to_be(False)
    expect(user.system_generated).to_be(False)


@test
async def create_user_group(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test create user with a group."""
    client = await hass_ws_client(hass, hass_access_token)

    cur_users = len(await hass.auth.async_get_users())

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth/create",
            "name": "Paulus",
            "group_ids": ["system-admin"],
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(True)
    expect(len(await hass.auth.async_get_users())).to_equal(cur_users + 1)
    data_user = result["result"]["user"]
    user = await hass.auth.async_get_user(data_user["id"])
    expect(user is not None).to_be(True)
    expect(user.name).to_equal(data_user["name"])
    expect(user.is_active).to_be(True)
    expect(user.groups[0].id).to_equal("system-admin")
    expect(user.is_admin).to_be(True)
    expect(user.is_owner).to_be(False)
    expect(user.system_generated).to_be(False)


@test
async def create_requires_admin(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_read_only_access_token: str = Depends(hass_read_only_access_token_fx),
) -> None:
    """Test create command requires an admin."""
    client = await hass_ws_client(hass, hass_read_only_access_token)

    await client.send_json({"id": 5, "type": "config/auth/create", "name": "YO"})

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("unauthorized")


@test
async def update_test(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test update command works."""
    client = await hass_ws_client(hass)

    user = await hass.auth.async_create_user("Test user")

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth/update",
            "user_id": user.id,
            "name": "Updated name",
            "group_ids": ["system-read-only"],
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(True)
    data_user = result["result"]["user"]

    expect(user.name).to_equal("Updated name")
    expect(data_user["name"]).to_equal("Updated name")
    expect(user.groups).to_have_length(1)
    expect(user.groups[0].id).to_equal("system-read-only")
    expect(data_user["group_ids"]).to_equal(["system-read-only"])


@test
async def update_requires_admin(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_read_only_access_token: str = Depends(hass_read_only_access_token_fx),
) -> None:
    """Test update command requires an admin."""
    client = await hass_ws_client(hass, hass_read_only_access_token)

    user = await hass.auth.async_create_user("Test user")

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth/update",
            "user_id": user.id,
            "name": "Updated name",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("unauthorized")
    expect(user.name).to_equal("Test user")


@test
async def update_system_generated(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test update command cannot update a system generated."""
    client = await hass_ws_client(hass)

    user = await hass.auth.async_create_system_user("Test user")

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth/update",
            "user_id": user.id,
            "name": "Updated name",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("cannot_modify_system_generated")
    expect(user.name).to_equal("Test user")


@test
async def deactivate(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test deactivation and reactivation of regular user."""
    client = await hass_ws_client(hass)

    user = await hass.auth.async_create_user("Test user")
    expect(user.is_active).to_be(True)

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth/update",
            "user_id": user.id,
            "name": "Updated name",
            "is_active": False,
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(True)
    data_user = result["result"]["user"]
    expect(data_user["is_active"]).to_be(False)

    await client.send_json(
        {
            "id": 6,
            "type": "config/auth/update",
            "user_id": user.id,
            "name": "Updated name",
            "is_active": True,
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(True)
    data_user = result["result"]["user"]
    expect(data_user["is_active"]).to_be(True)


@test
async def deactivate_owner(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test that owner cannot be deactivated."""
    user = MockUser(id="abc", name="Test Owner", is_owner=True).add_to_hass(hass)

    expect(user.is_active).to_be(True)
    expect(user.is_owner).to_be(True)

    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 5, "type": "config/auth/update", "user_id": user.id, "is_active": False}
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("cannot_deactivate_owner")


@test
async def deactivate_system_generated(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test that owner cannot be deactivated."""
    client = await hass_ws_client(hass)

    user = await hass.auth.async_create_system_user("Test user")
    expect(user.is_active).to_be(True)
    expect(user.system_generated).to_be(True)
    expect(user.is_owner).to_be(False)

    await client.send_json(
        {"id": 5, "type": "config/auth/update", "user_id": user.id, "is_active": False}
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("cannot_modify_system_generated")
