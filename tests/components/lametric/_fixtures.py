"""Tryke fixtures for the lametric integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from demetriek import CloudDevice, Device
from tryke import Depends, fixture

from homeassistant.components.lametric.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_MAC
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_fixture, load_json_array_fixture
from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_application_credentials


@fixture
async def setup_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up LaMetric application credentials."""
    await setup_application_credentials(
        hass, DOMAIN, "client", "secret", "credentials"
    )


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="My LaMetric",
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.2",
            CONF_API_KEY: "mock-from-fixture",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
        },
        unique_id="SA110405124500W00BS9",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.lametric.async_setup_entry", return_value=True
    ):
        yield


@fixture
def mock_lametric_cloud() -> Generator[MagicMock]:
    """Return a mocked LaMetric Cloud client."""
    with patch(
        "homeassistant.components.lametric.config_flow.LaMetricCloud", autospec=True
    ) as lametric_mock:
        lametric = lametric_mock.return_value
        lametric.devices.return_value = [
            CloudDevice.from_dict(cloud_device)
            for cloud_device in load_json_array_fixture("cloud_devices.json", DOMAIN)
        ]
        yield lametric


@fixture
def device_fixture() -> str:
    """Return the device fixture for a specific device."""
    return "device"


@fixture
def mock_lametric(
    device_fixture: str = Depends(device_fixture),
) -> Generator[MagicMock]:
    """Return a mocked LaMetric TIME client."""
    with (
        patch(
            "homeassistant.components.lametric.coordinator.LaMetricDevice",
            autospec=True,
        ) as lametric_mock,
        patch(
            "homeassistant.components.lametric.config_flow.LaMetricDevice",
            new=lametric_mock,
        ),
    ):
        lametric = lametric_mock.return_value
        lametric.api_key = "mock-api-key"
        lametric.host = "127.0.0.1"
        lametric.device.return_value = Device.from_json(
            load_fixture(f"{device_fixture}.json", DOMAIN)
        )
        yield lametric


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_lametric: MagicMock = Depends(mock_lametric),
) -> MockConfigEntry:
    """Set up the LaMetric integration for testing."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
