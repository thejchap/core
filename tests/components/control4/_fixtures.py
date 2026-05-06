"""Tryke fixtures for Control4 tests."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.control4.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform

from tests.common import MockConfigEntry, load_fixture

MOCK_HOST = "192.168.1.100"
MOCK_USERNAME = "test-username"
MOCK_PASSWORD = "test-password"
MOCK_CONTROLLER_UNIQUE_ID = "control4_test_123"


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Controller",
        data={
            CONF_HOST: MOCK_HOST,
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
            "controller_unique_id": MOCK_CONTROLLER_UNIQUE_ID,
        },
        unique_id="00:aa:00:aa:00:aa",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock control4 setup entry."""
    with patch(
        "homeassistant.components.control4.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_c4_account() -> Generator[MagicMock]:
    """Mock a Control4 Account client."""
    with (
        patch(
            "homeassistant.components.control4.C4Account", autospec=True
        ) as mock_account_class,
        patch(
            "homeassistant.components.control4.config_flow.C4Account",
            new=mock_account_class,
        ),
    ):
        mock_account = mock_account_class.return_value
        mock_account.getAccountBearerToken = AsyncMock()
        mock_account.getAccountControllers = AsyncMock(
            return_value={
                "controllerCommonName": "control4_model_00AA00AA00AA",
                "href": "https://apis.control4.com/account/v3/rest/accounts/000000",
                "name": "Name",
            }
        )
        mock_account.getDirectorBearerToken = AsyncMock(return_value={"token": "test"})
        mock_account.getControllerOSVersion = AsyncMock(return_value="3.2.0")
        yield mock_account


@fixture
def mock_c4_director() -> Generator[MagicMock]:
    """Mock a Control4 Director client."""
    with (
        patch(
            "homeassistant.components.control4.C4Director", autospec=True
        ) as mock_director_class,
        patch(
            "homeassistant.components.control4.config_flow.C4Director",
            new=mock_director_class,
        ),
    ):
        mock_director = mock_director_class.return_value
        mock_director.getAllItemInfo = AsyncMock(
            return_value=load_fixture("director_all_items.json", DOMAIN)
        )
        mock_director.getUiConfiguration = AsyncMock(
            return_value=load_fixture("ui_configuration.json", DOMAIN)
        )
        yield mock_director


@fixture
async def mock_patch_platforms() -> AsyncGenerator[None]:
    """Patch PLATFORMS to media_player only."""
    with patch(
        "homeassistant.components.control4.PLATFORMS", [Platform.MEDIA_PLAYER]
    ):
        yield
