"""Tryke fixtures for Ring integration tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from itertools import chain
from unittest.mock import AsyncMock, Mock, create_autospec, patch

import ring_doorbell
from tryke import Depends, fixture

from homeassistant.components.ring import DOMAIN
from homeassistant.components.ring.const import CONF_CONFIG_ENTRY_MINOR_VERSION
from homeassistant.const import CONF_DEVICE_ID, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .device_mocks import get_devices_data, get_mock_devices

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

MOCK_HARDWARE_ID = "foo-bar"


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.ring.async_setup_entry", return_value=True
    ) as m:
        yield m


@fixture
def mock_ring_auth() -> Generator[Mock]:
    """Mock ring_doorbell.Auth."""
    with patch(
        "homeassistant.components.ring.config_flow.Auth", autospec=True
    ) as mock_ring_auth:
        mock_ring_auth.return_value.async_fetch_token.return_value = {
            "access_token": "mock-token"
        }
        yield mock_ring_auth.return_value


@fixture
def mock_ring_devices() -> object:
    """Mock Ring devices."""
    devices = get_mock_devices()
    device_list = list(chain.from_iterable(devices.values()))

    def filter_devices(
        device_api_ai: int, device_family: set | None = None
    ) -> object:
        return next(
            iter(
                [
                    device
                    for device in device_list
                    if device.id == device_api_ai
                    and (not device_family or device.family in device_family)
                ]
            )
        )

    class FakeRingDevices:
        all_devices = device_list
        video_devices = (
            devices["stickup_cams"]
            + devices["doorbots"]
            + devices["authorized_doorbots"]
        )
        stickup_cams = devices["stickup_cams"]
        other = devices["other"]
        chimes = devices["chimes"]

        def get_device(self, id: int) -> object:
            return filter_devices(id)

        def get_video_device(self, id: int) -> object:
            return filter_devices(
                id, {"stickup_cams", "doorbots", "authorized_doorbots"}
            )

        def get_stickup_cam(self, id: int) -> object:
            return filter_devices(id, {"stickup_cams"})

        def get_other(self, id: int) -> object:
            return filter_devices(id, {"other"})

    return FakeRingDevices()


@fixture
def mock_ring_client(
    _auth: Mock = Depends(mock_ring_auth),
    devices: object = Depends(mock_ring_devices),
) -> Generator[Mock]:
    """Mock ring client api."""
    mock_client = create_autospec(ring_doorbell.Ring)
    mock_client.return_value.devices_data = get_devices_data()
    mock_client.return_value.devices.return_value = devices
    mock_client.return_value.active_alerts.return_value = []

    with patch("homeassistant.components.ring.Ring", new=mock_client):
        yield mock_client.return_value


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock ConfigEntry."""
    return MockConfigEntry(
        title="Ring",
        domain=DOMAIN,
        data={
            CONF_DEVICE_ID: MOCK_HARDWARE_ID,
            CONF_USERNAME: "foo@bar.com",
            "token": {"access_token": "mock-token"},
        },
        unique_id="foo@bar.com",
        version=1,
        minor_version=CONF_CONFIG_ENTRY_MINOR_VERSION,
    )


@fixture
def mock_ring_event_listener_class() -> Generator[Mock]:
    """Fixture to mock the ring event listener."""
    with patch(
        "homeassistant.components.ring.coordinator.RingEventListener", autospec=True
    ) as mock_ring_listener:
        mock_ring_listener.return_value.started = True
        yield mock_ring_listener


@fixture
async def mock_added_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _auth: Mock = Depends(mock_ring_auth),
    _client: Mock = Depends(mock_ring_client),
    _listener: Mock = Depends(mock_ring_event_listener_class),
) -> AsyncGenerator[MockConfigEntry]:
    """Mock ConfigEntry that's been added to HA."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    yield entry
