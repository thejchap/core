"""Test config entries API."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.auth.providers import homeassistant as prov_ha
from homeassistant.components.config import auth_provider_homeassistant as auth_ha
from homeassistant.core import HomeAssistant

from tests.common import CLIENT_ID, MockUser
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fx,
    hass_owner_user as hass_owner_user_fx,
    hass_storage as hass_storage_fx,
    hass_ws_client as hass_ws_client_fx,
    local_auth as local_auth_fx,
    mock_network,
)
from tests.hass_fixtures import (
    hass_read_only_access_token as hass_read_only_access_token_fx,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor(_network: int = Depends(mock_network)) -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
async def setup_config(
    hass: HomeAssistant = Depends(hass_fixture),
    _local_auth: prov_ha.HassAuthProvider = Depends(local_auth_fx),
) -> HomeAssistant:
    """Set up the auth provider homeassistant module on the hass instance."""
    auth_ha.async_setup(hass)
    return hass


@fixture
async def auth_provider(
    local_auth: prov_ha.HassAuthProvider = Depends(local_auth_fx),
) -> prov_ha.HassAuthProvider:
    """Hass auth provider."""
    return local_auth


@fixture
async def owner_access_token(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_owner_user: MockUser = Depends(hass_owner_user_fx),
) -> str:
    """Access token for owner user."""
    refresh_token = await hass.auth.async_create_refresh_token(
        hass_owner_user, CLIENT_ID
    )
    return hass.auth.async_create_access_token(refresh_token)


@fixture
async def hass_admin_credential(
    hass: HomeAssistant = Depends(hass_fixture),
    auth_provider: prov_ha.HassAuthProvider = Depends(auth_provider),
) -> Any:
    """Overload credentials to admin user."""
    await hass.async_add_executor_job(
        auth_provider.data.add_auth, "test-user", "test-pass"
    )

    return await auth_provider.async_get_or_create_credentials(
        {"username": "test-user"}
    )


@fixture
async def hass_admin_user_linked(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    credential: Any = Depends(hass_admin_credential),
) -> MockUser:
    """Link the admin user with the local credential."""
    await hass.auth.async_link_user(hass_admin_user, credential)
    return hass_admin_user


@test
async def create_auth_system_generated_user(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test we can't add auth to system generated users."""
    system_user = MockUser(system_generated=True).add_to_hass(hass)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/homeassistant/create",
            "user_id": system_user.id,
            "username": "test-user",
            "password": "test-pass",
        }
    )

    result = await client.receive_json()

    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("system_generated")


@test
async def create_auth_user_already_credentials() -> None:
    """Test we can't create auth for user with pre-existing credentials."""
    # assert False


@test
async def create_auth_unknown_user(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test create pointing at unknown user."""
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/homeassistant/create",
            "user_id": "test-id",
            "username": "test-user",
            "password": "test-pass",
        }
    )

    result = await client.receive_json()

    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("not_found")


@test
async def create_auth_requires_admin(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_read_only_access_token: str = Depends(hass_read_only_access_token_fx),
) -> None:
    """Test create requires admin to call API."""
    client = await hass_ws_client(hass, hass_read_only_access_token)

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/homeassistant/create",
            "user_id": "test-id",
            "username": "test-user",
            "password": "test-pass",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("unauthorized")


@test
async def create_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test create auth command works."""
    client = await hass_ws_client(hass)
    user = MockUser().add_to_hass(hass)

    expect(len(user.credentials)).to_equal(0)

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/homeassistant/create",
            "user_id": user.id,
            "username": "test-user2",
            "password": "test-pass",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(True)
    expect(len(user.credentials)).to_equal(1)
    creds = user.credentials[0]
    expect(creds.auth_provider_type).to_equal("homeassistant")
    expect(creds.auth_provider_id).to_be(None)
    expect(creds.data).to_equal({"username": "test-user2"})
    expect(prov_ha.STORAGE_KEY in hass_storage).to_be(True)
    entry = hass_storage[prov_ha.STORAGE_KEY]["data"]["users"][1]
    expect(entry["username"]).to_equal("test-user2")


@test
async def create_auth_duplicate_username(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test we can't create auth with a duplicate username."""
    client = await hass_ws_client(hass)
    user = MockUser().add_to_hass(hass)

    hass_storage[prov_ha.STORAGE_KEY] = {
        "version": 1,
        "data": {"users": [{"username": "test-user"}]},
    }

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/homeassistant/create",
            "user_id": user.id,
            "username": "test-user",
            "password": "test-pass",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]).to_equal(
        {
            "code": "home_assistant_error",
            "message": "username_already_exists",
            "translation_key": "username_already_exists",
            "translation_placeholders": {"username": "test-user"},
            "translation_domain": "auth",
        }
    )


@test
async def delete_removes_just_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test deleting an auth without being connected to a user."""
    client = await hass_ws_client(hass)

    hass_storage[prov_ha.STORAGE_KEY] = {
        "version": 1,
        "data": {"users": [{"username": "test-user"}]},
    }

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/homeassistant/delete",
            "username": "test-user",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(True)
    expect(len(hass_storage[prov_ha.STORAGE_KEY]["data"]["users"])).to_equal(0)


@test
async def delete_removes_credential(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test deleting auth that is connected to a user."""
    client = await hass_ws_client(hass)

    user = MockUser().add_to_hass(hass)
    hass_storage[prov_ha.STORAGE_KEY] = {
        "version": 1,
        "data": {"users": [{"username": "test-user"}]},
    }

    user.credentials.append(
        await hass.auth.auth_providers[0].async_get_or_create_credentials(
            {"username": "test-user"}
        )
    )

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/homeassistant/delete",
            "username": "test-user",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(True)
    expect(len(hass_storage[prov_ha.STORAGE_KEY]["data"]["users"])).to_equal(0)


@test
async def delete_requires_admin(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_read_only_access_token: str = Depends(hass_read_only_access_token_fx),
) -> None:
    """Test delete requires admin."""
    client = await hass_ws_client(hass, hass_read_only_access_token)

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/homeassistant/delete",
            "username": "test-user",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("unauthorized")


@test
async def delete_unknown_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test trying to delete an unknown auth username."""
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/homeassistant/delete",
            "username": "test-user2",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]).to_equal(
        {
            "code": "home_assistant_error",
            "message": "user_not_found",
            "translation_key": "user_not_found",
            "translation_placeholders": None,
            "translation_domain": "auth",
        }
    )


@test
async def change_password(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    auth_provider: prov_ha.HassAuthProvider = Depends(auth_provider),
    _admin_linked: MockUser = Depends(hass_admin_user_linked),
) -> None:
    """Test that change password succeeds with valid password."""
    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/homeassistant/change_password",
            "current_password": "test-pass",
            "new_password": "new-pass",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(True)
    await auth_provider.async_validate_login("test-user", "new-pass")


@test
async def change_password_wrong_pw(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    _admin_linked: MockUser = Depends(hass_admin_user_linked),
    auth_provider: prov_ha.HassAuthProvider = Depends(auth_provider),
) -> None:
    """Test that change password fails with invalid password."""
    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/homeassistant/change_password",
            "current_password": "wrong-pass",
            "new_password": "new-pass",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("invalid_current_password")
    async with expect_raises_async(prov_ha.InvalidAuth):
        await auth_provider.async_validate_login("test-user", "new-pass")


@test
async def change_password_no_creds(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that change password fails with no credentials."""
    hass_admin_user.credentials.clear()
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/homeassistant/change_password",
            "current_password": "test-pass",
            "new_password": "new-pass",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("credentials_not_found")


@test
async def admin_change_password_not_owner(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    auth_provider: prov_ha.HassAuthProvider = Depends(auth_provider),
    _admin_linked: MockUser = Depends(hass_admin_user_linked),
) -> None:
    """Test that change password fails when not owner."""
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/homeassistant/admin_change_password",
            "user_id": "test-user",
            "password": "new-pass",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("unauthorized")

    # Validate old login still works
    await auth_provider.async_validate_login("test-user", "test-pass")


@test
async def admin_change_password_no_user(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    owner_access_token: str = Depends(owner_access_token),
) -> None:
    """Test that change password fails with unknown user."""
    client = await hass_ws_client(hass, owner_access_token)

    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/homeassistant/admin_change_password",
            "user_id": "non-existing",
            "password": "new-pass",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("user_not_found")


@test
async def admin_change_password_no_cred(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    owner_access_token: str = Depends(owner_access_token),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that change password fails with unknown credential."""
    hass_admin_user.credentials.clear()
    client = await hass_ws_client(hass, owner_access_token)

    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/homeassistant/admin_change_password",
            "user_id": hass_admin_user.id,
            "password": "new-pass",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("credentials_not_found")


@test
async def admin_change_password_test(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    owner_access_token: str = Depends(owner_access_token),
    auth_provider: prov_ha.HassAuthProvider = Depends(auth_provider),
    hass_admin_user: MockUser = Depends(hass_admin_user_linked),
) -> None:
    """Test that owners can change any password."""
    client = await hass_ws_client(hass, owner_access_token)

    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/homeassistant/admin_change_password",
            "user_id": hass_admin_user.id,
            "password": "new-pass",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(True)

    await auth_provider.async_validate_login("test-user", "new-pass")


def _assert_username(
    local_auth: prov_ha.HassAuthProvider, username: str, *, should_exist: bool
) -> None:
    if any(user["username"] == username for user in local_auth.data.users):
        if should_exist:
            return  # found

        raise AssertionError(
            f"Found user with username {username} when not expected"
        )

    if should_exist:
        raise AssertionError(f"Did not find user with username {username}")


async def _do_admin_change_username(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    local_auth: prov_ha.HassAuthProvider,
    hass_admin_user: MockUser,
    owner_access_token: str,
    new_username: str,
) -> dict[str, Any]:
    """Test admin change username ws endpoint."""
    client = await hass_ws_client(hass, owner_access_token)
    current_username_user = hass_admin_user.credentials[0].data["username"]
    _assert_username(local_auth, current_username_user, should_exist=True)

    await client.send_json_auto_id(
        {
            "type": "config/auth_provider/homeassistant/admin_change_username",
            "user_id": hass_admin_user.id,
            "username": new_username,
        }
    )
    return await client.receive_json()


@test
async def admin_change_username_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    local_auth: prov_ha.HassAuthProvider = Depends(local_auth_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_linked),
    owner_access_token: str = Depends(owner_access_token),
) -> None:
    """Test that change username succeeds."""
    current_username = hass_admin_user.credentials[0].data["username"]
    new_username = "blabla"

    result = await _do_admin_change_username(
        hass,
        hass_ws_client,
        local_auth,
        hass_admin_user,
        owner_access_token,
        new_username,
    )

    expect(result["success"]).to_be(True)
    _assert_username(local_auth, current_username, should_exist=False)
    _assert_username(local_auth, new_username, should_exist=True)
    expect(hass_admin_user.credentials[0].data["username"]).to_equal(new_username)
    # Validate new login works
    await local_auth.async_validate_login(new_username, "test-pass")
    async with expect_raises_async(prov_ha.InvalidAuth):
        # Verify old login does not work
        await local_auth.async_validate_login(current_username, "test-pass")


@test.cases(
    test.case("leading_space", new_username=" bla"),
    test.case("trailing_space", new_username="bla "),
    test.case("uppercase", new_username="BlA"),
)
async def admin_change_username_error_not_normalized(
    new_username: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    local_auth: prov_ha.HassAuthProvider = Depends(local_auth_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_linked),
    owner_access_token: str = Depends(owner_access_token),
) -> None:
    """Test that change username raises error."""
    current_username = hass_admin_user.credentials[0].data["username"]

    result = await _do_admin_change_username(
        hass,
        hass_ws_client,
        local_auth,
        hass_admin_user,
        owner_access_token,
        new_username,
    )
    expect(result["success"]).to_be(False)
    expect(result["error"]).to_equal(
        {
            "code": "home_assistant_error",
            "message": "username_not_normalized",
            "translation_key": "username_not_normalized",
            "translation_placeholders": {"new_username": new_username},
            "translation_domain": "auth",
        }
    )
    _assert_username(local_auth, current_username, should_exist=True)
    _assert_username(local_auth, new_username, should_exist=False)
    expect(hass_admin_user.credentials[0].data["username"]).to_equal(current_username)
    # Validate old login still works
    await local_auth.async_validate_login(current_username, "test-pass")


@test
async def admin_change_username_not_owner(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    auth_provider: prov_ha.HassAuthProvider = Depends(auth_provider),
    _admin_linked: MockUser = Depends(hass_admin_user_linked),
) -> None:
    """Test that change username fails when not owner."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "config/auth_provider/homeassistant/admin_change_username",
            "user_id": "test-user",
            "username": "new-user",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("unauthorized")

    # Validate old login still works
    await auth_provider.async_validate_login("test-user", "test-pass")


@test
async def admin_change_username_no_user(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    owner_access_token: str = Depends(owner_access_token),
) -> None:
    """Test that change username fails with unknown user."""
    client = await hass_ws_client(hass, owner_access_token)

    await client.send_json_auto_id(
        {
            "type": "config/auth_provider/homeassistant/admin_change_username",
            "user_id": "non-existing",
            "username": "new-username",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("user_not_found")


@test
async def admin_change_username_no_cred(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: HomeAssistant = Depends(setup_config),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    owner_access_token: str = Depends(owner_access_token),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that change username fails with unknown credential."""
    hass_admin_user.credentials.clear()
    client = await hass_ws_client(hass, owner_access_token)

    await client.send_json_auto_id(
        {
            "type": "config/auth_provider/homeassistant/admin_change_username",
            "user_id": hass_admin_user.id,
            "username": "new-username",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]["code"]).to_equal("credentials_not_found")
