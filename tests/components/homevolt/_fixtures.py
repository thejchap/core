"""Tryke fixtures for the Homevolt integration."""

from collections.abc import Generator
import json
from unittest.mock import AsyncMock, MagicMock, patch

from homevolt import DeviceMetadata, Sensor
from tryke import fixture

from homeassistant.components.homevolt.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD

from tests.common import MockConfigEntry, load_fixture

DEVICE_IDENTIFIER = "ems_40580137858664"


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.homevolt.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Homevolt",
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "test-password",
        },
        unique_id="40580137858664",
    )


@fixture
def mock_homevolt_client() -> Generator[MagicMock]:
    """Return a mocked Homevolt client."""
    with (
        patch(
            "homeassistant.components.homevolt.Homevolt",
            autospec=True,
        ) as homevolt_mock,
        patch(
            "homeassistant.components.homevolt.config_flow.Homevolt",
            new=homevolt_mock,
        ),
    ):
        client = homevolt_mock.return_value
        client.base_url = "http://127.0.0.1"
        client.update_info = AsyncMock()
        client.close_connection = AsyncMock()
        client.unique_id = "40580137858664"

        sensors_data = json.loads(load_fixture("sensors.json", DOMAIN))
        client.sensors = {
            key: Sensor(
                value=value,
                type=key,
                device_identifier=DEVICE_IDENTIFIER,
            )
            for key, value in sensors_data.items()
        }

        metadata_data = json.loads(load_fixture("device_metadata.json", DOMAIN))
        client.device_metadata = {
            key: DeviceMetadata(
                name=metadata["name"],
                model=metadata["model"],
            )
            for key, metadata in metadata_data.items()
        }

        client.current_schedule = json.loads(load_fixture("schedule.json", DOMAIN))

        client.local_mode_enabled = False
        client.enable_local_mode = AsyncMock()
        client.disable_local_mode = AsyncMock()

        yield client
