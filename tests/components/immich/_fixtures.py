"""Tryke fixtures for the Immich integration."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

from aioimmich import ImmichUsers
from aioimmich.users.models import ImmichUserObject
from tryke import Depends, fixture

from homeassistant.components.immich.const import DOMAIN
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
)

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.immich.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "localhost",
            CONF_PORT: 80,
            CONF_SSL: False,
            CONF_API_KEY: "api_key",
            CONF_VERIFY_SSL: True,
        },
        unique_id="e7ef5713-9dab-4bd4-b899-715b0ca4379e",
        title="Someone",
    )


@fixture
def mock_immich_user() -> AsyncMock:
    """Mock the Immich server."""
    mock = AsyncMock(spec=ImmichUsers)
    mock.async_get_my_user.return_value = ImmichUserObject.from_dict(
        {
            "id": "e7ef5713-9dab-4bd4-b899-715b0ca4379e",
            "email": "user@immich.local",
            "name": "user",
            "profileImagePath": "",
            "avatarColor": "primary",
            "profileChangedAt": "2025-05-11T10:07:46.866Z",
            "storageLabel": "user",
            "shouldChangePassword": True,
            "isAdmin": True,
            "createdAt": "2025-05-11T10:07:46.866Z",
            "deletedAt": None,
            "updatedAt": "2025-05-18T00:59:55.547Z",
            "oauthId": "",
            "quotaSizeInBytes": None,
            "quotaUsageInBytes": 119526467534,
            "status": "active",
            "license": None,
        }
    )
    return mock


@fixture
async def mock_immich(
    mock_immich_user: AsyncMock = Depends(mock_immich_user),
) -> AsyncGenerator[AsyncMock]:
    """Mock the Immich API."""
    with (
        patch(
            "homeassistant.components.immich.coordinator.Immich", autospec=True
        ) as mock_immich,
        patch("homeassistant.components.immich.config_flow.Immich", new=mock_immich),
    ):
        client = mock_immich.return_value
        client.users = mock_immich_user
        yield client
