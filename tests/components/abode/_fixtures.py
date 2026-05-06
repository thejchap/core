"""Tryke fixtures for the Abode integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from jaraco.abode.helpers import urls as URL
import requests_mock
from tryke import fixture

from homeassistant.components.light import Profiles
from homeassistant.core import HomeAssistant

from tests.common import load_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.abode.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_light_profiles() -> Generator[dict]:
    """Mock loading of light profiles (autouse equivalent)."""
    data: dict = {}

    def mock_profiles_class(hass: HomeAssistant) -> Profiles:
        profiles = Profiles(hass)
        profiles.data = data
        profiles.async_initialize = AsyncMock()
        return profiles

    with patch(
        "homeassistant.components.light.Profiles",
        side_effect=mock_profiles_class,
    ):
        yield data


@fixture
def requests_mock_fixture() -> Generator[requests_mock.Mocker]:
    """Mock the upstream Abode HTTP endpoints used during setup."""
    with requests_mock.Mocker() as mocker:
        mocker.post(URL.LOGIN, text=load_fixture("login.json", "abode"))
        mocker.post(URL.LOGOUT, text=load_fixture("logout.json", "abode"))
        mocker.get(URL.OAUTH_TOKEN, text=load_fixture("oauth_claims.json", "abode"))
        mocker.get(URL.PANEL, text=load_fixture("panel.json", "abode"))
        mocker.get(URL.AUTOMATION, text=load_fixture("automation.json", "abode"))
        mocker.get(URL.DEVICES, text=load_fixture("devices.json", "abode"))
        yield mocker
