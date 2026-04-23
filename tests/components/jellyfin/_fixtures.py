"""Tryke fixtures for Jellyfin integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

from jellyfin_apiclient_python import JellyfinClient
from jellyfin_apiclient_python.api import API
from jellyfin_apiclient_python.configuration import Config
from jellyfin_apiclient_python.connection_manager import ConnectionManager
from tryke import Depends, fixture

from homeassistant.components.jellyfin.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME

from . import load_json_fixture
from .const import TEST_PASSWORD, TEST_URL, TEST_USERNAME

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Jellyfin",
        domain=DOMAIN,
        data={
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
        unique_id="USER-UUID",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.jellyfin.async_setup_entry", return_value=True
    ) as setup_mock:
        yield setup_mock


@fixture
def mock_client_device_id() -> Generator[MagicMock]:
    """Mock generating device id."""
    with patch(
        "homeassistant.components.jellyfin.config_flow._generate_client_device_id"
    ) as id_mock:
        id_mock.return_value = "TEST-UUID"
        yield id_mock


@fixture
def mock_auth() -> MagicMock:
    """Return a mocked ConnectionManager."""
    jf_auth = create_autospec(ConnectionManager)
    jf_auth.connect_to_address.return_value = load_json_fixture(
        "auth-connect-address.json"
    )
    jf_auth.login.return_value = load_json_fixture("auth-login.json")
    return jf_auth


@fixture
def mock_api() -> MagicMock:
    """Return a mocked API."""
    jf_api = create_autospec(API)
    jf_api.get_user_settings.return_value = load_json_fixture("get-user-settings.json")
    jf_api.sessions.return_value = load_json_fixture("sessions.json")
    return jf_api


@fixture
def mock_config() -> MagicMock:
    """Return a mocked JellyfinClient config."""
    jf_config = create_autospec(Config)
    jf_config.data = {"auth.server": "http://localhost"}
    return jf_config


@fixture
def mock_client(
    mock_config: MagicMock = Depends(mock_config),
    mock_auth: MagicMock = Depends(mock_auth),
    mock_api: MagicMock = Depends(mock_api),
) -> MagicMock:
    """Return a mocked JellyfinClient."""
    jf_client = create_autospec(JellyfinClient)
    jf_client.auth = mock_auth
    jf_client.config = mock_config
    jf_client.jellyfin = mock_api
    return jf_client


@fixture
def mock_jellyfin(
    mock_client: MagicMock = Depends(mock_client),
) -> Generator[MagicMock]:
    """Return a mocked Jellyfin."""
    with patch(
        "homeassistant.components.jellyfin.client_wrapper.Jellyfin", autospec=True
    ) as jellyfin_mock:
        jf = jellyfin_mock.return_value
        jf.get_client.return_value = mock_client
        yield jf
