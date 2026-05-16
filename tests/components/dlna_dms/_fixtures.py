"""Tryke fixtures for the DLNA DMS component."""

from collections.abc import AsyncGenerator, AsyncIterable, Generator
from typing import Final, cast
from unittest.mock import AsyncMock, MagicMock, Mock, create_autospec, patch, seal

from async_upnp_client.client import UpnpDevice, UpnpService
from async_upnp_client.exceptions import UpnpConnectionError
from async_upnp_client.utils import absolute_url
from didl_lite import didl_lite
from tryke import Depends, fixture

from homeassistant.components.dlna_dms.const import (
    CONF_SOURCE_ID,
    CONFIG_VERSION,
    DOMAIN,
)
from homeassistant.components.dlna_dms.dms import DlnaDmsData
from homeassistant.const import CONF_DEVICE_ID, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

DUMMY_OBJECT_ID: Final = "123"

MOCK_DEVICE_HOST: Final = "192.88.99.21"
MOCK_DEVICE_BASE_URL: Final = f"http://{MOCK_DEVICE_HOST}"
MOCK_DEVICE_LOCATION: Final = MOCK_DEVICE_BASE_URL + "/dms_description.xml"
MOCK_DEVICE_NAME: Final = "Test Server Device"
MOCK_DEVICE_TYPE: Final = "urn:schemas-upnp-org:device:MediaServer:1"
MOCK_DEVICE_UDN: Final = "uuid:7bf34520-f034-4fa2-8d2d-2f709d4221ef"
MOCK_DEVICE_USN: Final = f"{MOCK_DEVICE_UDN}::{MOCK_DEVICE_TYPE}"
MOCK_SOURCE_ID: Final = "test_server_device"

LOCAL_IP: Final = "192.88.99.1"
EVENT_CALLBACK_URL: Final = "http://192.88.99.1/notify"

NEW_DEVICE_LOCATION: Final = "http://192.88.99.7" + "/dmr_description.xml"


@fixture
async def setup_media_source(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up media source."""
    assert await async_setup_component(hass, "media_source", {})


@fixture
def aiohttp_session_requester_mock() -> Generator[Mock]:
    """Mock the AiohttpSessionRequester to prevent network use."""
    with patch(
        "homeassistant.components.dlna_dms.dms.AiohttpSessionRequester", autospec=True
    ) as requester_mock:
        requester_mock.return_value = mock = AsyncMock()
        mock.async_http_request.return_value.body = MagicMock()
        yield requester_mock


@fixture
def upnp_factory_mock() -> Generator[Mock]:
    """Mock the UpnpFactory class to construct DMS-style UPnP devices."""
    with patch(
        "homeassistant.components.dlna_dms.dms.UpnpFactory",
        autospec=True,
        spec_set=True,
    ) as upnp_factory:
        upnp_device = create_autospec(UpnpDevice, instance=True)
        upnp_device.name = MOCK_DEVICE_NAME
        upnp_device.udn = MOCK_DEVICE_UDN
        upnp_device.device_url = MOCK_DEVICE_LOCATION
        upnp_device.device_type = MOCK_DEVICE_TYPE
        upnp_device.available = True
        upnp_device.parent_device = None
        upnp_device.root_device = upnp_device
        upnp_device.all_devices = [upnp_device]
        upnp_device.services = {
            "urn:schemas-upnp-org:service:ContentDirectory:1": create_autospec(
                UpnpService,
                instance=True,
                service_type="urn:schemas-upnp-org:service:ContentDirectory:1",
                service_id="urn:upnp-org:serviceId:ContentDirectory",
            ),
            "urn:schemas-upnp-org:service:ConnectionManager:1": create_autospec(
                UpnpService,
                instance=True,
                service_type="urn:schemas-upnp-org:service:ConnectionManager:1",
                service_id="urn:upnp-org:serviceId:ConnectionManager",
            ),
        }
        seal(upnp_device)
        upnp_factory_instance = upnp_factory.return_value
        upnp_factory_instance.async_create_device.return_value = upnp_device

        yield upnp_factory_instance


@fixture
def config_entry_mock() -> MockConfigEntry:
    """Mock a config entry for this platform."""
    return MockConfigEntry(
        unique_id=MOCK_DEVICE_USN,
        domain=DOMAIN,
        version=CONFIG_VERSION,
        data={
            CONF_URL: MOCK_DEVICE_LOCATION,
            CONF_DEVICE_ID: MOCK_DEVICE_USN,
            CONF_SOURCE_ID: MOCK_SOURCE_ID,
        },
        title=MOCK_DEVICE_NAME,
    )


@fixture
def dms_device_mock(
    upnp_factory_mock: Mock = Depends(upnp_factory_mock),
) -> Generator[Mock]:
    """Mock the async_upnp_client DMS device, initially connected."""
    with patch(
        "homeassistant.components.dlna_dms.dms.DmsDevice", autospec=True
    ) as constructor:
        device = constructor.return_value
        device.on_event = None
        device.profile_device = upnp_factory_mock.async_create_device.return_value
        device.icon = MOCK_DEVICE_BASE_URL + "/icon.jpg"
        device.udn = "device_udn"
        device.manufacturer = "device_manufacturer"
        device.model_name = "device_model_name"
        device.name = "device_name"
        device.get_absolute_url.side_effect = lambda url: absolute_url(
            MOCK_DEVICE_BASE_URL, url
        )

        yield device


@fixture
def ssdp_scanner_mock() -> Generator[Mock]:
    """Mock the SSDP Scanner."""
    with patch("homeassistant.components.ssdp.Scanner", autospec=True) as mock_scanner:
        reg_callback = mock_scanner.return_value.async_register_callback
        reg_callback.return_value = Mock(return_value=None)
        yield mock_scanner.return_value


@fixture
def ssdp_server_mock() -> Generator[None]:
    """Mock the SSDP Server."""
    with patch("homeassistant.components.ssdp.Server", autospec=True):
        yield


@fixture
async def device_source_mock(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry_mock: MockConfigEntry = Depends(config_entry_mock),
    ssdp_scanner_mock: Mock = Depends(ssdp_scanner_mock),
    dms_device_mock: Mock = Depends(dms_device_mock),
) -> AsyncGenerator[None]:
    """Fixture to set up a DmsDeviceSource and cleanup at completion."""
    config_entry_mock.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry_mock.entry_id)
    await hass.async_block_till_done()

    assert len(config_entry_mock.update_listeners) == 0
    assert ssdp_scanner_mock.async_register_callback.await_count == 2
    assert ssdp_scanner_mock.async_register_callback.return_value.call_count == 0

    yield None

    assert await hass.config_entries.async_remove(config_entry_mock.entry_id) == {
        "require_restart": False
    }

    assert not config_entry_mock.update_listeners
    assert (
        ssdp_scanner_mock.async_register_callback.await_count
        == ssdp_scanner_mock.async_register_callback.return_value.call_count
    )

    domain_data = cast(DlnaDmsData, hass.data[DOMAIN])
    assert MOCK_DEVICE_USN not in domain_data.devices
    assert MOCK_SOURCE_ID not in domain_data.sources


@fixture
async def connected_source_mock(
    dms_device_mock: Mock = Depends(dms_device_mock),
    _device_source_mock: None = Depends(device_source_mock),
) -> None:
    """Fixture to set up a mock DmsDeviceSource in a connected state."""
    didl_item = didl_lite.Item(
        id=DUMMY_OBJECT_ID,
        restricted=False,
        title="Object",
        res=[didl_lite.Resource(uri="foo/bar", protocol_info="http-get:*:audio/mpeg:")],
    )
    dms_device_mock.async_browse_metadata.return_value = didl_item


@fixture
async def disconnected_source_mock(
    hass: HomeAssistant = Depends(hass_fixture),
    upnp_factory_mock: Mock = Depends(upnp_factory_mock),
    config_entry_mock: MockConfigEntry = Depends(config_entry_mock),
    ssdp_scanner_mock: Mock = Depends(ssdp_scanner_mock),
    dms_device_mock: Mock = Depends(dms_device_mock),
    _setup_media_source: None = Depends(setup_media_source),
) -> AsyncIterable[None]:
    """Fixture to set up a mock DmsDeviceSource in a disconnected state."""
    upnp_factory_mock.async_create_device.side_effect = UpnpConnectionError

    config_entry_mock.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry_mock.entry_id)
    await hass.async_block_till_done()

    assert len(config_entry_mock.update_listeners) == 0
    assert ssdp_scanner_mock.async_register_callback.await_count == 2
    assert ssdp_scanner_mock.async_register_callback.return_value.call_count == 0

    didl_item = didl_lite.Item(
        id=DUMMY_OBJECT_ID,
        restricted=False,
        title="Object",
        res=[didl_lite.Resource(uri="foo/bar", protocol_info="http-get:*:audio/mpeg:")],
    )
    dms_device_mock.async_browse_metadata.return_value = didl_item

    yield

    assert await hass.config_entries.async_remove(config_entry_mock.entry_id) == {
        "require_restart": False
    }

    assert not config_entry_mock.update_listeners
    assert (
        ssdp_scanner_mock.async_register_callback.await_count
        == ssdp_scanner_mock.async_register_callback.return_value.call_count
    )
