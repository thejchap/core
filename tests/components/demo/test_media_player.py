"""The tests for the Demo Media player platform."""

from collections.abc import Generator
from unittest.mock import patch

import voluptuous as vol

from tryke import Depends, expect, fixture, test

from homeassistant.components.media_player import (
    ATTR_GROUP_MEMBERS,
    ATTR_INPUT_SOURCE,
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_EPISODE,
    ATTR_MEDIA_REPEAT,
    ATTR_MEDIA_SEEK_POSITION,
    ATTR_MEDIA_TRACK,
    ATTR_MEDIA_VOLUME_LEVEL,
    ATTR_MEDIA_VOLUME_MUTED,
    DOMAIN as MP_DOMAIN,
    SERVICE_CLEAR_PLAYLIST,
    SERVICE_JOIN,
    SERVICE_PLAY_MEDIA,
    SERVICE_SELECT_SOURCE,
    SERVICE_UNJOIN,
    MediaPlayerEntityFeature,
    RepeatMode,
    is_on,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_MEDIA_NEXT_TRACK,
    SERVICE_MEDIA_PAUSE,
    SERVICE_MEDIA_PLAY,
    SERVICE_MEDIA_PLAY_PAUSE,
    SERVICE_MEDIA_PREVIOUS_TRACK,
    SERVICE_MEDIA_SEEK,
    SERVICE_MEDIA_STOP,
    SERVICE_REPEAT_SET,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SERVICE_VOLUME_DOWN,
    SERVICE_VOLUME_MUTE,
    SERVICE_VOLUME_SET,
    SERVICE_VOLUME_UP,
    STATE_OFF,
    STATE_PAUSED,
    STATE_PLAYING,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import setup_homeassistant

from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async

TEST_ENTITY_ID = "media_player.walkman"


@fixture
def media_player_only() -> Generator[None]:
    """Enable only the media_player platform."""
    with patch(
        "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
        [Platform.MEDIA_PLAYER],
    ):
        yield


@fixture
async def setup_comp(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_ha: None = Depends(setup_homeassistant),
    _mp_only: None = Depends(media_player_only),
) -> None:
    """Initialize the media_player demo component."""
    expect(
        await async_setup_component(
            hass, MP_DOMAIN, {"media_player": {"platform": "demo"}}
        )
    ).to_be(True)
    await hass.async_block_till_done()


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_comp: None = Depends(setup_comp),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@fixture
def mock_media_seek() -> Generator[object]:
    """Mock demo YouTube player media seek."""
    with patch(
        "homeassistant.components.demo.media_player.DemoYoutubePlayer.media_seek",
        autospec=True,
    ) as seek:
        yield seek


@test
async def source_select(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the input source service."""
    entity_id = "media_player.lounge_room"
    state = hass.states.get(entity_id)
    expect(state.attributes.get(ATTR_INPUT_SOURCE)).to_equal("dvd")

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_SELECT_SOURCE,
            {ATTR_ENTITY_ID: entity_id, ATTR_INPUT_SOURCE: None},
            blocking=True,
        )
    state = hass.states.get(entity_id)
    expect(state.attributes.get(ATTR_INPUT_SOURCE)).to_equal("dvd")

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_SELECT_SOURCE,
        {ATTR_ENTITY_ID: entity_id, ATTR_INPUT_SOURCE: "xbox"},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    expect(state.attributes.get(ATTR_INPUT_SOURCE)).to_equal("xbox")


@test
async def repeat_set(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the repeat set service."""
    entity_id = "media_player.walkman"
    state = hass.states.get(entity_id)
    expect(state.attributes.get(ATTR_MEDIA_REPEAT)).to_equal(RepeatMode.OFF)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_REPEAT_SET,
        {ATTR_ENTITY_ID: entity_id, ATTR_MEDIA_REPEAT: RepeatMode.ALL},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    expect(state.attributes.get(ATTR_MEDIA_REPEAT)).to_equal(RepeatMode.ALL)


@test
async def clear_playlist(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test clear playlist."""
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_PLAYING)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_CLEAR_PLAYLIST,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_OFF)


@test
async def volume_services(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the volume service."""
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.attributes.get(ATTR_MEDIA_VOLUME_LEVEL)).to_equal(1.0)

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_VOLUME_SET,
            {ATTR_ENTITY_ID: TEST_ENTITY_ID, ATTR_MEDIA_VOLUME_LEVEL: None},
            blocking=True,
        )

    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.attributes.get(ATTR_MEDIA_VOLUME_LEVEL)).to_equal(1.0)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_VOLUME_SET,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID, ATTR_MEDIA_VOLUME_LEVEL: 0.5},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.attributes.get(ATTR_MEDIA_VOLUME_LEVEL)).to_equal(0.5)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_VOLUME_DOWN,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.attributes.get(ATTR_MEDIA_VOLUME_LEVEL)).to_equal(0.4)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_VOLUME_UP,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.attributes.get(ATTR_MEDIA_VOLUME_LEVEL)).to_equal(0.5)
    expect(state.attributes.get(ATTR_MEDIA_VOLUME_MUTED)).to_be(False)

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_VOLUME_MUTE,
            {ATTR_ENTITY_ID: TEST_ENTITY_ID, ATTR_MEDIA_VOLUME_MUTED: None},
            blocking=True,
        )

    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.attributes.get(ATTR_MEDIA_VOLUME_MUTED)).to_be(False)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_VOLUME_MUTE,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID, ATTR_MEDIA_VOLUME_MUTED: True},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.attributes.get(ATTR_MEDIA_VOLUME_MUTED)).to_be(True)


@test
async def turning_off_and_on(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turn_on and turn_off."""
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_PLAYING)

    await hass.services.async_call(
        MP_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: TEST_ENTITY_ID}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_OFF)
    expect(is_on(hass, TEST_ENTITY_ID)).to_be(False)

    await hass.services.async_call(
        MP_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: TEST_ENTITY_ID}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_PLAYING)
    expect(is_on(hass, TEST_ENTITY_ID)).to_be(True)

    await hass.services.async_call(
        MP_DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: TEST_ENTITY_ID}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_OFF)
    expect(is_on(hass, TEST_ENTITY_ID)).to_be(False)


@test
async def playing_pausing(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test media_pause."""
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_PLAYING)

    await hass.services.async_call(
        MP_DOMAIN, SERVICE_MEDIA_PAUSE, {ATTR_ENTITY_ID: TEST_ENTITY_ID}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_PAUSED)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_PLAY_PAUSE,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_PLAYING)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_PLAY_PAUSE,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_PAUSED)

    await hass.services.async_call(
        MP_DOMAIN, SERVICE_MEDIA_PLAY, {ATTR_ENTITY_ID: TEST_ENTITY_ID}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_PLAYING)


@test
async def prev_next_track(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test media_next_track and media_previous_track."""
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.attributes.get(ATTR_MEDIA_TRACK)).to_equal(1)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_NEXT_TRACK,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.attributes.get(ATTR_MEDIA_TRACK)).to_equal(2)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_NEXT_TRACK,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.attributes.get(ATTR_MEDIA_TRACK)).to_equal(3)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_PREVIOUS_TRACK,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.attributes.get(ATTR_MEDIA_TRACK)).to_equal(2)

    ent_id = "media_player.lounge_room"
    state = hass.states.get(ent_id)
    expect(state.attributes.get(ATTR_MEDIA_EPISODE)).to_equal("1")

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_NEXT_TRACK,
        {ATTR_ENTITY_ID: ent_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(ent_id)
    expect(state.attributes.get(ATTR_MEDIA_EPISODE)).to_equal("2")

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_PREVIOUS_TRACK,
        {ATTR_ENTITY_ID: ent_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(ent_id)
    expect(state.attributes.get(ATTR_MEDIA_EPISODE)).to_equal("1")


@test
async def play_media(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test play_media."""
    ent_id = "media_player.living_room"
    state = hass.states.get(ent_id)
    expect(
        MediaPlayerEntityFeature.PLAY_MEDIA
        & state.attributes.get(ATTR_SUPPORTED_FEATURES)
        > 0
    ).to_be(True)
    expect(state.attributes.get(ATTR_MEDIA_CONTENT_ID) is not None).to_be(True)

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_PLAY_MEDIA,
            {ATTR_ENTITY_ID: ent_id, ATTR_MEDIA_CONTENT_ID: "some_id"},
            blocking=True,
        )
    state = hass.states.get(ent_id)
    expect(state.attributes.get(ATTR_MEDIA_CONTENT_ID) != "some_id").to_be(True)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: ent_id,
            ATTR_MEDIA_CONTENT_TYPE: "youtube",
            ATTR_MEDIA_CONTENT_ID: "some_id",
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(ent_id)
    expect(state.attributes.get(ATTR_MEDIA_CONTENT_ID)).to_equal("some_id")


@test
async def seek(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_seek: object = Depends(mock_media_seek),
) -> None:
    """Test seek."""
    ent_id = "media_player.living_room"
    state = hass.states.get(ent_id)
    expect(
        bool(
            state.attributes[ATTR_SUPPORTED_FEATURES] & MediaPlayerEntityFeature.SEEK
        )
    ).to_be(True)
    expect(mock_seek.called).to_be(False)

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_MEDIA_SEEK,
            {ATTR_ENTITY_ID: ent_id, ATTR_MEDIA_SEEK_POSITION: None},
            blocking=True,
        )
    expect(mock_seek.called).to_be(False)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_SEEK,
        {ATTR_ENTITY_ID: ent_id, ATTR_MEDIA_SEEK_POSITION: 100},
        blocking=True,
    )
    expect(mock_seek.called).to_be(True)


@test
async def stop(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test stop."""
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_PLAYING)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_STOP,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_OFF)


@test
async def grouping(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the join/unjoin services."""
    walkman = "media_player.walkman"
    kitchen = "media_player.kitchen"

    state = hass.states.get(walkman)
    expect(state.attributes.get(ATTR_GROUP_MEMBERS)).to_equal([])

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_JOIN,
        {ATTR_ENTITY_ID: walkman, ATTR_GROUP_MEMBERS: [kitchen]},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(walkman)
    expect(state.attributes.get(ATTR_GROUP_MEMBERS)).to_equal([walkman, kitchen])

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_UNJOIN,
        {ATTR_ENTITY_ID: walkman},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(walkman)
    expect(state.attributes.get(ATTR_GROUP_MEMBERS)).to_equal([])


@test.skip("requires hass_client (aiohttp client request flow)")
async def media_image_proxy() -> None:
    """Stub for test_media_image_proxy (port deferred)."""


@test.skip("requires hass_ws_client (websocket browse flow)")
async def browse() -> None:
    """Stub for test_browse (port deferred)."""
