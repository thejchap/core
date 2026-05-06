"""Tryke fixtures for the Withings integration."""

from collections.abc import Generator
from datetime import timedelta
import time
from unittest.mock import AsyncMock, patch

from aiowithings import Device, WithingsClient
from aiowithings.models import NotificationConfiguration
from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.withings.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import (
    load_activity_fixture,
    load_goals_fixture,
    load_measurements_fixture,
    load_sleep_fixture,
    load_workout_fixture,
)

from tests.common import MockConfigEntry, load_json_array_fixture
from tests.hass_fixtures import hass as hass_fx

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
SCOPES = [
    "user.info",
    "user.metrics",
    "user.activity",
    "user.sleepevents",
]
TITLE = "henk"
USER_ID = 12345
WEBHOOK_ID = "55a7335ea8dee830eed4ef8f84cda8f6d80b83af0847dc74032e86120bffed5e"


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Set up application credentials."""
    await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
        DOMAIN,
    )


@fixture
def expires_at() -> int:
    """Set the OAuth token expiration time."""
    return time.time() + 3600


@fixture
def polling_config_entry(
    expires_at: int = Depends(expires_at),
) -> MockConfigEntry:
    """Create Withings entry in Home Assistant."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        unique_id=str(USER_ID),
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "status": 0,
                "userid": str(USER_ID),
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "expires_at": expires_at,
                "scope": ",".join(SCOPES),
            },
            "profile": TITLE,
            "webhook_id": WEBHOOK_ID,
        },
    )


@fixture
def withings() -> Generator[AsyncMock]:
    """Mock withings."""
    devices_json = load_json_array_fixture("withings/devices.json")
    devices = [Device.from_api(device) for device in devices_json]

    measurement_groups = load_measurements_fixture()

    notification_json = load_json_array_fixture("withings/notifications.json")
    notifications = [
        NotificationConfiguration.from_api(not_conf) for not_conf in notification_json
    ]

    workouts = load_workout_fixture()
    activities = load_activity_fixture()

    mock = AsyncMock(spec=WithingsClient)
    mock.get_devices.return_value = devices
    mock.get_goals.return_value = load_goals_fixture()
    mock.get_measurement_in_period.return_value = measurement_groups
    mock.get_measurement_since.return_value = measurement_groups
    mock.get_sleep_summary_since.return_value = load_sleep_fixture()
    mock.get_activities_since.return_value = activities
    mock.get_activities_in_period.return_value = activities
    mock.list_notification_configurations.return_value = notifications
    mock.get_workouts_since.return_value = workouts
    mock.get_workouts_in_period.return_value = workouts

    with patch(
        "homeassistant.components.withings.WithingsClient",
        return_value=mock,
    ):
        yield mock


@fixture
def disable_webhook_delay() -> Generator[None]:
    """Disable webhook delays for faster tests."""
    with (
        patch(
            "homeassistant.components.withings.SUBSCRIBE_DELAY",
            timedelta(seconds=0),
        ),
        patch(
            "homeassistant.components.withings.UNSUBSCRIBE_DELAY",
            timedelta(seconds=0),
        ),
        patch(
            "homeassistant.components.withings.WEBHOOK_REGISTER_DELAY",
            0,
        ),
    ):
        yield
