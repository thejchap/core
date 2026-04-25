"""Tryke fixtures for the Ecovacs integration."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from deebot_client import const
from deebot_client.exceptions import ApiError
from deebot_client.models import Credentials
from tryke import Depends, fixture

from homeassistant.components.ecovacs.const import DOMAIN
from homeassistant.const import CONF_USERNAME

from .const import VALID_ENTRY_DATA_CLOUD

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.ecovacs.async_setup_entry", return_value=True
    ) as async_setup_entry:
        yield async_setup_entry


@fixture
def mock_config_entry_data() -> dict[str, Any]:
    """Return the default mocked config entry data."""
    return VALID_ENTRY_DATA_CLOUD


@fixture
def mock_config_entry(
    data: dict[str, Any] = Depends(mock_config_entry_data),
) -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title=data[CONF_USERNAME],
        domain=DOMAIN,
        data=data,
    )


@fixture
def device_fixture() -> str:
    """Device class returned by the get_devices api call."""
    return "yna5x1"


@fixture
def mock_authenticator(
    device_class: str = Depends(device_fixture),
) -> Generator[Mock]:
    """Mock the authenticator."""
    with (
        patch(
            "homeassistant.components.ecovacs.controller.Authenticator",
            autospec=True,
        ) as mock,
        patch(
            "homeassistant.components.ecovacs.config_flow.Authenticator",
            new=mock,
        ),
    ):
        authenticator = mock.return_value
        authenticator.authenticate.return_value = Credentials("token", "user_id", 0)

        devices = [
            load_json_object_fixture(f"devices/{device_class}/device.json", DOMAIN)
        ]

        async def post_authenticated(
            path: str,
            json: dict[str, Any],
            *,
            query_params: dict[str, Any] | None = None,
            headers: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            match path:
                case const.PATH_API_APPSVR_APP:
                    return {"code": 0, "devices": devices, "errno": "0"}
                case const.PATH_API_USERS_USER:
                    return {"todo": "result", "result": "ok", "devices": devices}
                case _:
                    raise ApiError("Path not mocked: {path}")

        authenticator.post_authenticated.side_effect = post_authenticated
        yield authenticator


@fixture
def mock_authenticator_authenticate(
    authenticator: Mock = Depends(mock_authenticator),
) -> AsyncMock:
    """Mock authenticator.authenticate."""
    return authenticator.authenticate


@fixture
def mock_mqtt_client(
    authenticator: Mock = Depends(mock_authenticator),
) -> Generator[Mock]:
    """Mock the MQTT client."""
    with (
        patch(
            "homeassistant.components.ecovacs.controller.MqttClient",
            autospec=True,
        ) as mock,
        patch(
            "homeassistant.components.ecovacs.config_flow.MqttClient",
            new=mock,
        ),
    ):
        client = mock.return_value
        client._authenticator = authenticator
        client.subscribe.return_value = lambda: None
        yield client
