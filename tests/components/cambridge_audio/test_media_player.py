"""Tests for the Cambridge Audio integration."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

from aiostreammagic import (
    RepeatMode as CambridgeRepeatMode,
    ShuffleMode,
    TransportControl,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.media_player import (
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_REPEAT,
    ATTR_MEDIA_SEEK_POSITION,
    ATTR_MEDIA_SHUFFLE,
    ATTR_MEDIA_VOLUME_LEVEL,
    DOMAIN as MP_DOMAIN,
    SERVICE_PLAY_MEDIA,
    RepeatMode,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_MEDIA_NEXT_TRACK,
    SERVICE_MEDIA_PAUSE,
    SERVICE_MEDIA_PLAY,
    SERVICE_MEDIA_PREVIOUS_TRACK,
    SERVICE_MEDIA_SEEK,
    SERVICE_MEDIA_STOP,
    SERVICE_REPEAT_SET,
    SERVICE_SHUFFLE_SET,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SERVICE_VOLUME_DOWN,
    SERVICE_VOLUME_SET,
    SERVICE_VOLUME_UP,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from . import mock_state_update, setup_integration
from ._fixtures import (
    mock_config_entry as mock_config_entry_fixture,
    mock_stream_magic_client as mock_stream_magic_client_fixture,
)
from .const import ENTITY_ID

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
) -> AsyncGenerator[HomeAssistant]:
    yield hass


@test
async def media_play_pause_stop(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_stream_magic_client: AsyncMock = Depends(mock_stream_magic_client_fixture),
) -> None:
    """Test media play/pause/stop service."""
    await setup_integration(hass, mock_config_entry)

    data = {ATTR_ENTITY_ID: ENTITY_ID}

    await hass.services.async_call(MP_DOMAIN, SERVICE_MEDIA_PAUSE, data, True)
    mock_stream_magic_client.play_pause.assert_called_once()

    await hass.services.async_call(MP_DOMAIN, SERVICE_MEDIA_PLAY, data, True)
    expect(mock_stream_magic_client.play_pause.call_count).to_equal(2)

    mock_stream_magic_client.now_playing.controls = [
        TransportControl.PLAY,
        TransportControl.PAUSE,
        TransportControl.STOP,
    ]
    await mock_state_update(mock_stream_magic_client)
    await hass.async_block_till_done()

    await hass.services.async_call(MP_DOMAIN, SERVICE_MEDIA_PAUSE, data, True)
    mock_stream_magic_client.pause.assert_called_once()

    await hass.services.async_call(MP_DOMAIN, SERVICE_MEDIA_PLAY, data, True)
    mock_stream_magic_client.play.assert_called_once()

    await hass.services.async_call(MP_DOMAIN, SERVICE_MEDIA_STOP, data, True)
    mock_stream_magic_client.stop.assert_called_once()


@test
async def media_next_previous_track(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_stream_magic_client: AsyncMock = Depends(mock_stream_magic_client_fixture),
) -> None:
    """Test media next/previous track service."""
    await setup_integration(hass, mock_config_entry)

    data = {ATTR_ENTITY_ID: ENTITY_ID}
    await hass.services.async_call(MP_DOMAIN, SERVICE_MEDIA_NEXT_TRACK, data, True)
    mock_stream_magic_client.next_track.assert_called_once()
    await hass.services.async_call(MP_DOMAIN, SERVICE_MEDIA_PREVIOUS_TRACK, data, True)
    mock_stream_magic_client.previous_track.assert_called_once()


@test
async def shuffle_repeat_set(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_stream_magic_client: AsyncMock = Depends(mock_stream_magic_client_fixture),
) -> None:
    """Test shuffle and repeat set service."""
    await setup_integration(hass, mock_config_entry)

    mock_stream_magic_client.now_playing.controls = [
        TransportControl.TOGGLE_SHUFFLE,
        TransportControl.TOGGLE_REPEAT,
    ]

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_SHUFFLE_SET,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_MEDIA_SHUFFLE: False},
    )
    mock_stream_magic_client.set_shuffle.assert_called_with(ShuffleMode.OFF)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_SHUFFLE_SET,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_MEDIA_SHUFFLE: True},
    )
    mock_stream_magic_client.set_shuffle.assert_called_with(ShuffleMode.ALL)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_REPEAT_SET,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_MEDIA_REPEAT: RepeatMode.OFF},
    )
    mock_stream_magic_client.set_repeat.assert_called_with(CambridgeRepeatMode.OFF)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_REPEAT_SET,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_MEDIA_REPEAT: RepeatMode.ALL},
    )
    mock_stream_magic_client.set_repeat.assert_called_with(CambridgeRepeatMode.ALL)


@test
async def shuffle_repeat_get(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_stream_magic_client: AsyncMock = Depends(mock_stream_magic_client_fixture),
) -> None:
    """Test shuffle and repeat get service."""
    await setup_integration(hass, mock_config_entry)

    mock_stream_magic_client.play_state.mode_shuffle = None

    state = hass.states.get(ENTITY_ID)
    expect(state.attributes[ATTR_MEDIA_SHUFFLE]).to_be(False)

    mock_stream_magic_client.play_state.mode_shuffle = ShuffleMode.ALL
    await mock_state_update(mock_stream_magic_client)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    expect(state.attributes[ATTR_MEDIA_SHUFFLE]).to_be(True)

    mock_stream_magic_client.play_state.mode_repeat = CambridgeRepeatMode.ALL
    await mock_state_update(mock_stream_magic_client)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    expect(state.attributes[ATTR_MEDIA_REPEAT]).to_equal(RepeatMode.ALL)


@test
async def power_service(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_stream_magic_client: AsyncMock = Depends(mock_stream_magic_client_fixture),
) -> None:
    """Test power service."""
    await setup_integration(hass, mock_config_entry)

    data = {ATTR_ENTITY_ID: ENTITY_ID}
    await hass.services.async_call(MP_DOMAIN, SERVICE_TURN_ON, data, True)
    mock_stream_magic_client.power_on.assert_called_once()
    await hass.services.async_call(MP_DOMAIN, SERVICE_TURN_OFF, data, True)
    mock_stream_magic_client.power_off.assert_called_once()


@test
async def media_seek(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_stream_magic_client: AsyncMock = Depends(mock_stream_magic_client_fixture),
) -> None:
    """Test media seek service."""
    await setup_integration(hass, mock_config_entry)

    mock_stream_magic_client.now_playing.controls = [TransportControl.SEEK]
    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_SEEK,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_MEDIA_SEEK_POSITION: 100},
    )
    mock_stream_magic_client.media_seek.assert_called_once_with(100)


@test
async def media_volume(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_stream_magic_client: AsyncMock = Depends(mock_stream_magic_client_fixture),
) -> None:
    """Test volume service."""
    await setup_integration(hass, mock_config_entry)

    mock_stream_magic_client.state.pre_amp_mode = True

    await hass.services.async_call(
        MP_DOMAIN, SERVICE_VOLUME_UP, {ATTR_ENTITY_ID: ENTITY_ID}
    )
    mock_stream_magic_client.volume_up.assert_called_once()

    await hass.services.async_call(
        MP_DOMAIN, SERVICE_VOLUME_DOWN, {ATTR_ENTITY_ID: ENTITY_ID}
    )
    mock_stream_magic_client.volume_down.assert_called_once()

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_VOLUME_SET,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_MEDIA_VOLUME_LEVEL: 0.30},
    )
    mock_stream_magic_client.set_volume.assert_called_once_with(30)


@test
async def play_media_preset_item_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_stream_magic_client: AsyncMock = Depends(mock_stream_magic_client_fixture),
) -> None:
    """Test playing media with a preset item id."""
    await setup_integration(hass, mock_config_entry)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: ENTITY_ID,
            ATTR_MEDIA_CONTENT_TYPE: "preset",
            ATTR_MEDIA_CONTENT_ID: "1",
        },
        blocking=True,
    )
    expect(mock_stream_magic_client.recall_preset.call_count).to_equal(1)
    expect(mock_stream_magic_client.recall_preset.call_args_list[0].args[0]).to_equal(1)

    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_PLAY_MEDIA,
            {
                ATTR_ENTITY_ID: ENTITY_ID,
                ATTR_MEDIA_CONTENT_TYPE: "preset",
                ATTR_MEDIA_CONTENT_ID: "10",
            },
            blocking=True,
        )

    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_PLAY_MEDIA,
            {
                ATTR_ENTITY_ID: ENTITY_ID,
                ATTR_MEDIA_CONTENT_TYPE: "preset",
                ATTR_MEDIA_CONTENT_ID: "UNKNOWN_PRESET",
            },
            blocking=True,
        )


@test
async def play_media_airable_radio_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_stream_magic_client: AsyncMock = Depends(mock_stream_magic_client_fixture),
) -> None:
    """Test playing media with an airable radio id."""
    await setup_integration(hass, mock_config_entry)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: ENTITY_ID,
            ATTR_MEDIA_CONTENT_TYPE: "airable",
            ATTR_MEDIA_CONTENT_ID: "12345678",
        },
        blocking=True,
    )
    expect(mock_stream_magic_client.play_radio_airable.call_count).to_equal(1)
    call_args = mock_stream_magic_client.play_radio_airable.call_args_list[0].args
    expect(call_args[0]).to_equal("Radio")
    expect(call_args[1]).to_equal(12345678)


@test
async def play_media_internet_radio(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_stream_magic_client: AsyncMock = Depends(mock_stream_magic_client_fixture),
) -> None:
    """Test playing media with a url."""
    await setup_integration(hass, mock_config_entry)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: ENTITY_ID,
            ATTR_MEDIA_CONTENT_TYPE: "internet_radio",
            ATTR_MEDIA_CONTENT_ID: "https://example.com",
        },
        blocking=True,
    )
    expect(mock_stream_magic_client.play_radio_url.call_count).to_equal(1)
    call_args = mock_stream_magic_client.play_radio_url.call_args_list[0].args
    expect(call_args[0]).to_equal("Radio")
    expect(call_args[1]).to_equal("https://example.com")


@test
async def play_media_unknown_type(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_stream_magic_client: AsyncMock = Depends(mock_stream_magic_client_fixture),
) -> None:
    """Test playing media with an unsupported content type."""
    await setup_integration(hass, mock_config_entry)

    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_PLAY_MEDIA,
            {
                ATTR_ENTITY_ID: ENTITY_ID,
                ATTR_MEDIA_CONTENT_TYPE: "unsupported_content_type",
                ATTR_MEDIA_CONTENT_ID: "1",
            },
            blocking=True,
        )
