"""Tryke fixtures for ESPHome tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from aioesphomeapi import APIClient, APIVersion, DeviceInfo, ReconnectLogic
from tryke import Depends, fixture

from homeassistant.components.esphome.const import (
    CONF_DEVICE_NAME,
    CONF_NOISE_PSK,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    enable_bluetooth as enable_bluetooth_fixture,
    hass as hass_fixture,
    tmp_path as tmp_path_fixture,
)


class BaseMockReconnectLogic(ReconnectLogic):
    """Mock ReconnectLogic."""

    def stop_callback(self) -> None:
        """Stop the reconnect logic."""
        self._cancel_connect("forced disconnect from test")
        self._is_stopped = True

    async def stop(self) -> None:
        """Stop the reconnect logic."""
        self.stop_callback()


@fixture
def mock_async_zeroconf() -> Generator[MagicMock]:
    """Mock AsyncZeroconf."""
    from zeroconf import DNSCache, Zeroconf  # noqa: PLC0415
    from zeroconf.asyncio import AsyncZeroconf  # noqa: PLC0415

    with patch(
        "homeassistant.components.zeroconf.HaAsyncZeroconf", spec=AsyncZeroconf
    ) as mock_aiozc:
        zc = mock_aiozc.return_value
        zc.async_unregister_service = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.zeroconf = Mock(spec=Zeroconf)
        zc.zeroconf.async_wait_for_start = AsyncMock()
        zc.zeroconf.cache = DNSCache()
        zc.async_close = AsyncMock()
        yield mock_aiozc


@fixture
def mock_tts_cache_dir(
    tmp_path: Path = Depends(tmp_path_fixture),
) -> Generator[None]:
    """Mock the TTS cache dir."""
    with (
        patch(
            "homeassistant.components.tts._init_tts_cache_dir",
            return_value=str(tmp_path),
        ),
        patch(
            "homeassistant.components.tts._get_cache_files",
            return_value={},
        ),
    ):
        yield


@fixture
async def load_homeassistant(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Load the homeassistant integration."""
    assert await async_setup_component(hass, "homeassistant", {})


@fixture
def mock_device_info() -> DeviceInfo:
    """Return the default mocked device info."""
    return DeviceInfo(
        uses_password=False,
        name="test",
        legacy_bluetooth_proxy_version=0,
        mac_address="11:22:33:44:55:AA",
        esphome_version="1.0.0",
    )


@fixture
def mock_client(
    mock_device_info: DeviceInfo = Depends(mock_device_info),
) -> Generator[APIClient]:
    """Mock APIClient."""
    mock_client = Mock(spec=APIClient)

    def mock_constructor(
        address: str,
        port: int,
        password: str | None,
        *,
        client_info: str = "aioesphomeapi",
        keepalive: float = 15.0,
        zeroconf_instance=None,
        noise_psk: str | None = None,
        expected_name: str | None = None,
        timezone: str | None = None,
    ) -> Mock:
        """Fake the client constructor."""
        mock_client.host = address
        mock_client.port = port
        mock_client.password = password
        mock_client.zeroconf_instance = zeroconf_instance
        mock_client.noise_psk = noise_psk
        mock_client.timezone = timezone
        return mock_client

    mock_client.side_effect = mock_constructor
    mock_client.device_info = AsyncMock(return_value=mock_device_info)
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    mock_client.subscribe_logs = Mock()
    mock_client.list_entities_services = AsyncMock(return_value=([], []))
    mock_client.address = "127.0.0.1"
    mock_client.api_version = APIVersion(99, 99)

    with (
        patch(
            "homeassistant.components.esphome.manager.ReconnectLogic",
            BaseMockReconnectLogic,
        ),
        patch("homeassistant.components.esphome.APIClient", mock_client),
        patch("homeassistant.components.esphome.config_flow.APIClient", mock_client),
    ):
        yield mock_client


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Return the default mocked config entry."""
    config_entry = MockConfigEntry(
        title="ESPHome Device",
        entry_id="08d821dc059cf4f645cb024d32c8e708",
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.2",
            CONF_PORT: 6053,
            CONF_PASSWORD: "pwd",
            CONF_NOISE_PSK: "12345678123456781234567812345678",
            CONF_DEVICE_NAME: "test",
        },
        unique_id="11:22:33:44:55:aa",
    )
    config_entry.add_to_hass(hass)
    return config_entry


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    _bluetooth: None = Depends(enable_bluetooth_fixture),
    _zeroconf: MagicMock = Depends(mock_async_zeroconf),
    _tts: None = Depends(mock_tts_cache_dir),
    _homeassistant: None = Depends(load_homeassistant),
    _client: APIClient = Depends(mock_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> MockConfigEntry:
    """Set up the ESPHome integration for testing."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
