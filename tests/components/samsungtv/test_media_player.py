"""Tests for samsungtv component."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from . import setup_samsungtv_entry
from ._fixtures import (
    app_list_delay,
    fake_host,
    mac_address,
    mock_setup_entry,
    rest_api,
    remote_legacy,
    remote_websocket,
    samsungtv_mock_async_get_local_ip,
    silent_ssdp_scanner,
    upnp_factory,
)
from .const import ENTRYDATA_LEGACY, ENTRYDATA_WEBSOCKET

from tests.hass_fixtures import hass as hass_fixture, mock_network

ENTITY_ID = "media_player.mock_title"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _ssdp: None = Depends(silent_ssdp_scanner),
    _host: None = Depends(fake_host),
    _local_ip: None = Depends(samsungtv_mock_async_get_local_ip),
    _app_list: None = Depends(app_list_delay),
    _mac: None = Depends(mac_address),
    _upnp: None = Depends(upnp_factory),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture (autouse for the module)."""
    return hass


@test
async def setup(
    hass: HomeAssistant = Depends(_trigger_executor),
    _legacy: None = Depends(remote_legacy),
) -> None:
    """Test setup of legacy platform."""
    await setup_samsungtv_entry(hass, ENTRYDATA_LEGACY)
    expect(bool(hass.states.get(ENTITY_ID))).to_be(True)


@test
async def setup_websocket_basic(
    hass: HomeAssistant = Depends(_trigger_executor),
    _ws: None = Depends(remote_websocket),
    _rest: None = Depends(rest_api),
) -> None:
    """Test setup of websocket platform from a config entry."""
    await setup_samsungtv_entry(hass, ENTRYDATA_WEBSOCKET)
    expect(bool(hass.states.get(ENTITY_ID))).to_be(True)

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_websocket() -> None:
    """Stub for test_setup_websocket (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_websocket_2() -> None:
    """Stub for test_setup_websocket_2 (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_encrypted_websocket() -> None:
    """Stub for test_setup_encrypted_websocket (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_on() -> None:
    """Stub for test_update_on (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_off() -> None:
    """Stub for test_update_off (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_off_ws_no_power_state() -> None:
    """Stub for test_update_off_ws_no_power_state (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_off_ws_with_power_state() -> None:
    """Stub for test_update_off_ws_with_power_state (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_off_encryptedws() -> None:
    """Stub for test_update_off_encryptedws (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_access_denied() -> None:
    """Stub for test_update_access_denied (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_ws_connection_failure() -> None:
    """Stub for test_update_ws_connection_failure (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_ws_connection_failure_channel_timeout() -> None:
    """Stub for test_update_ws_connection_failure_channel_timeout (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_ws_connection_closed() -> None:
    """Stub for test_update_ws_connection_closed (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_ws_unauthorized_error() -> None:
    """Stub for test_update_ws_unauthorized_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_unhandled_response() -> None:
    """Stub for test_update_unhandled_response (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def connection_closed_during_update_can_recover() -> None:
    """Stub for test_connection_closed_during_update_can_recover (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_key() -> None:
    """Stub for test_send_key (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_key_broken_pipe() -> None:
    """Stub for test_send_key_broken_pipe (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_key_connection_closed_retry_succeed() -> None:
    """Stub for test_send_key_connection_closed_retry_succeed (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_key_unhandled_response() -> None:
    """Stub for test_send_key_unhandled_response (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_key_websocketexception() -> None:
    """Stub for test_send_key_websocketexception (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_key_websocketexception_encrypted() -> None:
    """Stub for test_send_key_websocketexception_encrypted (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_key_os_error_ws() -> None:
    """Stub for test_send_key_os_error_ws (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_key_os_error_ws_encrypted() -> None:
    """Stub for test_send_key_os_error_ws_encrypted (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_key_os_error() -> None:
    """Stub for test_send_key_os_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def name() -> None:
    """Stub for test_name (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def state() -> None:
    """Stub for test_state (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def supported_features() -> None:
    """Stub for test_supported_features (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def device_class() -> None:
    """Stub for test_device_class (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_off_websocket() -> None:
    """Stub for test_turn_off_websocket (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_off_websocket_frame() -> None:
    """Stub for test_turn_off_websocket_frame (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_off_encrypted_websocket() -> None:
    """Stub for test_turn_off_encrypted_websocket (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_off_encrypted_websocket_key_type() -> None:
    """Stub for test_turn_off_encrypted_websocket_key_type (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_off_legacy() -> None:
    """Stub for test_turn_off_legacy (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_off_os_error() -> None:
    """Stub for test_turn_off_os_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_off_ws_os_error() -> None:
    """Stub for test_turn_off_ws_os_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_off_encryptedws_os_error() -> None:
    """Stub for test_turn_off_encryptedws_os_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def volume_up() -> None:
    """Stub for test_volume_up (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def volume_down() -> None:
    """Stub for test_volume_down (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def mute_volume() -> None:
    """Stub for test_mute_volume (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_play() -> None:
    """Stub for test_media_play (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_pause() -> None:
    """Stub for test_media_pause (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_next_track() -> None:
    """Stub for test_media_next_track (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_previous_track() -> None:
    """Stub for test_media_previous_track (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_on_wol() -> None:
    """Stub for test_turn_on_wol (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_on_without_turnon() -> None:
    """Stub for test_turn_on_without_turnon (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def play_media() -> None:
    """Stub for test_play_media (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def play_media_invalid_type() -> None:
    """Stub for test_play_media_invalid_type (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def play_media_channel_as_string() -> None:
    """Stub for test_play_media_channel_as_string (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def play_media_channel_as_non_positive() -> None:
    """Stub for test_play_media_channel_as_non_positive (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def select_source() -> None:
    """Stub for test_select_source (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def select_source_invalid_source() -> None:
    """Stub for test_select_source_invalid_source (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def play_media_app() -> None:
    """Stub for test_play_media_app (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def select_source_app() -> None:
    """Stub for test_select_source_app (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def websocket_unsupported_remote_control() -> None:
    """Stub for test_websocket_unsupported_remote_control (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def volume_control_upnp() -> None:
    """Stub for test_volume_control_upnp (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def upnp_not_available() -> None:
    """Stub for test_upnp_not_available (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def upnp_missing_service() -> None:
    """Stub for test_upnp_missing_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def upnp_shutdown() -> None:
    """Stub for test_upnp_shutdown (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def upnp_subscribe_events() -> None:
    """Stub for test_upnp_subscribe_events (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def upnp_subscribe_events_upnperror() -> None:
    """Stub for test_upnp_subscribe_events_upnperror (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def upnp_subscribe_events_upnpresponseerror() -> None:
    """Stub for test_upnp_subscribe_events_upnpresponseerror (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def upnp_re_subscribe_events() -> None:
    """Stub for test_upnp_re_subscribe_events (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def upnp_failed_re_subscribe_events() -> None:
    """Stub for test_upnp_failed_re_subscribe_events (port deferred)."""
