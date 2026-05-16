"""Tests for the HDMI-CEC media player platform."""

from typing import Any

from pycec.const import (
    DEVICE_TYPE_NAMES,
    KEY_BACKWARD,
    KEY_FORWARD,
    KEY_MUTE_TOGGLE,
    KEY_PAUSE,
    KEY_PLAY,
    KEY_STOP,
    KEY_VOLUME_DOWN,
    KEY_VOLUME_UP,
    POWER_OFF,
    POWER_ON,
    STATUS_PLAY,
    STATUS_STILL,
    STATUS_STOP,
    TYPE_AUDIO,
    TYPE_PLAYBACK,
    TYPE_RECORDER,
    TYPE_TUNER,
    TYPE_TV,
    TYPE_UNKNOWN,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.hdmi_cec import EVENT_HDMI_CEC_UNAVAILABLE
from homeassistant.components.media_player import (
    DOMAIN as MEDIA_PLAYER_DOMAIN,
    MediaPlayerEntityFeature as MPEF,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_MEDIA_NEXT_TRACK,
    SERVICE_MEDIA_PAUSE,
    SERVICE_MEDIA_PLAY,
    SERVICE_MEDIA_PLAY_PAUSE,
    SERVICE_MEDIA_PREVIOUS_TRACK,
    SERVICE_MEDIA_STOP,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SERVICE_VOLUME_DOWN,
    SERVICE_VOLUME_MUTE,
    SERVICE_VOLUME_UP,
    STATE_IDLE,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant

from . import MockHDMIDevice, assert_key_press_release
from ._fixtures import (
    CecEntityCreator,
    HDMINetworkCreator,
    create_cec_entity,
    create_hdmi_network,
)

from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> int:
    return 0


@test
async def load_platform(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test that media_player entity is loaded."""
    hdmi_network = await create_hdmi_network(config={"platform": "media_player"})
    mock_hdmi_device = MockHDMIDevice(logical_address=3)
    await create_cec_entity(hdmi_network, mock_hdmi_device)
    mock_hdmi_device.set_update_callback.assert_called_once()
    state = hass.states.get("media_player.hdmi_3")
    expect(state).not_.to_be_none()

    state = hass.states.get("switch.hdmi_3")
    expect(state).to_be_none()


@test.cases(
    test.case("empty", platform={}),
    test.case("switch", platform={"platform": "switch"}),
)
async def load_types(
    platform: dict[str, Any],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test that media_player entity is loaded when types is set."""
    config = platform | {"types": {"hdmi_cec.hdmi_4": "media_player"}}
    hdmi_network = await create_hdmi_network(config=config)
    mock_hdmi_device = MockHDMIDevice(logical_address=3)
    await create_cec_entity(hdmi_network, mock_hdmi_device)
    mock_hdmi_device.set_update_callback.assert_called_once()
    state = hass.states.get("media_player.hdmi_3")
    expect(state).to_be_none()

    state = hass.states.get("switch.hdmi_3")
    expect(state).not_.to_be_none()

    mock_hdmi_device = MockHDMIDevice(logical_address=4)
    await create_cec_entity(hdmi_network, mock_hdmi_device)
    mock_hdmi_device.set_update_callback.assert_called_once()
    state = hass.states.get("media_player.hdmi_4")
    expect(state).not_.to_be_none()

    state = hass.states.get("switch.hdmi_4")
    expect(state).to_be_none()


@test
async def service_on(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test that media_player triggers on `on` service."""
    hdmi_network = await create_hdmi_network({"platform": "media_player"})
    mock_hdmi_device = MockHDMIDevice(logical_address=3)
    await create_cec_entity(hdmi_network, mock_hdmi_device)
    state = hass.states.get("media_player.hdmi_3")
    expect(state.state).not_.to_equal(STATE_ON)

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "media_player.hdmi_3"},
        blocking=True,
    )

    mock_hdmi_device.turn_on.assert_called_once_with()

    state = hass.states.get("media_player.hdmi_3")
    expect(state.state).to_equal(STATE_ON)


@test
async def service_off(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test that media_player triggers on `off` service."""
    hdmi_network = await create_hdmi_network({"platform": "media_player"})
    mock_hdmi_device = MockHDMIDevice(logical_address=3)
    await create_cec_entity(hdmi_network, mock_hdmi_device)
    state = hass.states.get("media_player.hdmi_3")
    expect(state.state).not_.to_equal(STATE_OFF)

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "media_player.hdmi_3"},
        blocking=True,
    )

    mock_hdmi_device.turn_off.assert_called_once_with()

    state = hass.states.get("media_player.hdmi_3")
    expect(state.state).to_equal(STATE_OFF)


@test.cases(
    test.case("tv", type_id=TYPE_TV, expected_features=(MPEF.TURN_ON, MPEF.TURN_OFF)),
    test.case(
        "recorder",
        type_id=TYPE_RECORDER,
        expected_features=(
            MPEF.TURN_ON,
            MPEF.TURN_OFF,
            MPEF.PAUSE,
            MPEF.STOP,
            MPEF.PREVIOUS_TRACK,
            MPEF.NEXT_TRACK,
        ),
    ),
    test.case(
        "recorder_play",
        type_id=TYPE_RECORDER,
        expected_features=(MPEF.PLAY,),
        xfail="The feature is wrongly set to PLAY_MEDIA, but should be PLAY.",
    ),
    test.case(
        "unknown", type_id=TYPE_UNKNOWN, expected_features=(MPEF.TURN_ON, MPEF.TURN_OFF)
    ),
    test.case(
        "tuner",
        type_id=TYPE_TUNER,
        expected_features=(
            MPEF.TURN_ON,
            MPEF.TURN_OFF,
            MPEF.PAUSE,
            MPEF.STOP,
        ),
        xfail="Checking for the wrong attribute, should be checking `type_id`, is checking `type`.",
    ),
    test.case(
        "tuner_play",
        type_id=TYPE_TUNER,
        expected_features=(MPEF.PLAY,),
        xfail="The feature is wrongly set to PLAY_MEDIA, but should be PLAY.",
    ),
    test.case(
        "playback",
        type_id=TYPE_PLAYBACK,
        expected_features=(
            MPEF.TURN_ON,
            MPEF.TURN_OFF,
            MPEF.PAUSE,
            MPEF.STOP,
            MPEF.PREVIOUS_TRACK,
            MPEF.NEXT_TRACK,
        ),
        xfail="Checking for the wrong attribute, should be checking `type_id`, is checking `type`.",
    ),
    test.case(
        "playback_play",
        type_id=TYPE_PLAYBACK,
        expected_features=(MPEF.PLAY,),
        xfail="The feature is wrongly set to PLAY_MEDIA, but should be PLAY.",
    ),
    test.case(
        "audio",
        type_id=TYPE_AUDIO,
        expected_features=(
            MPEF.TURN_ON,
            MPEF.TURN_OFF,
            MPEF.VOLUME_STEP,
            MPEF.VOLUME_MUTE,
        ),
    ),
)
async def supported_features(
    type_id: int,
    expected_features: tuple[MPEF, ...],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test that features load as expected."""
    hdmi_network = await create_hdmi_network({"platform": "media_player"})
    mock_hdmi_device = MockHDMIDevice(
        logical_address=3, type=type_id, type_name=DEVICE_TYPE_NAMES[type_id]
    )
    await create_cec_entity(hdmi_network, mock_hdmi_device)

    state = hass.states.get("media_player.hdmi_3")
    supported = state.attributes["supported_features"]
    for feature in expected_features:
        expect(bool(supported & feature)).to_be(True)


@test.cases(
    test.case("volume_down", service=SERVICE_VOLUME_DOWN, extra_data=None, key=KEY_VOLUME_DOWN),
    test.case("volume_up", service=SERVICE_VOLUME_UP, extra_data=None, key=KEY_VOLUME_UP),
    test.case(
        "mute_on",
        service=SERVICE_VOLUME_MUTE,
        extra_data={"is_volume_muted": True},
        key=KEY_MUTE_TOGGLE,
    ),
    test.case(
        "mute_off",
        service=SERVICE_VOLUME_MUTE,
        extra_data={"is_volume_muted": False},
        key=KEY_MUTE_TOGGLE,
    ),
)
async def volume_services(
    service: str,
    extra_data: dict[str, Any] | None,
    key: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test volume related commands."""
    hdmi_network = await create_hdmi_network({"platform": "media_player"})
    mock_hdmi_device = MockHDMIDevice(logical_address=3, type=TYPE_AUDIO)
    await create_cec_entity(hdmi_network, mock_hdmi_device)

    data = {ATTR_ENTITY_ID: "media_player.hdmi_3"}
    if extra_data:
        data |= extra_data

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        service,
        data,
        blocking=True,
    )

    expect(mock_hdmi_device.send_command.call_count).to_equal(2)
    assert_key_press_release(mock_hdmi_device.send_command, dst=3, key=key)


@test.cases(
    test.case("next", service=SERVICE_MEDIA_NEXT_TRACK, key=KEY_FORWARD),
    test.case("previous", service=SERVICE_MEDIA_PREVIOUS_TRACK, key=KEY_BACKWARD),
)
async def track_change_services(
    service: str,
    key: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test track change related commands."""
    hdmi_network = await create_hdmi_network({"platform": "media_player"})
    mock_hdmi_device = MockHDMIDevice(logical_address=3, type=TYPE_RECORDER)
    await create_cec_entity(hdmi_network, mock_hdmi_device)

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        service,
        {ATTR_ENTITY_ID: "media_player.hdmi_3"},
        blocking=True,
    )

    expect(mock_hdmi_device.send_command.call_count).to_equal(2)
    assert_key_press_release(mock_hdmi_device.send_command, dst=3, key=key)


@test.cases(
    test.case(
        "play",
        service=SERVICE_MEDIA_PLAY,
        key=KEY_PLAY,
        expected_state=STATE_PLAYING,
        xfail="The wrong feature is defined, should be PLAY, not PLAY_MEDIA",
    ),
    test.case("pause", service=SERVICE_MEDIA_PAUSE, key=KEY_PAUSE, expected_state=STATE_PAUSED),
    test.case("stop", service=SERVICE_MEDIA_STOP, key=KEY_STOP, expected_state=STATE_IDLE),
)
async def playback_services(
    service: str,
    key: int,
    expected_state: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test playback related commands."""
    hdmi_network = await create_hdmi_network({"platform": "media_player"})
    mock_hdmi_device = MockHDMIDevice(logical_address=3, type=TYPE_RECORDER)
    await create_cec_entity(hdmi_network, mock_hdmi_device)

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        service,
        {ATTR_ENTITY_ID: "media_player.hdmi_3"},
        blocking=True,
    )

    expect(mock_hdmi_device.send_command.call_count).to_equal(2)
    assert_key_press_release(mock_hdmi_device.send_command, dst=3, key=key)

    state = hass.states.get("media_player.hdmi_3")
    expect(state.state).to_equal(expected_state)


@test.xfail("PLAY feature isn't enabled")
async def play_pause_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test play pause service."""
    hdmi_network = await create_hdmi_network({"platform": "media_player"})
    mock_hdmi_device = MockHDMIDevice(
        logical_address=3, type=TYPE_RECORDER, status=STATUS_PLAY
    )
    await create_cec_entity(hdmi_network, mock_hdmi_device)

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_MEDIA_PLAY_PAUSE,
        {ATTR_ENTITY_ID: "media_player.hdmi_3"},
        blocking=True,
    )

    expect(mock_hdmi_device.send_command.call_count).to_equal(2)
    assert_key_press_release(mock_hdmi_device.send_command, dst=3, key=KEY_PAUSE)

    state = hass.states.get("media_player.hdmi_3")
    expect(state.state).to_equal(STATE_PAUSED)

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_MEDIA_PLAY_PAUSE,
        {ATTR_ENTITY_ID: "media_player.hdmi_3"},
        blocking=True,
    )

    expect(mock_hdmi_device.send_command.call_count).to_equal(4)
    assert_key_press_release(mock_hdmi_device.send_command, 1, dst=3, key=KEY_PLAY)


@test.cases(
    test.case("tv_power_off", type_id=TYPE_TV, update_data={"power_status": POWER_OFF}, expected_state=STATE_OFF),
    test.case("tv_power_3", type_id=TYPE_TV, update_data={"power_status": 3}, expected_state=STATE_OFF),
    test.case("tv_power_on", type_id=TYPE_TV, update_data={"power_status": POWER_ON}, expected_state=STATE_ON),
    test.case("tv_power_4", type_id=TYPE_TV, update_data={"power_status": 4}, expected_state=STATE_ON),
    test.case(
        "tv_power_on_play",
        type_id=TYPE_TV,
        update_data={"power_status": POWER_ON, "status": STATUS_PLAY},
        expected_state=STATE_ON,
    ),
    test.case(
        "recorder_off_play",
        type_id=TYPE_RECORDER,
        update_data={"power_status": POWER_OFF, "status": STATUS_PLAY},
        expected_state=STATE_OFF,
    ),
    test.case(
        "recorder_on_play",
        type_id=TYPE_RECORDER,
        update_data={"power_status": POWER_ON, "status": STATUS_PLAY},
        expected_state=STATE_PLAYING,
    ),
    test.case(
        "recorder_on_stop",
        type_id=TYPE_RECORDER,
        update_data={"power_status": POWER_ON, "status": STATUS_STOP},
        expected_state=STATE_IDLE,
    ),
    test.case(
        "recorder_on_still",
        type_id=TYPE_RECORDER,
        update_data={"power_status": POWER_ON, "status": STATUS_STILL},
        expected_state=STATE_PAUSED,
    ),
    test.case(
        "recorder_on_none",
        type_id=TYPE_RECORDER,
        update_data={"power_status": POWER_ON, "status": None},
        expected_state=STATE_UNKNOWN,
    ),
)
async def update_state(
    type_id: int,
    update_data: dict[str, Any],
    expected_state: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test state updates work as expected."""
    hdmi_network = await create_hdmi_network({"platform": "media_player"})
    mock_hdmi_device = MockHDMIDevice(logical_address=3, type=type_id)
    await create_cec_entity(hdmi_network, mock_hdmi_device)

    for att, val in update_data.items():
        setattr(mock_hdmi_device, att, val)
    await hass.async_block_till_done()

    state = hass.states.get("media_player.hdmi_3")
    expect(state.state).to_equal(expected_state)


@test.cases(
    test.case("power_off", data={"power_status": POWER_OFF}, expected_state=STATE_OFF),
    test.case("power_3", data={"power_status": 3}, expected_state=STATE_OFF),
    test.case(
        "tv_on",
        data={"power_status": POWER_ON, "type": TYPE_TV},
        expected_state=STATE_ON,
    ),
    test.case(
        "tv_4",
        data={"power_status": 4, "type": TYPE_TV},
        expected_state=STATE_ON,
    ),
    test.case(
        "tv_on_play",
        data={"power_status": POWER_ON, "type": TYPE_TV, "status": STATUS_PLAY},
        expected_state=STATE_ON,
    ),
    test.case(
        "recorder_off_play",
        data={"power_status": POWER_OFF, "type": TYPE_RECORDER, "status": STATUS_PLAY},
        expected_state=STATE_OFF,
    ),
    test.case(
        "recorder_on_play",
        data={"power_status": POWER_ON, "type": TYPE_RECORDER, "status": STATUS_PLAY},
        expected_state=STATE_PLAYING,
    ),
    test.case(
        "recorder_on_stop",
        data={"power_status": POWER_ON, "type": TYPE_RECORDER, "status": STATUS_STOP},
        expected_state=STATE_IDLE,
    ),
    test.case(
        "recorder_on_still",
        data={"power_status": POWER_ON, "type": TYPE_RECORDER, "status": STATUS_STILL},
        expected_state=STATE_PAUSED,
    ),
    test.case(
        "recorder_on_none",
        data={"power_status": POWER_ON, "type": TYPE_RECORDER, "status": None},
        expected_state=STATE_UNKNOWN,
    ),
)
async def starting_state(
    data: dict[str, Any],
    expected_state: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test starting states are set as expected."""
    hdmi_network = await create_hdmi_network({"platform": "media_player"})
    mock_hdmi_device = MockHDMIDevice(logical_address=3, **data)
    await create_cec_entity(hdmi_network, mock_hdmi_device)
    state = hass.states.get("media_player.hdmi_3")
    expect(state.state).to_equal(expected_state)


@test
async def unavailable_status(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test entity goes into unavailable status when expected."""
    hdmi_network = await create_hdmi_network({"platform": "media_player"})
    mock_hdmi_device = MockHDMIDevice(logical_address=3)
    await create_cec_entity(hdmi_network, mock_hdmi_device)

    hass.bus.async_fire(EVENT_HDMI_CEC_UNAVAILABLE)
    await hass.async_block_till_done()

    state = hass.states.get("media_player.hdmi_3")
    expect(state.state).to_equal(STATE_UNAVAILABLE)
