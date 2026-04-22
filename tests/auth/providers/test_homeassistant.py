"""Test the Home Assistant local auth provider."""

import asyncio
from typing import Any
from unittest.mock import Mock, patch

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant import data_entry_flow
from homeassistant.auth import auth_manager_from_config, auth_store
from homeassistant.auth.providers import (
    auth_provider_from_config,
    homeassistant as hass_auth,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass, hass_storage, issue_registry


@fixture
async def data(hass: HomeAssistant = Depends(hass)) -> hass_auth.Data:
    """Create a loaded data class."""
    data = hass_auth.Data(hass)
    await data.async_load()
    return data


@fixture
async def legacy_data(hass: HomeAssistant = Depends(hass)) -> hass_auth.Data:
    """Create a loaded legacy data class."""
    data = hass_auth.Data(hass)
    await data.async_load()
    data.is_legacy = True
    return data


@fixture
async def load_auth_component(hass: HomeAssistant = Depends(hass)) -> None:
    """Load the auth component for translations."""
    await async_setup_component(hass, "auth", {})


@test
async def validating_password_invalid_user(
    data: hass_auth.Data = Depends(data),
) -> None:
    """Test validating an invalid user."""
    expect(lambda: data.validate_login("non-existing", "pw")).to_raise(
        hass_auth.InvalidAuth
    )


@test
async def not_allow_set_id() -> None:
    """Test we are not allowed to set an ID in config."""
    hass = Mock()
    hass.data = {}
    try:
        await auth_provider_from_config(
            hass, None, {"type": "homeassistant", "id": "invalid"}
        )
    except vol.Invalid:
        return
    raise AssertionError("Expected vol.Invalid to be raised")


@test
async def new_users_populate_values(
    hass: HomeAssistant = Depends(hass),
    data: hass_auth.Data = Depends(data),
) -> None:
    """Test that we populate data for new users."""
    data.add_auth("hello", "test-pass")
    await data.async_save()

    manager = await auth_manager_from_config(hass, [{"type": "homeassistant"}], [])
    provider = manager.auth_providers[0]
    credentials = await provider.async_get_or_create_credentials({"username": "hello"})
    user = await manager.async_get_or_create_user(credentials)
    expect(user.name).to_equal("hello")
    expect(user.is_active).to_be(True)


@test
async def changing_password_raises_invalid_user(
    data: hass_auth.Data = Depends(data),
) -> None:
    """Test that changing password raises invalid user."""
    expect(lambda: data.change_password("non-existing", "pw")).to_raise(
        hass_auth.InvalidUser
    )


# Modern mode.


@test
async def adding_user(data: hass_auth.Data = Depends(data)) -> None:
    """Test adding a user."""
    data.add_auth("test-user", "test-pass")
    data.validate_login(" test-user ", "test-pass")


@test.cases(
    test.case("with_trailing_space", username="test-user "),
    test.case("uppercase", username="TEST-USER"),
)
async def adding_user_not_normalized(
    username: str,
    data: hass_auth.Data = Depends(data),
    _load: None = Depends(load_auth_component),
) -> None:
    """Test adding a user."""
    expect(lambda: data.add_auth(username, "test-pass")).to_raise(
        hass_auth.InvalidUsername,
        match="username_not_normalized",
    )


@test
async def adding_user_duplicate_username(
    data: hass_auth.Data = Depends(data),
    _load: None = Depends(load_auth_component),
) -> None:
    """Test adding a user with duplicate username."""
    data.add_auth("test-user", "test-pass")

    expect(lambda: data.add_auth("test-user", "other-pass")).to_raise(
        hass_auth.InvalidUsername,
        match="username_already_exists",
    )


@test
async def validating_password_invalid_password(
    data: hass_auth.Data = Depends(data),
) -> None:
    """Test validating an invalid password."""
    data.add_auth("test-user", "test-pass")

    expect(lambda: data.validate_login(" test-user ", "invalid-pass")).to_raise(
        hass_auth.InvalidAuth
    )
    expect(lambda: data.validate_login("test-user", "test-pass ")).to_raise(
        hass_auth.InvalidAuth
    )
    expect(lambda: data.validate_login("test-user", "Test-pass")).to_raise(
        hass_auth.InvalidAuth
    )


@test
async def changing_password(data: hass_auth.Data = Depends(data)) -> None:
    """Test adding a user."""
    data.add_auth("test-user", "test-pass")
    data.change_password("TEST-USER ", "new-pass")

    expect(lambda: data.validate_login("test-user", "test-pass")).to_raise(
        hass_auth.InvalidAuth
    )

    data.validate_login("test-UsEr", "new-pass")


@test
async def password_truncated(data: hass_auth.Data = Depends(data)) -> None:
    """Test long passwords are truncated before they are send to bcrypt for hashing."""
    pwd_truncated = "hWwjDpFiYtDTaaMbXdjzeuKAPI3G4Di2mC92" * 4
    long_pwd = pwd_truncated * 2
    data.add_auth("test-user", long_pwd)
    data.validate_login("test-user", long_pwd)

    data.validate_login("test-user", pwd_truncated)
    expect(lambda: data.validate_login("test-user", pwd_truncated[:71])).to_raise(
        hass_auth.InvalidAuth
    )


@test
async def login_flow_validates(
    data: hass_auth.Data = Depends(data),
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test login flow."""
    data.add_auth("test-user", "test-pass")
    await data.async_save()

    provider = hass_auth.HassAuthProvider(
        hass, auth_store.AuthStore(hass), {"type": "homeassistant"}
    )
    flow = await provider.async_login_flow({})
    result = await flow.async_step_init()
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    result = await flow.async_step_init(
        {"username": "incorrect-user", "password": "test-pass"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("invalid_auth")

    result = await flow.async_step_init(
        {"username": "TEST-user ", "password": "incorrect-pass"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("invalid_auth")

    result = await flow.async_step_init(
        {"username": "test-USER", "password": "test-pass"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]["username"]).to_equal("test-USER")


@test
async def saving_loading(
    data: hass_auth.Data = Depends(data),
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test saving and loading JSON."""
    data.add_auth("test-user", "test-pass")
    data.add_auth("second-user", "second-pass")
    await data.async_save()

    data = hass_auth.Data(hass)
    await data.async_load()
    data.validate_login("test-user ", "test-pass")
    data.validate_login("second-user ", "second-pass")


@test
async def get_or_create_credentials(
    hass: HomeAssistant = Depends(hass),
    data: hass_auth.Data = Depends(data),
) -> None:
    """Test that we can get or create credentials."""
    manager = await auth_manager_from_config(hass, [{"type": "homeassistant"}], [])
    provider = manager.auth_providers[0]
    provider.data = data
    credentials1 = await provider.async_get_or_create_credentials({"username": "hello"})
    with patch.object(provider, "async_credentials", return_value=[credentials1]):
        credentials2 = await provider.async_get_or_create_credentials(
            {"username": "hello "}
        )
    expect(credentials1 is credentials2).to_be(True)


# Legacy mode.


@test
async def legacy_adding_user(
    legacy_data: hass_auth.Data = Depends(legacy_data),
) -> None:
    """Test in legacy mode adding a user."""
    legacy_data.add_auth("test-user", "test-pass")
    legacy_data.validate_login("test-user", "test-pass")


@test
async def legacy_validating_password_invalid_password(
    legacy_data: hass_auth.Data = Depends(legacy_data),
) -> None:
    """Test in legacy mode validating an invalid password."""
    legacy_data.add_auth("test-user", "test-pass")

    expect(lambda: legacy_data.validate_login("test-user", "invalid-pass")).to_raise(
        hass_auth.InvalidAuth
    )


@test
async def legacy_changing_password(
    legacy_data: hass_auth.Data = Depends(legacy_data),
) -> None:
    """Test in legacy mode adding a user."""
    user = "test-user"
    legacy_data.add_auth(user, "test-pass")
    legacy_data.change_password(user, "new-pass")

    expect(lambda: legacy_data.validate_login(user, "test-pass")).to_raise(
        hass_auth.InvalidAuth
    )

    legacy_data.validate_login(user, "new-pass")


@test
async def legacy_changing_password_raises_invalid_user(
    legacy_data: hass_auth.Data = Depends(legacy_data),
) -> None:
    """Test in legacy mode that we initialize an empty config."""
    expect(lambda: legacy_data.change_password("non-existing", "pw")).to_raise(
        hass_auth.InvalidUser
    )


@test
async def legacy_login_flow_validates(
    legacy_data: hass_auth.Data = Depends(legacy_data),
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test in legacy mode login flow."""
    legacy_data.add_auth("test-user", "test-pass")
    await legacy_data.async_save()

    provider = hass_auth.HassAuthProvider(
        hass, auth_store.AuthStore(hass), {"type": "homeassistant"}
    )
    flow = await provider.async_login_flow({})
    result = await flow.async_step_init()
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    result = await flow.async_step_init(
        {"username": "incorrect-user", "password": "test-pass"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("invalid_auth")

    result = await flow.async_step_init(
        {"username": "test-user", "password": "incorrect-pass"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("invalid_auth")

    result = await flow.async_step_init(
        {"username": "test-user", "password": "test-pass"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]["username"]).to_equal("test-user")


@test
async def legacy_saving_loading(
    legacy_data: hass_auth.Data = Depends(legacy_data),
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test in legacy mode saving and loading JSON."""
    legacy_data.add_auth("test-user", "test-pass")
    legacy_data.add_auth("second-user", "second-pass")
    await legacy_data.async_save()

    legacy_data = hass_auth.Data(hass)
    await legacy_data.async_load()
    legacy_data.is_legacy = True
    legacy_data.validate_login("test-user", "test-pass")
    legacy_data.validate_login("second-user", "second-pass")

    expect(lambda: legacy_data.validate_login("test-user ", "test-pass")).to_raise(
        hass_auth.InvalidAuth
    )


@test
async def legacy_get_or_create_credentials(
    hass: HomeAssistant = Depends(hass),
    legacy_data: hass_auth.Data = Depends(legacy_data),
) -> None:
    """Test in legacy mode that we can get or create credentials."""
    manager = await auth_manager_from_config(hass, [{"type": "homeassistant"}], [])
    provider = manager.auth_providers[0]
    provider.data = legacy_data
    credentials1 = await provider.async_get_or_create_credentials({"username": "hello"})

    with patch.object(provider, "async_credentials", return_value=[credentials1]):
        credentials2 = await provider.async_get_or_create_credentials(
            {"username": "hello"}
        )
    expect(credentials1 is credentials2).to_be(True)

    with patch.object(provider, "async_credentials", return_value=[credentials1]):
        credentials3 = await provider.async_get_or_create_credentials(
            {"username": "hello "}
        )
    expect(credentials1 is not credentials3).to_be(True)


@test
async def race_condition_in_data_loading(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test race condition in the hass_auth.Data loading."""
    counter = 0

    async def mock_load(_):
        """Mock of homeassistant.helpers.storage.Store.async_load."""
        nonlocal counter
        counter += 1
        await asyncio.sleep(0)

    provider = hass_auth.HassAuthProvider(
        hass, auth_store.AuthStore(hass), {"type": "homeassistant"}
    )
    with patch("homeassistant.helpers.storage.Store.async_load", new=mock_load):
        task1 = provider.async_validate_login("user", "pass")
        task2 = provider.async_validate_login("user", "pass")
        results = await asyncio.gather(task1, task2, return_exceptions=True)
        expect(counter).to_equal(1)
        expect(isinstance(results[0], hass_auth.InvalidAuth)).to_be(True)
        expect(isinstance(results[1], hass_auth.InvalidAuth)).to_be(True)


@test
def change_username(data: hass_auth.Data = Depends(data)) -> None:
    """Test changing username."""
    data.add_auth("test-user", "test-pass")
    users = data.users
    expect(len(users)).to_equal(1)
    expect(users[0]["username"]).to_equal("test-user")

    data.change_username("test-user", "new-user")

    users = data.users
    expect(len(users)).to_equal(1)
    expect(users[0]["username"]).to_equal("new-user")


@test.cases(
    test.case("with_trailing_space", username="test-user "),
    test.case("uppercase", username="TEST-USER"),
)
def change_username_legacy(
    username: str,
    legacy_data: hass_auth.Data = Depends(legacy_data),
) -> None:
    """Test changing username."""
    legacy_data.users.append(
        {
            "username": username,
            "password": legacy_data.hash_password("test-pass", True).decode(),
        }
    )

    users = legacy_data.users
    expect(len(users)).to_equal(1)
    expect(users[0]["username"]).to_equal(username)

    legacy_data.change_username(username, "test-user")

    users = legacy_data.users
    expect(len(users)).to_equal(1)
    expect(users[0]["username"]).to_equal("test-user")


@test
def change_username_invalid_user(data: hass_auth.Data = Depends(data)) -> None:
    """Test changing username raises on invalid user."""
    data.add_auth("test-user", "test-pass")
    users = data.users
    expect(len(users)).to_equal(1)
    expect(users[0]["username"]).to_equal("test-user")

    expect(lambda: data.change_username("non-existing", "new-user")).to_raise(
        hass_auth.InvalidUser
    )

    users = data.users
    expect(len(users)).to_equal(1)
    expect(users[0]["username"]).to_equal("test-user")


@test
async def change_username_not_normalized(
    data: hass_auth.Data = Depends(data),
    hass: HomeAssistant = Depends(hass),
    _load: None = Depends(load_auth_component),
) -> None:
    """Test changing username raises on not normalized username."""
    data.add_auth("test-user", "test-pass")

    expect(lambda: data.change_username("test-user", "TEST-user ")).to_raise(
        hass_auth.InvalidUsername,
        match="username_not_normalized",
    )


@test.cases(
    test.case(
        "uppercase",
        usernames_in_storage=["Uppercase"],
        usernames_in_repair='- "Uppercase"',
    ),
    test.case(
        "leading_space",
        usernames_in_storage=[" leading"],
        usernames_in_repair='- " leading"',
    ),
    test.case(
        "trailing_space",
        usernames_in_storage=["trailing "],
        usernames_in_repair='- "trailing "',
    ),
    test.case(
        "multiple",
        usernames_in_storage=["Test", "test", "Fritz "],
        usernames_in_repair='- "Fritz "\n- "Test"',
    ),
)
async def create_repair_on_legacy_usernames(
    usernames_in_storage: list[str],
    usernames_in_repair: str,
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
) -> None:
    """Test that we create a repair issue for legacy usernames."""
    expect(
        bool(
            issue_registry.issues.get(
                ("auth", "homeassistant_provider_not_normalized_usernames")
            )
        )
    ).to_be(False)

    hass_storage[hass_auth.STORAGE_KEY] = {
        "version": 1,
        "minor_version": 1,
        "key": "auth_provider.homeassistant",
        "data": {
            "users": [
                {
                    "username": username,
                    "password": "onlyherebecauseweneedapasswordstring",
                }
                for username in usernames_in_storage
            ]
        },
    }
    data = hass_auth.Data(hass)
    await data.async_load()
    issue = issue_registry.issues.get(
        ("auth", "homeassistant_provider_not_normalized_usernames")
    )
    expect(issue is not None).to_be(True)
    expect(issue.translation_placeholders).to_equal({"usernames": usernames_in_repair})


@test
async def delete_repair_after_fixing_usernames(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
) -> None:
    """Test that the repair is deleted after fixing the usernames."""
    hass_storage[hass_auth.STORAGE_KEY] = {
        "version": 1,
        "minor_version": 1,
        "key": "auth_provider.homeassistant",
        "data": {
            "users": [
                {
                    "username": "Test",
                    "password": "onlyherebecauseweneedapasswordstring",
                },
                {
                    "username": "bla ",
                    "password": "onlyherebecauseweneedapasswordstring",
                },
            ]
        },
    }
    data = hass_auth.Data(hass)
    await data.async_load()
    issue = issue_registry.issues.get(
        ("auth", "homeassistant_provider_not_normalized_usernames")
    )
    expect(issue is not None).to_be(True)
    expect(issue.translation_placeholders).to_equal(
        {"usernames": '- "Test"\n- "bla "'}
    )

    data.change_username("Test", "test")
    issue = issue_registry.issues.get(
        ("auth", "homeassistant_provider_not_normalized_usernames")
    )
    expect(issue is not None).to_be(True)
    expect(issue.translation_placeholders).to_equal({"usernames": '- "bla "'})

    data.change_username("bla ", "bla")
    expect(
        bool(
            issue_registry.issues.get(
                ("auth", "homeassistant_provider_not_normalized_usernames")
            )
        )
    ).to_be(False)
