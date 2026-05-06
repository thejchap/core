"""Tryke fixtures for the WaterFurnace integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

from tryke import fixture
from waterfurnace.waterfurnace import WFGateway, WFNoDataError, WFReading

from homeassistant.components.waterfurnace.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.waterfurnace.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_waterfurnace_client() -> Generator[Mock]:
    """Mock WaterFurnace client."""
    with (
        patch(
            "homeassistant.components.waterfurnace.config_flow.WaterFurnace",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.waterfurnace.WaterFurnace",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.gwid = "TEST_GWID_12345"
        client.account_id = "test_account_id"

        gateway_data = {
            "gwid": "TEST_GWID_12345",
            "description": "Test WaterFurnace Device",
            "awlabctypedesc": "Test ABC Type",
        }
        client.devices = [WFGateway(gateway_data)]

        device_data = WFReading(load_json_object_fixture("device_data.json", DOMAIN))
        client.read.return_value = device_data
        client.read_with_retry.return_value = device_data
        client.get_energy_data.side_effect = WFNoDataError("No data")

        yield client


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="WaterFurnace test_user",
        data={
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_password",
        },
        unique_id="test_account_id",
        version=1,
        minor_version=2,
    )
