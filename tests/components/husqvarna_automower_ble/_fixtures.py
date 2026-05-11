"""Tryke fixtures for the husqvarna_automower_ble integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from automower_ble.protocol import ResponseResult
from gardena_bluetooth.parse import ManufacturerData
from tryke import Depends, fixture

from homeassistant.components.bluetooth import async_last_service_info
from homeassistant.components.husqvarna_automower_ble.const import DOMAIN
from homeassistant.const import CONF_ADDRESS, CONF_CLIENT_ID, CONF_PIN
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_bluetooth

from . import AUTOMOWER_SERVICE_INFO_SERIAL

from tests.common import MockConfigEntry
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture


@fixture
def only_discover_this_domain() -> Generator[None]:
    """Only discover devices for this domain."""

    async def filtered_matches(hass: HomeAssistant):
        matchers = await async_get_bluetooth(hass)
        return [matcher for matcher in matchers if matcher["domain"] == DOMAIN]

    with patch(
        "homeassistant.components.bluetooth.async_get_bluetooth",
        new=filtered_matches,
    ):
        yield


@fixture
def mock_get_manufacturer_data(
    hass: HomeAssistant = Depends(hass_fixture),
    _bluetooth: None = Depends(enable_bluetooth),
) -> Generator[None]:
    """Mock async_get_manufacturer_data."""

    async def _get_manufacturer_data(
        addresses: set[str], **kwargs
    ) -> dict[str, ManufacturerData]:
        result: dict[str, ManufacturerData] = {}
        for address in addresses:
            mfg = ManufacturerData()
            if service_info := async_last_service_info(hass, address):
                raw = service_info.manufacturer_data.get(ManufacturerData.company)
                if raw is not None:
                    mfg.update(raw)
            result[address] = mfg
        return result

    with patch(
        "homeassistant.components.husqvarna_automower_ble.config_flow.async_get_manufacturer_data",
        new=_get_manufacturer_data,
    ):
        yield


@fixture
def mock_automower_client(
    _bluetooth: None = Depends(enable_bluetooth),
) -> Generator[AsyncMock]:
    """Mock the Mower client."""
    with (
        patch(
            "homeassistant.components.husqvarna_automower_ble.Mower",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.husqvarna_automower_ble.config_flow.Mower",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.connect.return_value = ResponseResult.OK
        client.is_connected.return_value = True
        client.get_model.return_value = "305"
        client.battery_level.return_value = 100
        client.mower_state.return_value = "pendingStart"
        client.mower_activity.return_value = "charging"
        client.probe_gatts.return_value = ("Husqvarna", "Automower", "305")

        yield client


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Build a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Husqvarna AutoMower",
        data={
            CONF_ADDRESS: AUTOMOWER_SERVICE_INFO_SERIAL.address,
            CONF_CLIENT_ID: 1197489078,
            CONF_PIN: "1234",
        },
        unique_id=AUTOMOWER_SERVICE_INFO_SERIAL.address,
    )
