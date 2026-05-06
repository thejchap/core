"""Tests for the command_line auth provider."""

import os
from unittest.mock import AsyncMock
import uuid

from tryke import Depends, expect, fixture, test

from homeassistant import data_entry_flow
from homeassistant.auth import AuthManager, auth_store, models as auth_models
from homeassistant.auth.providers import command_line
from homeassistant.const import CONF_TYPE
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass


@fixture
async def store(hass: HomeAssistant = Depends(hass)) -> auth_store.AuthStore:
    """Mock store."""
    store = auth_store.AuthStore(hass)
    await store.async_load()
    return store


@fixture
def provider(
    hass: HomeAssistant = Depends(hass),
    store: auth_store.AuthStore = Depends(store),
) -> command_line.CommandLineAuthProvider:
    """Mock provider."""
    return command_line.CommandLineAuthProvider(
        hass,
        store,
        {
            CONF_TYPE: "command_line",
            command_line.CONF_COMMAND: os.path.join(
                os.path.dirname(__file__), "test_command_line_cmd.sh"
            ),
            command_line.CONF_ARGS: [],
            command_line.CONF_META: False,
        },
    )


@fixture
def manager(
    hass: HomeAssistant = Depends(hass),
    store: auth_store.AuthStore = Depends(store),
    provider: command_line.CommandLineAuthProvider = Depends(provider),
) -> AuthManager:
    """Mock manager."""
    return AuthManager(hass, store, {(provider.type, provider.id): provider}, {})


@test
async def create_new_credential(
    manager: AuthManager = Depends(manager),
    provider: command_line.CommandLineAuthProvider = Depends(provider),
) -> None:
    """Test that we create a new credential."""
    credentials = await provider.async_get_or_create_credentials(
        {"username": "good-user", "password": "good-pass"}
    )
    expect(credentials.is_new).to_be(True)

    user = await manager.async_get_or_create_user(credentials)
    expect(user.is_active).to_be(True)
    expect(len(user.groups)).to_equal(1)
    expect(user.groups[0].id).to_equal("system-admin")
    expect(user.local_only).to_be(False)


@test
async def match_existing_credentials(
    provider: command_line.CommandLineAuthProvider = Depends(provider),
) -> None:
    """See if we match existing users."""
    existing = auth_models.Credentials(
        id=uuid.uuid4(),
        auth_provider_type="command_line",
        auth_provider_id=None,
        data={"username": "good-user"},
        is_new=False,
    )
    provider.async_credentials = AsyncMock(return_value=[existing])
    credentials = await provider.async_get_or_create_credentials(
        {"username": "good-user", "password": "irrelevant"}
    )
    expect(credentials is existing).to_be(True)


@test
async def invalid_username(
    provider: command_line.CommandLineAuthProvider = Depends(provider),
) -> None:
    """Test we raise if incorrect user specified."""
    try:
        await provider.async_validate_login("bad-user", "good-pass")
    except command_line.InvalidAuthError:
        return
    raise AssertionError("Expected InvalidAuthError to be raised")


@test
async def invalid_password(
    provider: command_line.CommandLineAuthProvider = Depends(provider),
) -> None:
    """Test we raise if incorrect password specified."""
    try:
        await provider.async_validate_login("good-user", "bad-pass")
    except command_line.InvalidAuthError:
        return
    raise AssertionError("Expected InvalidAuthError to be raised")


@test
async def good_auth(
    provider: command_line.CommandLineAuthProvider = Depends(provider),
) -> None:
    """Test nothing is raised with good credentials."""
    await provider.async_validate_login("good-user", "good-pass")


@test
async def good_auth_with_meta(
    manager: AuthManager = Depends(manager),
    provider: command_line.CommandLineAuthProvider = Depends(provider),
) -> None:
    """Test metadata is added upon successful authentication."""
    provider.config[command_line.CONF_ARGS] = ["--with-meta"]
    provider.config[command_line.CONF_META] = True

    await provider.async_validate_login("good-user", "good-pass")

    credentials = await provider.async_get_or_create_credentials(
        {"username": "good-user", "password": "good-pass"}
    )
    expect(credentials.is_new).to_be(True)

    user = await manager.async_get_or_create_user(credentials)
    expect(user.name).to_equal("Bob")
    expect(user.is_active).to_be(True)
    expect(len(user.groups)).to_equal(1)
    expect(user.groups[0].id).to_equal("system-users")
    expect(user.local_only).to_be(True)


@test
async def utf_8_username_password(
    provider: command_line.CommandLineAuthProvider = Depends(provider),
) -> None:
    """Test that we create a new credential."""
    credentials = await provider.async_get_or_create_credentials(
        {"username": "ßßß", "password": "äöü"}
    )
    expect(credentials.is_new).to_be(True)


@test
async def login_flow_validates(
    provider: command_line.CommandLineAuthProvider = Depends(provider),
) -> None:
    """Test login flow."""
    flow = await provider.async_login_flow({})
    result = await flow.async_step_init()
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    result = await flow.async_step_init(
        {"username": "bad-user", "password": "bad-pass"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("invalid_auth")

    result = await flow.async_step_init(
        {"username": "good-user", "password": "good-pass"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]["username"]).to_equal("good-user")


@test
async def strip_username(
    provider: command_line.CommandLineAuthProvider = Depends(provider),
) -> None:
    """Test authentication works with username with whitespace around."""
    flow = await provider.async_login_flow({})
    result = await flow.async_step_init(
        {"username": "\t\ngood-user ", "password": "good-pass"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]["username"]).to_equal("good-user")
