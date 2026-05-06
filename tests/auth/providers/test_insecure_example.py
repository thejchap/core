"""Tests for the insecure example auth provider."""

from unittest.mock import AsyncMock
import uuid

from tryke import Depends, expect, fixture, test

from homeassistant.auth import AuthManager, auth_store, models as auth_models
from homeassistant.auth.providers import insecure_example
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
) -> insecure_example.ExampleAuthProvider:
    """Mock provider."""
    return insecure_example.ExampleAuthProvider(
        hass,
        store,
        {
            "type": "insecure_example",
            "users": [
                {
                    "name": "Test Name",
                    "username": "user-test",
                    "password": "password-test",
                },
                {"username": "🎉", "password": "😎"},
            ],
        },
    )


@fixture
def manager(
    hass: HomeAssistant = Depends(hass),
    store: auth_store.AuthStore = Depends(store),
    provider: insecure_example.ExampleAuthProvider = Depends(provider),
) -> AuthManager:
    """Mock manager."""
    return AuthManager(hass, store, {(provider.type, provider.id): provider}, {})


@test
async def create_new_credential(
    manager: AuthManager = Depends(manager),
    provider: insecure_example.ExampleAuthProvider = Depends(provider),
) -> None:
    """Test that we create a new credential."""
    credentials = await provider.async_get_or_create_credentials(
        {"username": "user-test", "password": "password-test"}
    )
    expect(credentials.is_new).to_be(True)

    user = await manager.async_get_or_create_user(credentials)
    expect(user.name).to_equal("Test Name")
    expect(user.is_active).to_be(True)


@test
async def match_existing_credentials(
    provider: insecure_example.ExampleAuthProvider = Depends(provider),
) -> None:
    """See if we match existing users."""
    existing = auth_models.Credentials(
        id=uuid.uuid4(),
        auth_provider_type="insecure_example",
        auth_provider_id=None,
        data={"username": "user-test"},
        is_new=False,
    )
    provider.async_credentials = AsyncMock(return_value=[existing])
    credentials = await provider.async_get_or_create_credentials(
        {"username": "user-test", "password": "password-test"}
    )
    expect(credentials is existing).to_be(True)


@test
async def verify_username(
    provider: insecure_example.ExampleAuthProvider = Depends(provider),
) -> None:
    """Test we raise if incorrect user specified."""
    try:
        await provider.async_validate_login("non-existing-user", "password-test")
    except insecure_example.InvalidAuthError:
        return
    raise AssertionError("Expected InvalidAuthError to be raised")


@test
async def verify_password(
    provider: insecure_example.ExampleAuthProvider = Depends(provider),
) -> None:
    """Test we raise if incorrect user specified."""
    try:
        await provider.async_validate_login("user-test", "incorrect-password")
    except insecure_example.InvalidAuthError:
        return
    raise AssertionError("Expected InvalidAuthError to be raised")


@test
async def utf_8_username_password(
    provider: insecure_example.ExampleAuthProvider = Depends(provider),
) -> None:
    """Test that we create a new credential."""
    credentials = await provider.async_get_or_create_credentials(
        {"username": "🎉", "password": "😎"}
    )
    expect(credentials.is_new).to_be(True)
