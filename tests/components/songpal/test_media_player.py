"""Test songpal media_player."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock, call, patch

from songpal import (
    ConnectChange,
    ContentChange,
    PowerChange,
    SongpalException,
    VolumeChange,
)
from songpal.notification import SettingChange
from tryke import Depends, expect, fixture, test

from homeassistant.components import media_player, songpal
from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.components.songpal.const import ERROR_REQUEST_RETRY
from homeassistant.components.songpal.services import SET_SOUND_SETTING
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from . import (
    CONF_DATA,
    CONF_ENDPOINT,
    CONF_NAME,
    ENDPOINT,
    ENTITY_ID,
    FRIENDLY_NAME,
    MAC,
    MODEL,
    SW_VERSION,
    WIRELESS_MAC,
    _create_mocked_device,
    _patch_media_player_device,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async

SUPPORT_SONGPAL = (
    MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


def _get_attributes(hass: HomeAssistant) -> dict[str, Any]:
    state = hass.states.get(ENTITY_ID)
    return state.as_dict()["attributes"]


async def _call(hass: HomeAssistant, service: str, **argv: Any) -> None:
    await hass.services.async_call(
        media_player.DOMAIN,
        service,
        {"entity_id": ENTITY_ID, **argv},
        blocking=True,
    )


@test
async def setup_platform(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the legacy setup platform."""
    mocked_device = _create_mocked_device(throw_exception=True)
    with _patch_media_player_device(mocked_device):
        await async_setup_component(
            hass,
            media_player.DOMAIN,
            {
                media_player.DOMAIN: [
                    {
                        "platform": songpal.DOMAIN,
                        CONF_NAME: FRIENDLY_NAME,
                        CONF_ENDPOINT: ENDPOINT,
                    }
                ],
            },
        )
        await hass.async_block_till_done()

    mocked_device.assert_not_called()
    all_states = hass.states.async_all()
    expect(len(all_states)).to_equal(0)


@test
async def setup_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test failed to set up the entity."""
    mocked_device = _create_mocked_device(throw_exception=True)
    entry = MockConfigEntry(domain=songpal.DOMAIN, data=CONF_DATA)
    entry.add_to_hass(hass)

    with _patch_media_player_device(mocked_device):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    all_states = hass.states.async_all()
    expect(len(all_states)).to_equal(0)
    expect("[name(http://0.0.0.0:10000/sony)] Unable to connect" in caplog.text).to_be(
        True
    )
    expect(
        "Platform songpal not ready yet: Unable to do POST request" in caplog.text
    ).to_be(True)
    expect(any(x.levelno == logging.ERROR for x in caplog.records)).to_be(False)
    caplog.clear()

    utcnow = dt_util.utcnow()
    type(mocked_device).get_supported_methods = AsyncMock()
    with _patch_media_player_device(mocked_device):
        async_fire_time_changed(hass, utcnow + timedelta(seconds=30))
        await hass.async_block_till_done()
    all_states = hass.states.async_all()
    expect(len(all_states)).to_equal(1)
    expect(any(x.levelno == logging.WARNING for x in caplog.records)).to_be(False)
    expect(any(x.levelno == logging.ERROR for x in caplog.records)).to_be(False)


@test
async def state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test state of the entity."""
    mocked_device = _create_mocked_device()
    entry = MockConfigEntry(domain=songpal.DOMAIN, data=CONF_DATA)
    entry.add_to_hass(hass)

    with _patch_media_player_device(mocked_device):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    expect(state.name).to_equal(FRIENDLY_NAME)
    expect(state.state).to_equal(STATE_ON)
    attributes = state.as_dict()["attributes"]
    expect(attributes["volume_level"]).to_equal(0.5)
    expect(attributes["is_volume_muted"]).to_be(False)
    expect(attributes["source_list"]).to_equal(["title1", "title2"])
    expect(attributes["source"]).to_equal("title2")
    expect(attributes["sound_mode_list"]).to_equal(["Sound Mode 1", "Sound Mode 2"])
    expect(attributes["sound_mode"]).to_equal("Sound Mode 2")
    expect(attributes["supported_features"]).to_equal(SUPPORT_SONGPAL)

    device = device_registry.async_get_device(identifiers={(songpal.DOMAIN, MAC)})
    expect(device.connections).to_equal({(dr.CONNECTION_NETWORK_MAC, MAC)})
    expect(device.manufacturer).to_equal("Sony Corporation")
    expect(device.name).to_equal(FRIENDLY_NAME)
    expect(device.sw_version).to_equal(SW_VERSION)
    expect(device.model).to_equal(MODEL)

    entity = entity_registry.async_get(ENTITY_ID)
    expect(entity.unique_id).to_equal(MAC)


@test
async def state_nosoundmode(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test state of the entity with no soundField in sound settings."""
    mocked_device = _create_mocked_device(no_soundfield=True)
    entry = MockConfigEntry(domain=songpal.DOMAIN, data=CONF_DATA)
    entry.add_to_hass(hass)

    with _patch_media_player_device(mocked_device):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    expect(state.name).to_equal(FRIENDLY_NAME)
    expect(state.state).to_equal(STATE_ON)
    attributes = state.as_dict()["attributes"]
    expect(attributes["volume_level"]).to_equal(0.5)
    expect(attributes["is_volume_muted"]).to_be(False)
    expect(attributes["source_list"]).to_equal(["title1", "title2"])
    expect(attributes["source"]).to_equal("title2")
    expect("sound_mode_list" in attributes).to_be(False)
    expect("sound_mode" in attributes).to_be(False)
    expect(attributes["supported_features"]).to_equal(SUPPORT_SONGPAL)

    device = device_registry.async_get_device(identifiers={(songpal.DOMAIN, MAC)})
    expect(device.connections).to_equal({(dr.CONNECTION_NETWORK_MAC, MAC)})
    expect(device.manufacturer).to_equal("Sony Corporation")
    expect(device.name).to_equal(FRIENDLY_NAME)
    expect(device.sw_version).to_equal(SW_VERSION)
    expect(device.model).to_equal(MODEL)

    entity = entity_registry.async_get(ENTITY_ID)
    expect(entity.unique_id).to_equal(MAC)


@test
async def state_wireless(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test state of the entity with only Wireless MAC."""
    mocked_device = _create_mocked_device(wired_mac=None, wireless_mac=WIRELESS_MAC)
    entry = MockConfigEntry(domain=songpal.DOMAIN, data=CONF_DATA)
    entry.add_to_hass(hass)

    with _patch_media_player_device(mocked_device):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    expect(state.name).to_equal(FRIENDLY_NAME)
    expect(state.state).to_equal(STATE_ON)
    attributes = state.as_dict()["attributes"]
    expect(attributes["volume_level"]).to_equal(0.5)
    expect(attributes["is_volume_muted"]).to_be(False)
    expect(attributes["source_list"]).to_equal(["title1", "title2"])
    expect(attributes["source"]).to_equal("title2")
    expect(attributes["sound_mode_list"]).to_equal(["Sound Mode 1", "Sound Mode 2"])
    expect(attributes["sound_mode"]).to_equal("Sound Mode 2")
    expect(attributes["supported_features"]).to_equal(SUPPORT_SONGPAL)

    device = device_registry.async_get_device(
        identifiers={(songpal.DOMAIN, WIRELESS_MAC)}
    )
    expect(device.connections).to_equal({(dr.CONNECTION_NETWORK_MAC, WIRELESS_MAC)})
    expect(device.manufacturer).to_equal("Sony Corporation")
    expect(device.name).to_equal(FRIENDLY_NAME)
    expect(device.sw_version).to_equal(SW_VERSION)
    expect(device.model).to_equal(MODEL)

    entity = entity_registry.async_get(ENTITY_ID)
    expect(entity.unique_id).to_equal(WIRELESS_MAC)


@test
async def state_both(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test state of the entity with both Wired and Wireless MAC."""
    mocked_device = _create_mocked_device(wired_mac=MAC, wireless_mac=WIRELESS_MAC)
    entry = MockConfigEntry(domain=songpal.DOMAIN, data=CONF_DATA)
    entry.add_to_hass(hass)

    with _patch_media_player_device(mocked_device):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    expect(state.name).to_equal(FRIENDLY_NAME)
    expect(state.state).to_equal(STATE_ON)
    attributes = state.as_dict()["attributes"]
    expect(attributes["volume_level"]).to_equal(0.5)
    expect(attributes["is_volume_muted"]).to_be(False)
    expect(attributes["source_list"]).to_equal(["title1", "title2"])
    expect(attributes["source"]).to_equal("title2")
    expect(attributes["sound_mode_list"]).to_equal(["Sound Mode 1", "Sound Mode 2"])
    expect(attributes["sound_mode"]).to_equal("Sound Mode 2")
    expect(attributes["supported_features"]).to_equal(SUPPORT_SONGPAL)

    device = device_registry.async_get_device(identifiers={(songpal.DOMAIN, MAC)})
    expect(device.connections).to_equal(
        {
            (dr.CONNECTION_NETWORK_MAC, MAC),
            (dr.CONNECTION_NETWORK_MAC, WIRELESS_MAC),
        }
    )
    expect(device.manufacturer).to_equal("Sony Corporation")
    expect(device.name).to_equal(FRIENDLY_NAME)
    expect(device.sw_version).to_equal(SW_VERSION)
    expect(device.model).to_equal(MODEL)

    entity = entity_registry.async_get(ENTITY_ID)
    # We prefer the wired mac if present.
    expect(entity.unique_id).to_equal(MAC)


@test
async def services(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test services."""
    mocked_device = _create_mocked_device()
    entry = MockConfigEntry(domain=songpal.DOMAIN, data=CONF_DATA)
    entry.add_to_hass(hass)

    with _patch_media_player_device(mocked_device):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    await _call(hass, media_player.SERVICE_TURN_ON)
    await _call(hass, media_player.SERVICE_TURN_OFF)
    await _call(hass, media_player.SERVICE_TOGGLE)
    expect(mocked_device.set_power.call_count).to_equal(3)
    mocked_device.set_power.assert_has_calls([call(True), call(False), call(False)])

    await _call(hass, media_player.SERVICE_VOLUME_SET, volume_level=0.6)
    await _call(hass, media_player.SERVICE_VOLUME_UP)
    await _call(hass, media_player.SERVICE_VOLUME_DOWN)
    expect(mocked_device.volume1.set_volume.call_count).to_equal(3)
    mocked_device.volume1.set_volume.assert_has_calls([call(60), call(51), call(49)])

    await _call(hass, media_player.SERVICE_VOLUME_MUTE, is_volume_muted=True)
    mocked_device.volume1.set_mute.assert_called_once_with(True)

    await _call(hass, media_player.SERVICE_SELECT_SOURCE, source="none")
    mocked_device.input1.activate.assert_not_called()
    await _call(hass, media_player.SERVICE_SELECT_SOURCE, source="title1")
    mocked_device.input1.activate.assert_called_once()

    await hass.services.async_call(
        songpal.DOMAIN,
        SET_SOUND_SETTING,
        {"entity_id": ENTITY_ID, "name": "name", "value": "value"},
        blocking=True,
    )
    mocked_device.set_sound_settings.assert_called_once_with("name", "value")
    mocked_device.set_sound_settings.reset_mock()

    mocked_device2 = _create_mocked_device(wired_mac="mac2")
    entry2 = MockConfigEntry(
        domain=songpal.DOMAIN, data={CONF_NAME: "d2", CONF_ENDPOINT: ENDPOINT}
    )
    entry2.add_to_hass(hass)
    with _patch_media_player_device(mocked_device2):
        await hass.config_entries.async_setup(entry2.entry_id)
        await hass.async_block_till_done()

    await hass.services.async_call(
        songpal.DOMAIN,
        SET_SOUND_SETTING,
        {"entity_id": "all", "name": "name", "value": "value"},
        blocking=True,
    )
    mocked_device.set_sound_settings.assert_called_once_with("name", "value")
    mocked_device2.set_sound_settings.assert_called_once_with("name", "value")
    mocked_device.set_sound_settings.reset_mock()
    mocked_device2.set_sound_settings.reset_mock()

    mocked_device3 = _create_mocked_device(wired_mac=None, wireless_mac=WIRELESS_MAC)
    entry3 = MockConfigEntry(
        domain=songpal.DOMAIN, data={CONF_NAME: "d2", CONF_ENDPOINT: ENDPOINT}
    )
    entry3.add_to_hass(hass)
    with _patch_media_player_device(mocked_device3):
        await hass.config_entries.async_setup(entry3.entry_id)
        await hass.async_block_till_done()

    await hass.services.async_call(
        songpal.DOMAIN,
        SET_SOUND_SETTING,
        {"entity_id": "all", "name": "name", "value": "value"},
        blocking=True,
    )
    mocked_device.set_sound_settings.assert_called_once_with("name", "value")
    mocked_device2.set_sound_settings.assert_called_once_with("name", "value")
    mocked_device3.set_sound_settings.assert_called_once_with("name", "value")

    await _call(hass, media_player.SERVICE_SELECT_SOUND_MODE, sound_mode="Sound Mode 1")
    mocked_device.set_sound_settings.assert_called_with("soundField", "sound_mode1")


@test
async def websocket_events(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test websocket events."""
    mocked_device = _create_mocked_device()
    entry = MockConfigEntry(domain=songpal.DOMAIN, data=CONF_DATA)
    entry.add_to_hass(hass)

    with _patch_media_player_device(mocked_device):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    mocked_device.listen_notifications.assert_called_once()
    expect(mocked_device.on_notification.call_count).to_equal(5)

    notification_callbacks = mocked_device.notification_callbacks

    volume_change = MagicMock()
    volume_change.mute = True
    volume_change.volume = 20
    await notification_callbacks[VolumeChange](volume_change)
    attributes = _get_attributes(hass)
    expect(attributes["is_volume_muted"]).to_be(True)
    expect(attributes["volume_level"]).to_equal(0.2)

    content_change = MagicMock()
    content_change.is_input = False
    content_change.uri = "uri1"
    await notification_callbacks[ContentChange](content_change)
    expect(_get_attributes(hass)["source"]).to_equal("title2")
    content_change.is_input = True
    await notification_callbacks[ContentChange](content_change)
    expect(_get_attributes(hass)["source"]).to_equal("title1")

    sound_mode_change = MagicMock()
    sound_mode_change.target = "soundField"
    sound_mode_change.currentValue = "sound_mode1"
    await notification_callbacks[SettingChange](sound_mode_change)
    expect(_get_attributes(hass)["sound_mode"]).to_equal("Sound Mode 1")
    sound_mode_change.currentValue = "sound_mode2"
    await notification_callbacks[SettingChange](sound_mode_change)
    expect(_get_attributes(hass)["sound_mode"]).to_equal("Sound Mode 2")

    power_change = MagicMock()
    power_change.status = False
    await notification_callbacks[PowerChange](power_change)
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_OFF)


@test
async def disconnected(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test disconnected behavior."""
    mocked_device = _create_mocked_device()
    entry = MockConfigEntry(domain=songpal.DOMAIN, data=CONF_DATA)
    entry.add_to_hass(hass)

    with _patch_media_player_device(mocked_device):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    async def _assert_state():
        state = hass.states.get(ENTITY_ID)
        expect(state.state).to_equal(STATE_UNAVAILABLE)

    connect_change = MagicMock()
    connect_change.exception = "disconnected"
    type(mocked_device).get_supported_methods = AsyncMock(
        side_effect=[SongpalException(""), SongpalException(""), _assert_state]
    )
    notification_callbacks = mocked_device.notification_callbacks
    with patch("homeassistant.components.songpal.media_player.INITIAL_RETRY_DELAY", 0):
        await notification_callbacks[ConnectChange](connect_change)
    warning_records = [x for x in caplog.records if x.levelno == logging.WARNING]
    expect(len(warning_records)).to_equal(2)
    expect(
        warning_records[0]
        .getMessage()
        .endswith("Got disconnected, trying to reconnect")
    ).to_be(True)
    expect(warning_records[1].getMessage().endswith("Connection reestablished")).to_be(
        True
    )
    expect(any(x.levelno == logging.ERROR for x in caplog.records)).to_be(False)


@test.cases(
    test.case(
        "turn_on_retry",
        service=media_player.SERVICE_TURN_ON,
        error_code=ERROR_REQUEST_RETRY,
        swallow=True,
    ),
    test.case(
        "turn_on_other",
        service=media_player.SERVICE_TURN_ON,
        error_code=1234,
        swallow=False,
    ),
    test.case(
        "turn_off_retry",
        service=media_player.SERVICE_TURN_OFF,
        error_code=ERROR_REQUEST_RETRY,
        swallow=True,
    ),
    test.case(
        "turn_off_other",
        service=media_player.SERVICE_TURN_OFF,
        error_code=1234,
        swallow=False,
    ),
)
async def error_swallowing(
    service: str,
    error_code: int,
    swallow: bool,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test swallowing specific errors on turn_on and turn_off."""
    mocked_device = _create_mocked_device()
    entry = MockConfigEntry(domain=songpal.DOMAIN, data=CONF_DATA)
    entry.add_to_hass(hass)

    with _patch_media_player_device(mocked_device):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    type(mocked_device).set_power = AsyncMock(
        side_effect=[
            SongpalException("Error to swallow", error=(error_code, "Error to swallow"))
        ]
    )

    if swallow:
        await _call(hass, service)
        expect("Swallowing" in caplog.text).to_be(True)
    else:
        async with expect_raises_async(SongpalException):
            await _call(hass, service)
