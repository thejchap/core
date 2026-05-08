"""Tryke fixtures for the Seko PoolDose integration."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from pooldose.request_status import RequestStatus
from tryke import Depends, fixture

from homeassistant.components.pooldose.const import DOMAIN
from homeassistant.const import CONF_HOST

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def device_info() -> dict[str, Any]:
    """Return the device info from the fixture."""
    return load_json_object_fixture("deviceinfo.json", DOMAIN)


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.pooldose.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_pooldose_client(
    device_info: dict[str, Any] = Depends(device_info),
) -> Generator[MagicMock]:
    """Mock a PooldoseClient for end-to-end testing."""
    with (
        patch(
            "homeassistant.components.pooldose.config_flow.PooldoseClient",
            autospec=True,
        ) as mock_client_class,
        patch(
            "homeassistant.components.pooldose.PooldoseClient", new=mock_client_class
        ),
    ):
        client = mock_client_class.return_value
        client.device_info = device_info

        client.connect.return_value = RequestStatus.SUCCESS
        client.check_apiversion_supported.return_value = (RequestStatus.SUCCESS, {})

        instant_values_data = load_json_object_fixture("instantvalues.json", DOMAIN)
        client.instant_values_structured.return_value = (
            RequestStatus.SUCCESS,
            instant_values_data,
        )

        client.set_switch = AsyncMock(return_value=RequestStatus.SUCCESS)
        client.set_select = AsyncMock(return_value=RequestStatus.SUCCESS)
        client.is_connected = True
        yield client


@fixture
def mock_config_entry(
    device_info: dict[str, Any] = Depends(device_info),
) -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Pool Device",
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100"},
        unique_id=device_info["SERIAL_NUMBER"],
        entry_id="01JG00V55WEVTJ0CJHM0GAD7PC",
    )
