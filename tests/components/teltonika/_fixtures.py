"""Tryke fixtures for Teltonika tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from teltasync.system import DeviceStatusData
from teltasync.unauthorized import UnauthorizedStatusData
from tryke import Depends, fixture

from homeassistant.components.teltonika.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.teltonika.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_teltasync() -> Generator[MagicMock]:
    """Mock Teltasync client for both config flow and init."""
    with (
        patch(
            "homeassistant.components.teltonika.config_flow.Teltasync",
            autospec=True,
        ) as mock_teltasync_class,
        patch(
            "homeassistant.components.teltonika.Teltasync",
            new=mock_teltasync_class,
        ),
    ):
        shared_client = mock_teltasync_class.return_value

        device_info = load_json_object_fixture("device_info.json", DOMAIN)
        shared_client.get_device_info.return_value = UnauthorizedStatusData(
            **device_info
        )

        system_info = load_json_object_fixture("system_info.json", DOMAIN)
        shared_client.get_system_info.return_value = DeviceStatusData(**system_info)

        yield mock_teltasync_class


@fixture
def mock_teltasync_client(
    teltasync: MagicMock = Depends(mock_teltasync),
) -> MagicMock:
    """Return the client instance from mock_teltasync."""
    return teltasync.return_value


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    device_data = load_json_object_fixture("device_data.json", DOMAIN)
    return MockConfigEntry(
        domain=DOMAIN,
        title="RUTX50 Test",
        data={
            CONF_HOST: "192.168.1.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "test_password",
        },
        unique_id=device_data["system_info"]["mnf_info"]["serial"],
    )
