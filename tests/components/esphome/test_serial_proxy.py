"""Tests for the ESPHome serial proxy helper."""

from unittest.mock import AsyncMock, MagicMock, call, patch

from aioesphomeapi import APIClient
from aioesphomeapi.model import SerialProxyInfo, SerialProxyPortType
from serialx.platforms.serial_esphome import InvalidSettingsError
from tryke import Depends, expect, fixture, test
from yarl import URL

from homeassistant.components.esphome import _async_scan_serial_ports, serial_proxy
from homeassistant.components.esphome.const import DOMAIN
from homeassistant.components.usb import SerialDevice
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import (
    MockESPHomeDeviceType,
    load_homeassistant,
    mock_async_zeroconf,
    mock_client,
    mock_esphome_device,
    mock_tts_cache_dir,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    enable_bluetooth as enable_bluetooth_fixture,
    hass as hass_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves before the test body."""
    return hass


@test
def build_url_basic() -> None:
    """Build a URL with a simple port name."""
    url = serial_proxy.build_url("abc123DEF456", "uart0")
    expect(url).to_equal(URL("esphome-hass://esphome/abc123DEF456?port_name=uart0"))


@test
def build_url_escapes_port_name() -> None:
    """Port names with special characters are URL-encoded."""
    url = serial_proxy.build_url("abc123", "uart 0/main")
    # Round-trip via yarl recovers the original port name
    expect(URL(str(url)).query["port_name"]).to_equal("uart 0/main")


@test
async def async_setup_stores_event_loop(
    hass: HomeAssistant = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth_fixture),
    _zeroconf: MagicMock = Depends(mock_async_zeroconf),
    _tts: None = Depends(mock_tts_cache_dir),
    _homeassistant: None = Depends(load_homeassistant),
) -> None:
    """async_setup registers hass.loop on the serial_proxy module."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    expect(serial_proxy._HASS_LOOP is hass.loop).to_be(True)


@test
async def resolve_client_unknown_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """An unknown entry_id raises InvalidSettingsError."""
    with patch.object(serial_proxy, "async_get_hass", return_value=hass):
        async with expect_raises_async(InvalidSettingsError):
            await serial_proxy._resolve_client("does-not-exist")


@test
async def resolve_client_wrong_domain(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """A config entry from a different domain raises InvalidSettingsError."""
    entry = MockConfigEntry(domain="other", data={})
    entry.add_to_hass(hass)

    with patch.object(serial_proxy, "async_get_hass", return_value=hass):
        async with expect_raises_async(InvalidSettingsError):
            await serial_proxy._resolve_client(entry.entry_id)


@test
async def resolve_client_unloaded_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """An ESPHome entry that isn't loaded raises InvalidSettingsError."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    with patch.object(serial_proxy, "async_get_hass", return_value=hass):
        async with expect_raises_async(InvalidSettingsError):
            await serial_proxy._resolve_client(entry.entry_id)


@test
async def resolve_client_loaded_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """A loaded ESPHome entry returns its APIClient."""
    device = await mock_esphome_device(mock_client=mock_client)

    with patch.object(serial_proxy, "async_get_hass", return_value=hass):
        client = await serial_proxy._resolve_client(device.entry.entry_id)

    expect(client is mock_client).to_be(True)


@test
async def scan_serial_ports_no_entries(
    hass: HomeAssistant = Depends(_trigger_executor),
    _zeroconf: MagicMock = Depends(mock_async_zeroconf),
) -> None:
    """No loaded ESPHome entries yields no ports."""
    expect(_async_scan_serial_ports(hass)).to_equal([])


@test
async def scan_serial_ports_happy_path(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """A loaded entry with serial proxies emits a SerialDevice per proxy."""
    device = await mock_esphome_device(
        mock_client=mock_client,
        device_info={
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "manufacturer": "Espressif",
            "model": "ESP32",
            "serial_proxies": [
                SerialProxyInfo(name="Left Port", port_type=SerialProxyPortType.TTL),
                SerialProxyInfo(name="Right Port", port_type=SerialProxyPortType.TTL),
            ],
        },
    )

    ports = _async_scan_serial_ports(hass)

    entry_id = device.entry.entry_id
    expect(ports).to_equal(
        [
            SerialDevice(
                device=str(serial_proxy.build_url(entry_id, "Left Port")),
                serial_number="AABBCCDDEEFF-left_port",
                manufacturer="Espressif",
                description="ESP32 (Left Port)",
            ),
            SerialDevice(
                device=str(serial_proxy.build_url(entry_id, "Right Port")),
                serial_number="AABBCCDDEEFF-right_port",
                manufacturer="Espressif",
                description="ESP32 (Right Port)",
            ),
        ]
    )


@test
async def scan_serial_ports_skips_unavailable(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Unavailable entries are skipped by the scanner."""
    device = await mock_esphome_device(
        mock_client=mock_client,
        device_info={
            "serial_proxies": [
                SerialProxyInfo(name="uart0", port_type=SerialProxyPortType.TTL)
            ],
        },
    )
    # Mark the entry as unavailable
    device.entry.runtime_data.available = False

    expect(_async_scan_serial_ports(hass)).to_equal([])


@test
async def async_open_missing_host(
    hass: HomeAssistant = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth_fixture),
    _zeroconf: MagicMock = Depends(mock_async_zeroconf),
    _tts: None = Depends(mock_tts_cache_dir),
    _homeassistant: None = Depends(load_homeassistant),
) -> None:
    """A URL with an invalid entry_id raises InvalidSettingsError."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    proxy = serial_proxy.HassESPHomeSerial("esphome-hass://unknown/?port_name=uart0")

    async with expect_raises_async(InvalidSettingsError):
        await proxy._async_open()


@test
async def async_open_missing_port_name(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """A URL with a missing port name raises InvalidSettingsError."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)

    device = await mock_esphome_device(
        mock_client=mock_client,
        device_info={
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "manufacturer": "Espressif",
            "model": "ESP32",
            "serial_proxies": [
                SerialProxyInfo(name="uart0", port_type=SerialProxyPortType.TTL),
            ],
        },
    )

    entry_id = device.entry.entry_id
    proxy = serial_proxy.HassESPHomeSerial(f"esphome-hass://{entry_id}")

    async with expect_raises_async(InvalidSettingsError):
        await proxy._async_open()


@test
async def async_open_happy_path(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Happy path sets _api from the loaded entry and applies port_name from query."""
    device = await mock_esphome_device(mock_client=mock_client)
    mock_client._loop = hass.loop

    url = str(serial_proxy.build_url(device.entry.entry_id, "uart0"))
    proxy = serial_proxy.HassESPHomeSerial(url)

    with patch(
        "homeassistant.components.esphome.serial_proxy.ESPHomeSerial._async_open",
        AsyncMock(),
    ) as mock_super_open:
        await proxy._async_open()

    expect(proxy._api is mock_client).to_be(True)
    expect(proxy._port_name).to_equal("uart0")
    expect(proxy._client_loop is hass.loop).to_be(True)
    expect(mock_super_open.mock_calls).to_equal([call()])
