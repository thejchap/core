"""Tryke fixtures for the August integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, fixture
from yalexs.manager.ratelimit import _RateLimitChecker

from homeassistant.components.august.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import load_fixture
from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_application_credentials

CLIENT_ID = "1"
CLIENT_SECRET = "2"
USER_ID = "a76c25e5-49aa-4c14-cd0c-48a6931e2081"


@fixture
def mock_discovery() -> Generator[None]:
    """Mock discovery to avoid loading the whole bluetooth stack."""
    with patch(
        "homeassistant.components.august.data.discovery_flow.async_create_flow"
    ) as mock_disc:
        yield mock_disc


@fixture
def disable_ratelimit_checks() -> Generator[None]:
    """Disable rate limit checks."""
    with patch.object(_RateLimitChecker, "register_wakeup"):
        yield


@fixture
def jwt() -> str:
    """Load JWT fixture."""
    return load_fixture("jwt", DOMAIN).strip("\n")


@fixture
async def client_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Mock client credentials."""
    await setup_application_credentials(
        hass, DOMAIN, CLIENT_ID, CLIENT_SECRET, DOMAIN
    )


@fixture
def skip_cloud() -> Generator[None]:
    """Skip cloud setup."""
    with patch("homeassistant.components.cloud.async_setup", return_value=True):
        yield


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setup entry."""
    with patch(
        "homeassistant.components.august.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup
