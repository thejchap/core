"""Tryke fixtures for VeSync config flow tests."""

from collections.abc import Generator
from contextlib import ExitStack
from unittest.mock import AsyncMock, PropertyMock, patch

from pyvesync import VeSync
from pyvesync.auth import VeSyncAuth
from tryke import Depends, fixture

from homeassistant.components.vesync import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx


@fixture
def patch_vesync_login() -> Generator[None]:
    """Patch VeSync login method."""
    with patch("pyvesync.vesync.VeSync.login", new=AsyncMock()):
        yield


@fixture
def patch_vesync() -> Generator[None]:
    """Patch VeSync methods and several properties/attributes for all tests."""
    props = {
        "enabled": True,
    }

    with ExitStack() as stack:
        for name, value in props.items():
            mock = stack.enter_context(
                patch.object(VeSync, name, new_callable=PropertyMock)
            )
            mock.return_value = value
        yield


@fixture
def patch_vesync_auth() -> Generator[None]:
    """Patch VeSync Auth methods and several properties/attributes for all tests."""
    props = {
        "_token": "TESTTOKEN",
        "_account_id": "TESTACCOUNTID",
        "_country_code": "US",
        "_current_region": "US",
        "_username": "TESTUSERNAME",
        "_password": "TESTPASSWORD",
    }

    with (
        patch.multiple(
            "pyvesync.auth.VeSyncAuth",
            login=AsyncMock(return_value=True),
        ),
        ExitStack() as stack,
    ):
        for name, value in props.items():
            mock = stack.enter_context(
                patch.object(VeSyncAuth, name, new_callable=PropertyMock)
            )
            mock.return_value = value
        yield


@fixture
def config_entry(hass: HomeAssistant = Depends(hass_fx)) -> MockConfigEntry:
    """Create a mock VeSync config entry."""
    entry = MockConfigEntry(
        title="VeSync",
        domain=DOMAIN,
        data={CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
        unique_id="TESTACCOUNTID",
        version=1,
        minor_version=3,
    )
    entry.add_to_hass(hass)
    return entry
