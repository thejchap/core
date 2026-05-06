"""Tryke fixtures for the Yale integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, fixture
from yalexs.manager.ratelimit import _RateLimitChecker

from homeassistant.components.yale.const import DOMAIN
from homeassistant.core import HomeAssistant

from .mocks import mock_client_credentials as _mock_client_credentials, mock_config_entry as _mock_config_entry

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fx


@fixture
def mock_discovery() -> Generator[object]:
    """Mock discovery to avoid loading the whole bluetooth stack."""
    with patch(
        "homeassistant.components.yale.data.discovery_flow.async_create_flow"
    ) as mock_discovery:
        yield mock_discovery


@fixture
def disable_ratelimit_checks() -> Generator[None]:
    """Disable rate limit checks."""
    with patch.object(_RateLimitChecker, "register_wakeup"):
        yield


@fixture
def jwt() -> str:
    """Load JWT fixture data."""
    return load_fixture("jwt", DOMAIN).strip("\n")


@fixture
def reauth_jwt() -> str:
    """Load reauth JWT fixture data."""
    return load_fixture("reauth_jwt", DOMAIN).strip("\n")


@fixture
def reauth_jwt_wrong_account() -> str:
    """Load reauth wrong-account JWT fixture data."""
    return load_fixture("reauth_jwt_wrong_account", DOMAIN).strip("\n")


@fixture
def mock_config_entry(jwt: str = Depends(jwt)) -> MockConfigEntry:
    """Return the default mocked Yale config entry."""
    return _mock_config_entry(jwt=jwt)


@fixture
async def client_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Mock Yale client credentials."""
    await _mock_client_credentials(hass)


@fixture
def skip_cloud() -> Generator[None]:
    """Skip setting up the cloud integration during yale tests."""
    with patch("homeassistant.components.cloud.async_setup", return_value=True):
        yield
