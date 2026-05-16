"""Tryke fixtures for ZoneMinder integration tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, PropertyMock, patch

from tryke import Depends, fixture

from homeassistant.components.zoneminder.const import DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)

from .conftest import MOCK_HOST, MOCK_HOST_2, create_mock_monitor

CONF_PATH_ZMS = "path_zms"


@fixture
def single_server_config() -> dict:
    """Return minimal single ZM server YAML config."""
    return {
        DOMAIN: [
            {
                CONF_HOST: MOCK_HOST,
                CONF_USERNAME: "admin",
                CONF_PASSWORD: "secret",
            }
        ]
    }


@fixture
def multi_server_config() -> dict:
    """Return two ZM servers with different settings."""
    return {
        DOMAIN: [
            {
                CONF_HOST: MOCK_HOST,
                CONF_USERNAME: "admin",
                CONF_PASSWORD: "secret",
            },
            {
                CONF_HOST: MOCK_HOST_2,
                CONF_USERNAME: "user2",
                CONF_PASSWORD: "pass2",
                CONF_SSL: True,
                CONF_VERIFY_SSL: False,
                "path": "/zoneminder/",
                CONF_PATH_ZMS: "/zoneminder/cgi-bin/nph-zms",
            },
        ]
    }


@fixture
def two_monitors() -> list[MagicMock]:
    """Pre-built list of 2 monitors."""
    from zoneminder.monitor import MonitorState  # noqa: PLC0415

    return [
        create_mock_monitor(
            monitor_id=1,
            name="Front Door",
            function=MonitorState.MODECT,
            is_recording=True,
            is_available=True,
        ),
        create_mock_monitor(
            monitor_id=2,
            name="Back Yard",
            function=MonitorState.MONITOR,
            is_recording=False,
            is_available=True,
        ),
    ]


@fixture
def mock_zoneminder_client(
    two_monitors: list[MagicMock] = Depends(two_monitors),
) -> Generator[MagicMock]:
    """Mock a ZoneMinder client."""
    with patch(
        "homeassistant.components.zoneminder.ZoneMinder",
        autospec=True,
    ) as mock_cls:
        client = mock_cls.return_value
        client.login.return_value = True
        client.get_monitors.return_value = two_monitors
        client.get_active_state.return_value = "Running"
        client.set_active_state.return_value = True

        # is_available and verify_ssl are properties in zm-py
        type(client).is_available = PropertyMock(return_value=True)
        type(client).verify_ssl = PropertyMock(return_value=True)

        # Expose the class mock so tests can inspect constructor call_args
        # without needing their own inline patch block.
        client.mock_cls = mock_cls

        yield client
