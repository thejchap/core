"""The tests the for Meraki device tracker."""

from collections.abc import Generator
from http import HTTPStatus
import json
from unittest.mock import patch

from aiohttp.test_utils import TestClient
from tryke import Depends, expect, fixture, test

from homeassistant.components import device_tracker
from homeassistant.components.device_tracker import legacy
from homeassistant.components.device_tracker.legacy import Device
from homeassistant.components.meraki.device_tracker import (
    CONF_SECRET,
    CONF_VALIDATOR,
    URL,
)
from homeassistant.const import CONF_PLATFORM
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    mock_network,
)
from tests.typing import ClientSessionGenerator


@fixture
def mock_device_tracker_conf() -> Generator[list[Device]]:
    """Prevent device tracker from reading/writing data."""
    devices: list[Device] = []

    async def mock_update_config(path: str, dev_id: str, entity: Device) -> None:
        devices.append(entity)

    with (
        patch(
            (
                "homeassistant.components.device_tracker.legacy"
                ".DeviceTracker.async_update_config"
            ),
            side_effect=mock_update_config,
        ),
        patch(
            "homeassistant.components.device_tracker.legacy.async_load_config",
            side_effect=lambda *args: devices,
        ),
    ):
        yield devices


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _mock_devices: list[Device] = Depends(mock_device_tracker_conf),
) -> None:
    """Anchor for tryke fixture resolution."""


@fixture
async def meraki_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> TestClient:
    """Meraki mock client."""
    assert await async_setup_component(
        hass,
        device_tracker.DOMAIN,
        {
            device_tracker.DOMAIN: {
                CONF_PLATFORM: "meraki",
                CONF_VALIDATOR: "validator",
                CONF_SECRET: "secret",
            }
        },
    )
    await hass.async_block_till_done()

    return await hass_client()


@test
async def invalid_or_missing_data(
    _trigger: None = Depends(_trigger_executor),
    meraki_client: TestClient = Depends(meraki_client),
) -> None:
    """Test validator with invalid or missing data."""
    req = await meraki_client.get(URL)
    text = await req.text()
    expect(req.status).to_equal(HTTPStatus.OK)
    expect(text).to_equal("validator")

    req = await meraki_client.post(URL, data=b"invalid")
    text = await req.json()
    expect(req.status).to_equal(HTTPStatus.BAD_REQUEST)
    expect(text["message"]).to_equal("Invalid JSON")

    req = await meraki_client.post(URL, data=b"{}")
    text = await req.json()
    expect(req.status).to_equal(HTTPStatus.UNPROCESSABLE_ENTITY)
    expect(text["message"]).to_equal("No secret")

    data = {"version": "1.0", "secret": "secret"}
    req = await meraki_client.post(URL, data=json.dumps(data))
    text = await req.json()
    expect(req.status).to_equal(HTTPStatus.UNPROCESSABLE_ENTITY)
    expect(text["message"]).to_equal("Invalid version")

    data = {"version": "2.0", "secret": "invalid"}
    req = await meraki_client.post(URL, data=json.dumps(data))
    text = await req.json()
    expect(req.status).to_equal(HTTPStatus.UNPROCESSABLE_ENTITY)
    expect(text["message"]).to_equal("Invalid secret")

    data = {"version": "2.0", "secret": "secret", "type": "InvalidType"}
    req = await meraki_client.post(URL, data=json.dumps(data))
    text = await req.json()
    expect(req.status).to_equal(HTTPStatus.UNPROCESSABLE_ENTITY)
    expect(text["message"]).to_equal("Invalid device type")

    data = {
        "version": "2.0",
        "secret": "secret",
        "type": "BluetoothDevicesSeen",
        "data": {"observations": []},
    }
    req = await meraki_client.post(URL, data=json.dumps(data))
    expect(req.status).to_equal(HTTPStatus.OK)


@test
async def data_will_be_saved(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    meraki_client: TestClient = Depends(meraki_client),
) -> None:
    """Test with valid data."""
    data = {
        "version": "2.0",
        "secret": "secret",
        "type": "DevicesSeen",
        "data": {
            "observations": [
                {
                    "location": {
                        "lat": "51.5355157",
                        "lng": "21.0699035",
                        "unc": "46.3610585",
                    },
                    "seenTime": "2016-09-12T16:23:13Z",
                    "ssid": "ssid",
                    "os": "HA",
                    "ipv6": "2607:f0d0:1002:51::4/64",
                    "clientMac": "00:26:ab:b8:a9:a4",
                    "seenEpoch": "147369739",
                    "rssi": "20",
                    "manufacturer": "Seiko Epson",
                },
                {
                    "location": {
                        "lat": "51.5355357",
                        "lng": "21.0699635",
                        "unc": "46.3610585",
                    },
                    "seenTime": "2016-09-12T16:21:13Z",
                    "ssid": "ssid",
                    "os": "HA",
                    "ipv4": "192.168.0.1",
                    "clientMac": "00:26:ab:b8:a9:a5",
                    "seenEpoch": "147369750",
                    "rssi": "20",
                    "manufacturer": "Seiko Epson",
                },
            ]
        },
    }
    req = await meraki_client.post(URL, data=json.dumps(data))
    expect(req.status).to_equal(HTTPStatus.OK)
    await hass.async_block_till_done()
    state_name = hass.states.get("device_tracker.00_26_ab_b8_a9_a4").state
    expect(state_name).to_equal("home")

    state_name = hass.states.get("device_tracker.00_26_ab_b8_a9_a5").state
    expect(state_name).to_equal("home")


_ = (legacy,)  # keep import to match original
