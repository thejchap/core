"""Tryke fixtures for the Flume integration."""

from __future__ import annotations

from collections.abc import Generator
import datetime
from http import HTTPStatus
from unittest.mock import patch

import jwt
import requests
import requests_mock
from tryke import Depends, fixture

from homeassistant.components.flume.const import DOMAIN
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

USER_ID = "test-user-id"
REFRESH_TOKEN = "refresh-token"
TOKEN_URL = "https://api.flumetech.com/oauth/token"
DEVICE_LIST_URL = (
    "https://api.flumetech.com/users/test-user-id/devices?user=true&location=true"
)
BRIDGE_DEVICE = {
    "id": "1234",
    "type": 1,
    "location": {"name": "Bridge Location"},
    "name": "Flume Bridge",
    "connected": True,
}
SENSOR_DEVICE = {
    "id": "1234",
    "type": 2,
    "location": {"name": "Sensor Location"},
    "name": "Flume Sensor",
    "connected": True,
}
DEVICE_LIST = [BRIDGE_DEVICE, SENSOR_DEVICE]


def encode_access_token() -> str:
    """Encode the payload of the access token."""
    expiration_time = datetime.datetime.now() + datetime.timedelta(hours=12)
    payload = {
        "user_id": USER_ID,
        "exp": int(expiration_time.timestamp()),
    }
    return jwt.encode(payload, key="secret")


@fixture
def requests_mocker() -> Generator[requests_mock.Mocker]:
    """Provide a requests_mock Mocker."""
    with requests_mock.Mocker() as mocker:
        yield mocker


@fixture
def access_token(
    mocker: requests_mock.Mocker = Depends(requests_mocker),
) -> Generator[None]:
    """Set up the access token endpoint."""
    token_response = {
        "refresh_token": REFRESH_TOKEN,
        "access_token": encode_access_token(),
    }
    mocker.register_uri(
        "POST",
        TOKEN_URL,
        status_code=HTTPStatus.OK,
        json={"data": [token_response]},
    )
    with patch("homeassistant.components.flume.coordinator.FlumeAuth.write_token_file"):
        yield


@fixture
def device_list(
    mocker: requests_mock.Mocker = Depends(requests_mocker),
) -> None:
    """Set up the device list response."""
    mocker.register_uri(
        "GET",
        DEVICE_LIST_URL,
        status_code=HTTPStatus.OK,
        json={"data": DEVICE_LIST},
    )


@fixture
def device_list_timeout(
    mocker: requests_mock.Mocker = Depends(requests_mocker),
) -> None:
    """Set up a timeout for device list."""
    mocker.register_uri(
        "GET",
        DEVICE_LIST_URL,
        exc=requests.exceptions.ConnectTimeout,
    )


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Create a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test-username",
        unique_id="test-username",
        data={
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_CLIENT_ID: "client_id",
            CONF_CLIENT_SECRET: "client_secret",
        },
    )
    entry.add_to_hass(hass)
    return entry
