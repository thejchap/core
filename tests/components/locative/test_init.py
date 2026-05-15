"""The tests the for Locative device tracker platform."""

from collections.abc import Generator
from http import HTTPStatus
from unittest.mock import patch

from aiohttp.test_utils import TestClient
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components import locative
from homeassistant.components.device_tracker import DOMAIN as DEVICE_TRACKER_DOMAIN
from homeassistant.components.device_tracker.legacy import Device
from homeassistant.components.locative import DOMAIN, TRACKER_UPDATE
from homeassistant.core import HomeAssistant
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.dispatcher import DATA_DISPATCHER
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
async def locative_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> TestClient:
    """Locative mock client."""
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()

    with patch("homeassistant.components.device_tracker.legacy.update_config"):
        return await hass_client()


@fixture
async def webhook_id(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: TestClient = Depends(locative_client),
) -> str:
    """Initialize the Locative component and get the webhook_id."""
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://example.local:8123"},
    )
    result = await hass.config_entries.flow.async_init(
        "locative", context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM, result

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    return result["result"].data["webhook_id"]


@test
async def missing_data(
    _trigger: None = Depends(_trigger_executor),
    locative_client: TestClient = Depends(locative_client),
    webhook_id: str = Depends(webhook_id),
) -> None:
    """Test missing data."""
    url = f"/api/webhook/{webhook_id}"

    data = {
        "latitude": 1.0,
        "longitude": 1.1,
        "device": "123",
        "id": "Home",
        "trigger": "enter",
    }

    # No data
    req = await locative_client.post(url)
    expect(req.status).to_equal(HTTPStatus.UNPROCESSABLE_ENTITY)

    # No latitude
    copy = data.copy()
    del copy["latitude"]
    req = await locative_client.post(url, data=copy)
    expect(req.status).to_equal(HTTPStatus.UNPROCESSABLE_ENTITY)

    # No device
    copy = data.copy()
    del copy["device"]
    req = await locative_client.post(url, data=copy)
    expect(req.status).to_equal(HTTPStatus.UNPROCESSABLE_ENTITY)

    # No location
    copy = data.copy()
    del copy["id"]
    req = await locative_client.post(url, data=copy)
    expect(req.status).to_equal(HTTPStatus.UNPROCESSABLE_ENTITY)

    # No trigger
    copy = data.copy()
    del copy["trigger"]
    req = await locative_client.post(url, data=copy)
    expect(req.status).to_equal(HTTPStatus.UNPROCESSABLE_ENTITY)

    # Test message
    copy = data.copy()
    copy["trigger"] = "test"
    req = await locative_client.post(url, data=copy)
    expect(req.status).to_equal(HTTPStatus.OK)

    # Test message, no location
    copy = data.copy()
    copy["trigger"] = "test"
    del copy["id"]
    req = await locative_client.post(url, data=copy)
    expect(req.status).to_equal(HTTPStatus.OK)

    # Unknown trigger
    copy = data.copy()
    copy["trigger"] = "foobar"
    req = await locative_client.post(url, data=copy)
    expect(req.status).to_equal(HTTPStatus.UNPROCESSABLE_ENTITY)


@test
async def enter_and_exit(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    locative_client: TestClient = Depends(locative_client),
    webhook_id: str = Depends(webhook_id),
) -> None:
    """Test when there is a known zone."""
    url = f"/api/webhook/{webhook_id}"

    data = {
        "latitude": 40.7855,
        "longitude": -111.7367,
        "device": "123",
        "id": "Home",
        "trigger": "enter",
    }

    # Enter the Home
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}").state
    expect(state_name).to_equal("home")

    data["id"] = "HOME"
    data["trigger"] = "exit"

    # Exit Home
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}").state
    expect(state_name).to_equal("not_home")

    data["id"] = "hOmE"
    data["trigger"] = "enter"

    # Enter Home again
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}").state
    expect(state_name).to_equal("home")

    data["trigger"] = "exit"

    # Exit Home
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}").state
    expect(state_name).to_equal("not_home")

    data["id"] = "work"
    data["trigger"] = "enter"

    # Enter Work
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}").state
    expect(state_name).to_equal("work")


@test
async def exit_after_enter(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    locative_client: TestClient = Depends(locative_client),
    webhook_id: str = Depends(webhook_id),
) -> None:
    """Test when an exit message comes after an enter message."""
    url = f"/api/webhook/{webhook_id}"

    data = {
        "latitude": 40.7855,
        "longitude": -111.7367,
        "device": "123",
        "id": "Home",
        "trigger": "enter",
    }

    # Enter Home
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)

    state = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}")
    expect(state.state).to_equal("home")

    data["id"] = "Work"

    # Enter Work
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)

    state = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}")
    expect(state.state).to_equal("work")

    data["id"] = "Home"
    data["trigger"] = "exit"

    # Exit Home
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)

    state = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}")
    expect(state.state).to_equal("work")


@test
async def exit_first(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    locative_client: TestClient = Depends(locative_client),
    webhook_id: str = Depends(webhook_id),
) -> None:
    """Test when an exit message is sent first on a new device."""
    url = f"/api/webhook/{webhook_id}"

    data = {
        "latitude": 40.7855,
        "longitude": -111.7367,
        "device": "new_device",
        "id": "Home",
        "trigger": "exit",
    }

    # Exit Home
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)

    state = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}")
    expect(state.state).to_equal("not_home")


@test
async def two_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    locative_client: TestClient = Depends(locative_client),
    webhook_id: str = Depends(webhook_id),
) -> None:
    """Test updating two different devices."""
    url = f"/api/webhook/{webhook_id}"

    data_device_1 = {
        "latitude": 40.7855,
        "longitude": -111.7367,
        "device": "device_1",
        "id": "Home",
        "trigger": "exit",
    }

    # Exit Home
    req = await locative_client.post(url, data=data_device_1)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)

    state = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data_device_1['device']}")
    expect(state.state).to_equal("not_home")

    # Enter Home
    data_device_2 = dict(data_device_1)
    data_device_2["device"] = "device_2"
    data_device_2["trigger"] = "enter"
    req = await locative_client.post(url, data=data_device_2)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)

    state = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data_device_2['device']}")
    expect(state.state).to_equal("home")
    state = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data_device_1['device']}")
    expect(state.state).to_equal("not_home")


@test.skip("xfail: device_tracker does not support unloading yet")
async def load_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    locative_client: TestClient = Depends(locative_client),
    webhook_id: str = Depends(webhook_id),
) -> None:
    """Test that the appropriate dispatch signals are added and removed."""
    url = f"/api/webhook/{webhook_id}"

    data = {
        "latitude": 40.7855,
        "longitude": -111.7367,
        "device": "new_device",
        "id": "Home",
        "trigger": "exit",
    }

    # Exit Home
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)

    state = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}")
    expect(state.state).to_equal("not_home")
    expect(len(hass.data[DATA_DISPATCHER][TRACKER_UPDATE])).to_equal(1)

    entry = hass.config_entries.async_entries(DOMAIN)[0]

    await locative.async_unload_entry(hass, entry)
    await hass.async_block_till_done()
    expect(bool(hass.data[DATA_DISPATCHER][TRACKER_UPDATE])).to_be(False)
