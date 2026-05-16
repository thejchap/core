"""Test the UniFi Protect media_player platform."""

from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, expect, fixture, test
from uiprotect.data import AiPort, Camera
from uiprotect.exceptions import StreamError

from homeassistant.components.media_player import (
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_VOLUME_LEVEL,
)
from homeassistant.components.unifiprotect.const import DEFAULT_ATTRIBUTION
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    STATE_IDLE,
    STATE_PLAYING,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from . import patch_ufp_method
from ._fixtures import aiport, doorbell, ufp, unadopted_camera
from .utils import (
    MockUFPFixture,
    adopt_devices,
    assert_entity_counts,
    init_entry,
    remove_entities,
)

from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Force a HookExecutor for this module (tryke discovery quirk)."""
    return 0


@test
async def media_player_camera_remove(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorbell: Camera = Depends(doorbell),
) -> None:
    """Test removing and re-adding a light device."""
    await init_entry(hass, ufp, [doorbell])
    assert_entity_counts(hass, Platform.MEDIA_PLAYER, 1, 1)
    await remove_entities(hass, ufp, [doorbell])
    assert_entity_counts(hass, Platform.MEDIA_PLAYER, 0, 0)
    await adopt_devices(hass, ufp, [doorbell])
    assert_entity_counts(hass, Platform.MEDIA_PLAYER, 1, 1)


@test
async def media_player_setup(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp),
    doorbell: Camera = Depends(doorbell),
    unadopted_camera: Camera = Depends(unadopted_camera),
) -> None:
    """Test media_player entity setup."""
    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.MEDIA_PLAYER, 1, 1)

    unique_id = f"{doorbell.mac}_speaker"
    entity_id = "media_player.test_camera_speaker"

    entity = entity_registry.async_get(entity_id)
    expect(entity).to_be_truthy()
    expect(entity.unique_id).to_equal(unique_id)

    expected_volume = float(doorbell.speaker_settings.speaker_volume / 100)

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_IDLE)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)
    expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(136708)
    expect(state.attributes[ATTR_MEDIA_CONTENT_TYPE]).to_equal("music")
    expect(state.attributes[ATTR_MEDIA_VOLUME_LEVEL]).to_equal(expected_volume)


@test
async def media_player_update(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorbell: Camera = Depends(doorbell),
    unadopted_camera: Camera = Depends(unadopted_camera),
) -> None:
    """Test media_player entity update."""
    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.MEDIA_PLAYER, 1, 1)

    new_camera = doorbell.model_copy()
    new_camera.talkback_stream = Mock()
    new_camera.talkback_stream.is_running = True

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = new_camera

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get("media_player.test_camera_speaker")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_PLAYING)


@test
async def media_player_set_volume(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorbell: Camera = Depends(doorbell),
    unadopted_camera: Camera = Depends(unadopted_camera),
) -> None:
    """Test media_player entity test set_volume_level."""
    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.MEDIA_PLAYER, 1, 1)

    with patch_ufp_method(
        doorbell, "set_speaker_volume", new_callable=AsyncMock
    ) as mock_method:
        await hass.services.async_call(
            "media_player",
            "volume_set",
            {ATTR_ENTITY_ID: "media_player.test_camera_speaker", "volume_level": 0.5},
            blocking=True,
        )

        mock_method.assert_called_once_with(50)


@test
async def media_player_stop(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorbell: Camera = Depends(doorbell),
    unadopted_camera: Camera = Depends(unadopted_camera),
) -> None:
    """Test media_player entity test media_stop."""
    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.MEDIA_PLAYER, 1, 1)

    new_camera = doorbell.model_copy()
    new_camera.talkback_stream = AsyncMock()
    new_camera.talkback_stream.is_running = True

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = new_camera

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "media_player",
        "media_stop",
        {ATTR_ENTITY_ID: "media_player.test_camera_speaker"},
        blocking=True,
    )

    new_camera.talkback_stream.stop.assert_called_once()


@test
async def media_player_play(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorbell: Camera = Depends(doorbell),
    unadopted_camera: Camera = Depends(unadopted_camera),
) -> None:
    """Test media_player entity test play_media."""
    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.MEDIA_PLAYER, 1, 1)

    with (
        patch_ufp_method(doorbell, "stop_audio", new_callable=AsyncMock),
        patch_ufp_method(doorbell, "play_audio", new_callable=AsyncMock) as mock_play,
        patch_ufp_method(
            doorbell, "wait_until_audio_completes", new_callable=AsyncMock
        ) as mock_wait,
    ):
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                ATTR_ENTITY_ID: "media_player.test_camera_speaker",
                "media_content_id": "http://example.com/test.mp3",
                "media_content_type": "music",
            },
            blocking=True,
        )

        mock_play.assert_called_once_with("http://example.com/test.mp3", blocking=False)
        mock_wait.assert_called_once()


@test
async def media_player_play_media_source(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorbell: Camera = Depends(doorbell),
    unadopted_camera: Camera = Depends(unadopted_camera),
) -> None:
    """Test media_player entity test play_media."""
    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.MEDIA_PLAYER, 1, 1)

    with (
        patch_ufp_method(doorbell, "stop_audio", new_callable=AsyncMock),
        patch_ufp_method(doorbell, "play_audio", new_callable=AsyncMock) as mock_play,
        patch_ufp_method(
            doorbell, "wait_until_audio_completes", new_callable=AsyncMock
        ) as mock_wait,
        patch(
            "homeassistant.components.media_source.async_resolve_media",
            return_value=Mock(url="http://example.com/test.mp3"),
        ),
    ):
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                ATTR_ENTITY_ID: "media_player.test_camera_speaker",
                "media_content_id": "media-source://some_source/some_id",
                "media_content_type": "audio/mpeg",
            },
            blocking=True,
        )

        mock_play.assert_called_once_with("http://example.com/test.mp3", blocking=False)
        mock_wait.assert_called_once()


@test
async def media_player_play_invalid(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorbell: Camera = Depends(doorbell),
    unadopted_camera: Camera = Depends(unadopted_camera),
) -> None:
    """Test media_player entity test play_media, not music."""
    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.MEDIA_PLAYER, 1, 1)

    with patch_ufp_method(
        doorbell, "play_audio", new_callable=AsyncMock
    ) as mock_method:
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                "media_player",
                "play_media",
                {
                    ATTR_ENTITY_ID: "media_player.test_camera_speaker",
                    "media_content_id": "/test.png",
                    "media_content_type": "image",
                },
                blocking=True,
            )

        expect(mock_method.called).to_be_falsy()


@test
async def media_player_play_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorbell: Camera = Depends(doorbell),
    unadopted_camera: Camera = Depends(unadopted_camera),
) -> None:
    """Test media_player entity test play_media, not music."""
    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.MEDIA_PLAYER, 1, 1)

    with (
        patch_ufp_method(
            doorbell, "play_audio", new_callable=AsyncMock, side_effect=StreamError
        ) as mock_play,
        patch_ufp_method(
            doorbell, "wait_until_audio_completes", new_callable=AsyncMock
        ) as mock_wait,
    ):
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                "media_player",
                "play_media",
                {
                    ATTR_ENTITY_ID: "media_player.test_camera_speaker",
                    "media_content_id": "/test.mp3",
                    "media_content_type": "music",
                },
                blocking=True,
            )

        expect(mock_play.called).to_be_truthy()
        expect(mock_wait.called).to_be_falsy()


@test
async def aiport_no_media_player_entities(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    aiport: AiPort = Depends(aiport),
) -> None:
    """Test that AI Port devices do not create camera-specific media player entities."""
    await init_entry(hass, ufp, [aiport])

    # AI Port should not create any media player entities (speaker)
    assert_entity_counts(hass, Platform.MEDIA_PLAYER, 0, 0)
