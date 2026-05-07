"""Tryke fixtures for the mikrotik integration."""

from collections.abc import Generator
from unittest.mock import patch

import librouteros
from tryke import fixture

from homeassistant.components.mikrotik.const import (
    CONF_ARP_PING,
    CONF_DETECTION_TIME,
    CONF_FORCE_DHCP,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)

DEMO_USER_INPUT = {
    CONF_HOST: "0.0.0.0",
    CONF_USERNAME: "username",
    CONF_PASSWORD: "password",
    CONF_PORT: 8278,
    CONF_VERIFY_SSL: False,
}

DEMO_CONFIG_ENTRY = {
    CONF_HOST: "0.0.0.0",
    CONF_USERNAME: "username",
    CONF_PASSWORD: "password",
    CONF_PORT: 8278,
    CONF_VERIFY_SSL: False,
    CONF_FORCE_DHCP: False,
    CONF_ARP_PING: False,
    CONF_DETECTION_TIME: 30,
}


@fixture
def api() -> Generator[None]:
    """Mock an API."""
    with patch("librouteros.connect"):
        yield


@fixture
def auth_error() -> Generator[None]:
    """Mock an API auth error."""
    with patch(
        "librouteros.connect",
        side_effect=librouteros.exceptions.TrapError("invalid user name or password"),
    ):
        yield


@fixture
def conn_error() -> Generator[None]:
    """Mock an API connection error."""
    with patch(
        "librouteros.connect", side_effect=librouteros.exceptions.ConnectionClosed
    ):
        yield
