"""The tests for reproduction of state."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.media_player import (
    ATTR_INPUT_SOURCE,
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_VOLUME_LEVEL,
    ATTR_MEDIA_VOLUME_MUTED,
    ATTR_SOUND_MODE,
    DOMAIN,
    SERVICE_PLAY_MEDIA,
    SERVICE_SELECT_SOUND_MODE,
    SERVICE_SELECT_SOURCE,
    MediaPlayerEntityFeature,
)
from homeassistant.components.media_player.reproduce_state import async_reproduce_states
from homeassistant.const import (
    ATTR_SUPPORTED_FEATURES,
    SERVICE_MEDIA_PAUSE,
    SERVICE_MEDIA_PLAY,
    SERVICE_MEDIA_STOP,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SERVICE_VOLUME_MUTE,
    SERVICE_VOLUME_SET,
    STATE_BUFFERING,
    STATE_IDLE,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
)
from homeassistant.core import Context, HomeAssistant, State

from tests.common import async_mock_service
from tests.hass_fixtures import hass as hass_fixture

ENTITY_1 = "media_player.test1"
ENTITY_2 = "media_player.test2"


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test.cases(
    test.case(
        "turn_on",
        service=SERVICE_TURN_ON,
        state=STATE_ON,
        supported_feature=MediaPlayerEntityFeature.TURN_ON,
    ),
    test.case(
        "turn_off",
        service=SERVICE_TURN_OFF,
        state=STATE_OFF,
        supported_feature=MediaPlayerEntityFeature.TURN_OFF,
    ),
    test.case(
        "media_play_buffering",
        service=SERVICE_MEDIA_PLAY,
        state=STATE_BUFFERING,
        supported_feature=MediaPlayerEntityFeature.PLAY,
    ),
    test.case(
        "media_play_playing",
        service=SERVICE_MEDIA_PLAY,
        state=STATE_PLAYING,
        supported_feature=MediaPlayerEntityFeature.PLAY,
    ),
    test.case(
        "media_stop",
        service=SERVICE_MEDIA_STOP,
        state=STATE_IDLE,
        supported_feature=MediaPlayerEntityFeature.STOP,
    ),
    test.case(
        "media_pause",
        service=SERVICE_MEDIA_PAUSE,
        state=STATE_PAUSED,
        supported_feature=MediaPlayerEntityFeature.PAUSE,
    ),
)
async def state(
    service: str,
    state: str,
    supported_feature: MediaPlayerEntityFeature,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that we can turn a state into a service call."""
    calls_1 = async_mock_service(hass, DOMAIN, service)
    if service != SERVICE_TURN_ON:
        async_mock_service(hass, DOMAIN, SERVICE_TURN_ON)

    # Don't support the feature won't call the service
    hass.states.async_set(ENTITY_1, "something", {ATTR_SUPPORTED_FEATURES: 0})
    await async_reproduce_states(hass, [State(ENTITY_1, state)])

    await hass.async_block_till_done()
    expect(len(calls_1)).to_equal(0)

    hass.states.async_set(
        ENTITY_1, "something", {ATTR_SUPPORTED_FEATURES: supported_feature}
    )
    await async_reproduce_states(hass, [State(ENTITY_1, state)])
    expect(len(calls_1)).to_equal(1)
    expect(calls_1[0].data).to_equal({"entity_id": ENTITY_1})


@test
async def turn_on_with_mode(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that state with additional attributes call multiple services."""
    hass.states.async_set(
        ENTITY_1,
        "something",
        {
            ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.SELECT_SOUND_MODE
        },
    )

    calls_1 = async_mock_service(hass, DOMAIN, SERVICE_TURN_ON)
    calls_2 = async_mock_service(hass, DOMAIN, SERVICE_SELECT_SOUND_MODE)

    await async_reproduce_states(
        hass, [State(ENTITY_1, "on", {ATTR_SOUND_MODE: "dummy"})]
    )

    await hass.async_block_till_done()

    expect(len(calls_1)).to_equal(1)
    expect(calls_1[0].data).to_equal({"entity_id": ENTITY_1})

    expect(len(calls_2)).to_equal(1)
    expect(calls_2[0].data).to_equal({"entity_id": ENTITY_1, ATTR_SOUND_MODE: "dummy"})


@test
async def multiple_same_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that multiple states with same state gets calls."""
    for entity in ENTITY_1, ENTITY_2:
        hass.states.async_set(
            entity,
            "something",
            {ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.TURN_ON},
        )

    calls_1 = async_mock_service(hass, DOMAIN, SERVICE_TURN_ON)

    await async_reproduce_states(hass, [State(ENTITY_1, "on"), State(ENTITY_2, "on")])

    await hass.async_block_till_done()

    expect(len(calls_1)).to_equal(2)
    # order is not guaranteed
    expect(
        any(call.data == {"entity_id": "media_player.test1"} for call in calls_1)
    ).to_be(True)
    expect(
        any(call.data == {"entity_id": "media_player.test2"} for call in calls_1)
    ).to_be(True)


@test
async def multiple_different_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that multiple states with different state gets calls."""
    for entity in ENTITY_1, ENTITY_2:
        hass.states.async_set(
            entity,
            "something",
            {
                ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.TURN_ON
                | MediaPlayerEntityFeature.TURN_OFF
            },
        )

    calls_1 = async_mock_service(hass, DOMAIN, SERVICE_TURN_ON)
    calls_2 = async_mock_service(hass, DOMAIN, SERVICE_TURN_OFF)

    await async_reproduce_states(hass, [State(ENTITY_1, "on"), State(ENTITY_2, "off")])

    await hass.async_block_till_done()

    expect(len(calls_1)).to_equal(1)
    expect(calls_1[0].data).to_equal({"entity_id": "media_player.test1"})
    expect(len(calls_2)).to_equal(1)
    expect(calls_2[0].data).to_equal({"entity_id": "media_player.test2"})


@test
async def state_with_context(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that context is forwarded."""
    hass.states.async_set(
        ENTITY_1,
        "something",
        {ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.TURN_ON},
    )

    calls = async_mock_service(hass, DOMAIN, SERVICE_TURN_ON)

    context = Context()

    await async_reproduce_states(hass, [State(ENTITY_1, "on")], context=context)

    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].data).to_equal({"entity_id": ENTITY_1})
    expect(calls[0].context).to_equal(context)


@test
async def attribute_no_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that no state service call is made with none state."""
    hass.states.async_set(
        ENTITY_1,
        "something",
        {
            ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.SELECT_SOUND_MODE
        },
    )

    calls_1 = async_mock_service(hass, DOMAIN, SERVICE_TURN_ON)
    calls_2 = async_mock_service(hass, DOMAIN, SERVICE_TURN_OFF)
    calls_3 = async_mock_service(hass, DOMAIN, SERVICE_SELECT_SOUND_MODE)

    value = "dummy"

    await async_reproduce_states(
        hass, [State(ENTITY_1, None, {ATTR_SOUND_MODE: value})]
    )

    await hass.async_block_till_done()

    expect(len(calls_1)).to_equal(0)
    expect(len(calls_2)).to_equal(0)
    expect(len(calls_3)).to_equal(1)
    expect(calls_3[0].data).to_equal({"entity_id": ENTITY_1, ATTR_SOUND_MODE: value})


@test.cases(
    test.case(
        "volume_set",
        service=SERVICE_VOLUME_SET,
        attribute=ATTR_MEDIA_VOLUME_LEVEL,
        supported_feature=MediaPlayerEntityFeature.VOLUME_SET,
    ),
    test.case(
        "volume_mute",
        service=SERVICE_VOLUME_MUTE,
        attribute=ATTR_MEDIA_VOLUME_MUTED,
        supported_feature=MediaPlayerEntityFeature.VOLUME_MUTE,
    ),
    test.case(
        "select_source",
        service=SERVICE_SELECT_SOURCE,
        attribute=ATTR_INPUT_SOURCE,
        supported_feature=MediaPlayerEntityFeature.SELECT_SOURCE,
    ),
    test.case(
        "select_sound_mode",
        service=SERVICE_SELECT_SOUND_MODE,
        attribute=ATTR_SOUND_MODE,
        supported_feature=MediaPlayerEntityFeature.SELECT_SOUND_MODE,
    ),
)
async def attribute(
    service: str,
    attribute: str,
    supported_feature: MediaPlayerEntityFeature,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that service call is made for each attribute."""
    hass.states.async_set(
        ENTITY_1,
        "something",
        {ATTR_SUPPORTED_FEATURES: supported_feature},
    )

    calls_1 = async_mock_service(hass, DOMAIN, service)

    value = "dummy"

    await async_reproduce_states(hass, [State(ENTITY_1, None, {attribute: value})])

    await hass.async_block_till_done()

    expect(len(calls_1)).to_equal(1)
    expect(calls_1[0].data).to_equal({"entity_id": ENTITY_1, attribute: value})


@test
async def play_media(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test playing media."""
    hass.states.async_set(
        ENTITY_1,
        "something",
        {ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.PLAY_MEDIA},
    )
    calls_1 = async_mock_service(hass, DOMAIN, SERVICE_PLAY_MEDIA)

    value_1 = "dummy_1"
    value_2 = "dummy_2"

    await async_reproduce_states(
        hass,
        [
            State(
                ENTITY_1,
                None,
                {ATTR_MEDIA_CONTENT_TYPE: value_1, ATTR_MEDIA_CONTENT_ID: value_2},
            )
        ],
    )

    await async_reproduce_states(
        hass,
        [
            State(
                ENTITY_1,
                None,
                {
                    ATTR_MEDIA_CONTENT_TYPE: value_1,
                    ATTR_MEDIA_CONTENT_ID: value_2,
                },
            )
        ],
    )

    await hass.async_block_till_done()

    expect(len(calls_1)).to_equal(2)
    expect(calls_1[0].data).to_equal(
        {
            "entity_id": ENTITY_1,
            ATTR_MEDIA_CONTENT_TYPE: value_1,
            ATTR_MEDIA_CONTENT_ID: value_2,
        }
    )

    expect(calls_1[1].data).to_equal(
        {
            "entity_id": ENTITY_1,
            ATTR_MEDIA_CONTENT_TYPE: value_1,
            ATTR_MEDIA_CONTENT_ID: value_2,
        }
    )
