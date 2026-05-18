"""Test how the DmsDeviceSource handles available and unavailable devices."""

import asyncio
from collections.abc import AsyncIterable
import logging
from typing import Final
from unittest.mock import ANY, DEFAULT, Mock

from async_upnp_client.exceptions import UpnpConnectionError, UpnpError
from didl_lite import didl_lite
from tryke import Depends, expect, fixture, test

from homeassistant.components import media_source, ssdp
from homeassistant.components.dlna_dms.const import DOMAIN
from homeassistant.components.dlna_dms.dms import get_domain_data
from homeassistant.components.media_player import BrowseError
from homeassistant.components.media_source import Unresolvable
from homeassistant.core import HomeAssistant
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo

from ._fixtures import (
    MOCK_DEVICE_LOCATION,
    MOCK_DEVICE_TYPE,
    MOCK_DEVICE_UDN,
    MOCK_DEVICE_USN,
    MOCK_SOURCE_ID,
    NEW_DEVICE_LOCATION,
    connected_source_mock,
    disconnected_source_mock,
    dms_device_mock,
    setup_media_source,
    ssdp_scanner_mock,
    ssdp_server_mock,
    upnp_factory_mock,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async

DUMMY_OBJECT_ID: Final = "123"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


async def assert_source_available(hass: HomeAssistant) -> None:
    """Assert that the DmsDeviceSource under test can be used."""
    assert await media_source.async_browse_media(
        hass, f"media-source://{DOMAIN}/{MOCK_SOURCE_ID}/:{DUMMY_OBJECT_ID}"
    )


async def assert_source_unavailable(hass: HomeAssistant) -> None:
    """Assert that the DmsDeviceSource under test cannot be used."""
    async with expect_raises_async(Unresolvable, match="DMS is not connected"):
        await media_source.async_browse_media(
            hass, f"media-source://{DOMAIN}/{MOCK_SOURCE_ID}/:{DUMMY_OBJECT_ID}"
        )


@test
async def unavailable_device(
    hass: HomeAssistant = Depends(hass_fixture),
    upnp_factory_mock: Mock = Depends(upnp_factory_mock),
    ssdp_scanner_mock: Mock = Depends(ssdp_scanner_mock),
    _ssdp_server_mock: None = Depends(ssdp_server_mock),
    _disconnected_source_mock: AsyncIterable[None] = Depends(disconnected_source_mock),
) -> None:
    """Test a DlnaDmsEntity with out a connected DmsDevice."""
    upnp_factory_mock.async_create_device.assert_awaited_once_with(MOCK_DEVICE_LOCATION)
    ssdp_scanner_mock.async_register_callback.assert_any_call(
        ANY, {"USN": MOCK_DEVICE_USN}
    )
    ssdp_scanner_mock.async_register_callback.assert_any_call(
        ANY, {"_udn": MOCK_DEVICE_UDN, "NTS": "ssdp:byebye"}
    )
    await assert_source_unavailable(hass)

    async with expect_raises_async(BrowseError, match="DMS is not connected"):
        await media_source.async_browse_media(
            hass, f"media-source://{DOMAIN}/{MOCK_SOURCE_ID}//browse_path"
        )
    async with expect_raises_async(BrowseError, match="DMS is not connected"):
        await media_source.async_browse_media(
            hass, f"media-source://{DOMAIN}/{MOCK_SOURCE_ID}/:browse_object"
        )
    async with expect_raises_async(BrowseError, match="DMS is not connected"):
        await media_source.async_browse_media(
            hass, f"media-source://{DOMAIN}/{MOCK_SOURCE_ID}/?browse_search"
        )
    async with expect_raises_async(Unresolvable, match="DMS is not connected"):
        await media_source.async_resolve_media(
            hass, f"media-source://{DOMAIN}/{MOCK_SOURCE_ID}//resolve_path", None
        )
    async with expect_raises_async(Unresolvable, match="DMS is not connected"):
        await media_source.async_resolve_media(
            hass, f"media-source://{DOMAIN}/{MOCK_SOURCE_ID}/:resolve_object", None
        )
    async with expect_raises_async(Unresolvable):
        await media_source.async_resolve_media(
            hass, f"media-source://{DOMAIN}/{MOCK_SOURCE_ID}/?resolve_search", None
        )


@test
async def become_available(
    hass: HomeAssistant = Depends(hass_fixture),
    upnp_factory_mock: Mock = Depends(upnp_factory_mock),
    ssdp_scanner_mock: Mock = Depends(ssdp_scanner_mock),
    _ssdp_server_mock: None = Depends(ssdp_server_mock),
    _disconnected_source_mock: AsyncIterable[None] = Depends(disconnected_source_mock),
) -> None:
    """Test a device becoming available after the entity is constructed."""
    upnp_factory_mock.async_create_device.side_effect = None
    upnp_factory_mock.async_create_device.reset_mock()

    ssdp_callback = ssdp_scanner_mock.async_register_callback.call_args.args[0].target
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=NEW_DEVICE_LOCATION,
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    upnp_factory_mock.async_create_device.assert_awaited_once_with(NEW_DEVICE_LOCATION)
    await assert_source_available(hass)


@test
async def alive_but_gone(
    hass: HomeAssistant = Depends(hass_fixture),
    upnp_factory_mock: Mock = Depends(upnp_factory_mock),
    ssdp_scanner_mock: Mock = Depends(ssdp_scanner_mock),
    _ssdp_server_mock: None = Depends(ssdp_server_mock),
    _disconnected_source_mock: AsyncIterable[None] = Depends(disconnected_source_mock),
) -> None:
    """Test a device sending an SSDP alive announcement, but not being connectable."""
    upnp_factory_mock.async_create_device.side_effect = UpnpError

    ssdp_callback = ssdp_scanner_mock.async_register_callback.call_args.args[0].target
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=NEW_DEVICE_LOCATION,
            ssdp_st=MOCK_DEVICE_TYPE,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "1"},
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    upnp_factory_mock.async_create_device.assert_awaited()

    await assert_source_unavailable(hass)

    upnp_factory_mock.async_create_device.reset_mock()
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=NEW_DEVICE_LOCATION,
            ssdp_st=MOCK_DEVICE_TYPE,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "1"},
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()
    upnp_factory_mock.async_create_device.assert_not_called()
    upnp_factory_mock.async_create_device.assert_not_awaited()
    await assert_source_unavailable(hass)

    upnp_factory_mock.async_create_device.reset_mock()
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=NEW_DEVICE_LOCATION,
            ssdp_st=MOCK_DEVICE_TYPE,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "2"},
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    upnp_factory_mock.async_create_device.assert_awaited()
    await assert_source_unavailable(hass)

    upnp_factory_mock.async_create_device.reset_mock()
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.BYEBYE,
    )
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=NEW_DEVICE_LOCATION,
            ssdp_st=MOCK_DEVICE_TYPE,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "2"},
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    upnp_factory_mock.async_create_device.assert_awaited()
    await assert_source_unavailable(hass)


@test
async def multiple_ssdp_alive(
    hass: HomeAssistant = Depends(hass_fixture),
    upnp_factory_mock: Mock = Depends(upnp_factory_mock),
    ssdp_scanner_mock: Mock = Depends(ssdp_scanner_mock),
    _ssdp_server_mock: None = Depends(ssdp_server_mock),
    _disconnected_source_mock: AsyncIterable[None] = Depends(disconnected_source_mock),
) -> None:
    """Test multiple SSDP alive notifications is ok, only connects to device once."""
    upnp_factory_mock.async_create_device.reset_mock()

    async def create_device_delayed(_location):
        """Delay before continuing with async_create_device."""
        await asyncio.sleep(0.1)
        return DEFAULT

    upnp_factory_mock.async_create_device.side_effect = create_device_delayed

    ssdp_callback = ssdp_scanner_mock.async_register_callback.call_args.args[0].target
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=NEW_DEVICE_LOCATION,
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=NEW_DEVICE_LOCATION,
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    upnp_factory_mock.async_create_device.assert_awaited_once_with(NEW_DEVICE_LOCATION)

    await assert_source_available(hass)


@test
async def ssdp_byebye(
    hass: HomeAssistant = Depends(hass_fixture),
    ssdp_scanner_mock: Mock = Depends(ssdp_scanner_mock),
    _ssdp_server_mock: None = Depends(ssdp_server_mock),
    _setup_media_source: None = Depends(setup_media_source),
    _connected_source_mock: None = Depends(connected_source_mock),
) -> None:
    """Test device is disconnected when byebye is received."""
    ssdp_callback = ssdp_scanner_mock.async_register_callback.call_args.args[0].target
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_udn=MOCK_DEVICE_UDN,
            ssdp_headers={"NTS": "ssdp:byebye"},
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.BYEBYE,
    )

    await assert_source_unavailable(hass)

    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_udn=MOCK_DEVICE_UDN,
            ssdp_headers={"NTS": "ssdp:byebye"},
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.BYEBYE,
    )


@test
async def ssdp_update_seen_bootid(
    hass: HomeAssistant = Depends(hass_fixture),
    ssdp_scanner_mock: Mock = Depends(ssdp_scanner_mock),
    upnp_factory_mock: Mock = Depends(upnp_factory_mock),
    _ssdp_server_mock: None = Depends(ssdp_server_mock),
    _disconnected_source_mock: AsyncIterable[None] = Depends(disconnected_source_mock),
) -> None:
    """Test device does not reconnect when it gets ssdp:update with next bootid."""
    await assert_source_unavailable(hass)

    upnp_factory_mock.async_create_device.reset_mock()
    upnp_factory_mock.async_create_device.side_effect = None

    ssdp_callback = ssdp_scanner_mock.async_register_callback.call_args.args[0].target
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=MOCK_DEVICE_LOCATION,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "1"},
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    await assert_source_available(hass)
    expect(upnp_factory_mock.async_create_device.await_count).to_equal(1)

    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_udn=MOCK_DEVICE_UDN,
            ssdp_headers={
                "NTS": "ssdp:update",
                ssdp.ATTR_SSDP_BOOTID: "1",
                ssdp.ATTR_SSDP_NEXTBOOTID: "2",
            },
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.UPDATE,
    )
    await hass.async_block_till_done()

    await assert_source_available(hass)
    expect(upnp_factory_mock.async_create_device.await_count).to_equal(1)

    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_udn=MOCK_DEVICE_UDN,
            ssdp_headers={
                "NTS": "ssdp:update",
                ssdp.ATTR_SSDP_BOOTID: "1",
                ssdp.ATTR_SSDP_NEXTBOOTID: "2",
            },
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.UPDATE,
    )
    await hass.async_block_till_done()

    await assert_source_available(hass)
    expect(upnp_factory_mock.async_create_device.await_count).to_equal(1)

    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_udn=MOCK_DEVICE_UDN,
            ssdp_headers={
                "NTS": "ssdp:update",
                ssdp.ATTR_SSDP_BOOTID: "2",
                ssdp.ATTR_SSDP_NEXTBOOTID: "7c848375-a106-4bd1-ac3c-8e50427c8e4f",
            },
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.UPDATE,
    )
    await hass.async_block_till_done()

    await assert_source_available(hass)
    expect(upnp_factory_mock.async_create_device.await_count).to_equal(1)

    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=MOCK_DEVICE_LOCATION,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "2"},
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    await assert_source_available(hass)
    expect(upnp_factory_mock.async_create_device.await_count).to_equal(1)


@test
async def ssdp_update_missed_bootid(
    hass: HomeAssistant = Depends(hass_fixture),
    ssdp_scanner_mock: Mock = Depends(ssdp_scanner_mock),
    upnp_factory_mock: Mock = Depends(upnp_factory_mock),
    _ssdp_server_mock: None = Depends(ssdp_server_mock),
    _disconnected_source_mock: AsyncIterable[None] = Depends(disconnected_source_mock),
) -> None:
    """Test device disconnects when it gets ssdp:update bootid it wasn't expecting."""
    await assert_source_unavailable(hass)

    upnp_factory_mock.async_create_device.reset_mock()
    upnp_factory_mock.async_create_device.side_effect = None

    ssdp_callback = ssdp_scanner_mock.async_register_callback.call_args.args[0].target
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=MOCK_DEVICE_LOCATION,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "1"},
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    await assert_source_available(hass)
    expect(upnp_factory_mock.async_create_device.await_count).to_equal(1)

    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_udn=MOCK_DEVICE_UDN,
            ssdp_headers={
                "NTS": "ssdp:update",
                ssdp.ATTR_SSDP_BOOTID: "2",
                ssdp.ATTR_SSDP_NEXTBOOTID: "3",
            },
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.UPDATE,
    )
    await hass.async_block_till_done()

    await assert_source_available(hass)
    expect(upnp_factory_mock.async_create_device.await_count).to_equal(1)

    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=MOCK_DEVICE_LOCATION,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "3"},
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    await assert_source_available(hass)
    expect(upnp_factory_mock.async_create_device.await_count).to_equal(2)


@test
async def ssdp_bootid(
    hass: HomeAssistant = Depends(hass_fixture),
    upnp_factory_mock: Mock = Depends(upnp_factory_mock),
    ssdp_scanner_mock: Mock = Depends(ssdp_scanner_mock),
    _ssdp_server_mock: None = Depends(ssdp_server_mock),
    _disconnected_source_mock: AsyncIterable[None] = Depends(disconnected_source_mock),
) -> None:
    """Test an alive with a new BOOTID.UPNP.ORG header causes a reconnect."""
    await assert_source_unavailable(hass)

    upnp_factory_mock.async_create_device.side_effect = None
    upnp_factory_mock.async_create_device.reset_mock()

    ssdp_callback = ssdp_scanner_mock.async_register_callback.call_args.args[0].target
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=MOCK_DEVICE_LOCATION,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "1"},
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    await assert_source_available(hass)
    expect(upnp_factory_mock.async_create_device.await_count).to_equal(1)

    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=MOCK_DEVICE_LOCATION,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "1"},
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    await assert_source_available(hass)
    expect(upnp_factory_mock.async_create_device.await_count).to_equal(1)

    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=MOCK_DEVICE_LOCATION,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "2"},
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    await assert_source_available(hass)
    expect(upnp_factory_mock.async_create_device.await_count).to_equal(2)


@test
async def repeated_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    upnp_factory_mock: Mock = Depends(upnp_factory_mock),
    _ssdp_server_mock: None = Depends(ssdp_server_mock),
    _setup_media_source: None = Depends(setup_media_source),
    _connected_source_mock: None = Depends(connected_source_mock),
) -> None:
    """Test trying to connect an already connected device is safely ignored."""
    upnp_factory_mock.async_create_device.reset_mock()

    domain_data = get_domain_data(hass)
    device_source = domain_data.sources[MOCK_SOURCE_ID]
    logging.getLogger().setLevel(logging.DEBUG)
    await device_source.device_connect()

    assert not upnp_factory_mock.async_create_device.await_count
    await assert_source_available(hass)


@test
async def become_unavailable(
    hass: HomeAssistant = Depends(hass_fixture),
    dms_device_mock: Mock = Depends(dms_device_mock),
    _ssdp_server_mock: None = Depends(ssdp_server_mock),
    _setup_media_source: None = Depends(setup_media_source),
    _connected_source_mock: None = Depends(connected_source_mock),
) -> None:
    """Test a device becoming unavailable."""
    dms_device_mock.async_browse_metadata.return_value = didl_lite.Item(
        id="object_id",
        restricted=False,
        title="Object",
        res=[didl_lite.Resource(uri="foo", protocol_info="http-get:*:audio/mpeg:")],
    )

    assert await media_source.async_resolve_media(
        hass, f"media-source://{DOMAIN}/{MOCK_SOURCE_ID}/:object_id", None
    )

    dms_device_mock.async_browse_metadata.side_effect = UpnpConnectionError

    async with expect_raises_async(Unresolvable):
        await media_source.async_resolve_media(
            hass, f"media-source://{DOMAIN}/{MOCK_SOURCE_ID}/:object_id", None
        )

    await assert_source_unavailable(hass)
