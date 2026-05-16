"""Test the base functions of the media player."""

from http import HTTPStatus
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components import media_player
from homeassistant.components.media_player import (
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_FILTER_CLASSES,
    ATTR_MEDIA_SEARCH_QUERY,
    BrowseMedia,
    MediaClass,
    MediaPlayerEnqueue,
    MediaPlayerEntity,
    SearchMedia,
    SearchMediaQuery,
)
from homeassistant.components.media_player.const import (
    SERVICE_BROWSE_MEDIA,
    SERVICE_SEARCH_MEDIA,
)
from homeassistant.components.websocket_api import TYPE_RESULT
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockEntityPlatform
from tests.hass_fixtures import (
    ClientSessionGenerator,
    LogCapture,
    aioclient_mock as aioclient_mock_fixture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    hass_client_no_auth as hass_client_no_auth_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-level anchor fixture for Tryke's HookExecutor path."""
    return 0


@fixture
async def setup_homeassistant(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up the homeassistant integration."""
    await async_setup_component(hass, "homeassistant", {})


@test.cases(
    test.case("play", property_suffix="play"),
    test.case("pause", property_suffix="pause"),
    test.case("stop", property_suffix="stop"),
    test.case("seek", property_suffix="seek"),
    test.case("volume_set", property_suffix="volume_set"),
    test.case("volume_mute", property_suffix="volume_mute"),
    test.case("previous_track", property_suffix="previous_track"),
    test.case("next_track", property_suffix="next_track"),
    test.case("play_media", property_suffix="play_media"),
    test.case("select_source", property_suffix="select_source"),
    test.case("select_sound_mode", property_suffix="select_sound_mode"),
    test.case("clear_playlist", property_suffix="clear_playlist"),
    test.case("shuffle_set", property_suffix="shuffle_set"),
    test.case("grouping", property_suffix="grouping"),
)
def support_properties(
    property_suffix: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
) -> None:
    """Test support_*** properties explicitly."""
    all_features = media_player.MediaPlayerEntityFeature(653887)
    feature = media_player.MediaPlayerEntityFeature[property_suffix.upper()]

    entity1 = MediaPlayerEntity()
    entity1.hass = hass
    entity1.platform = MockEntityPlatform(hass)
    entity1._attr_supported_features = media_player.MediaPlayerEntityFeature(0)
    entity2 = MediaPlayerEntity()
    entity2.hass = hass
    entity2.platform = MockEntityPlatform(hass)
    entity2._attr_supported_features = all_features
    entity3 = MediaPlayerEntity()
    entity3.hass = hass
    entity3.platform = MockEntityPlatform(hass)
    entity3._attr_supported_features = feature
    entity4 = MediaPlayerEntity()
    entity4.hass = hass
    entity4.platform = MockEntityPlatform(hass)
    entity4._attr_supported_features = media_player.MediaPlayerEntityFeature(
        all_features - feature
    )

    expect(getattr(entity1, f"support_{property_suffix}")).to_be(False)
    expect(getattr(entity2, f"support_{property_suffix}")).to_be(True)
    expect(getattr(entity3, f"support_{property_suffix}")).to_be(True)
    expect(getattr(entity4, f"support_{property_suffix}")).to_be(False)


@test
async def get_image_http(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
) -> None:
    """Test get image via http command."""
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    state = hass.states.get("media_player.bedroom")
    expect("entity_picture_local" in state.attributes).to_be(False)

    client = await hass_client_no_auth()

    with patch(
        "homeassistant.components.media_player.MediaPlayerEntity.async_get_media_image",
        return_value=(b"image", "image/jpeg"),
    ):
        resp = await client.get(state.attributes["entity_picture"])
        content = await resp.read()

    expect(content).to_equal(b"image")


@test
async def get_image_http_remote(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
) -> None:
    """Test get image url via http command."""
    with patch(
        "homeassistant.components.media_player.MediaPlayerEntity."
        "media_image_remotely_accessible",
        return_value=True,
    ):
        await async_setup_component(
            hass, "media_player", {"media_player": {"platform": "demo"}}
        )
        await hass.async_block_till_done()

        state = hass.states.get("media_player.bedroom")
        expect("entity_picture_local" in state.attributes).to_be(True)

        client = await hass_client_no_auth()

        with patch(
            "homeassistant.components.media_player.MediaPlayerEntity."
            "async_get_media_image",
            return_value=(b"image", "image/jpeg"),
        ):
            resp = await client.get(state.attributes["entity_picture_local"])
            content = await resp.read()

        expect(content).to_equal(b"image")


@test
async def get_image_http_log_credentials_redacted(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test credentials are redacted when logging url when fetching image."""
    url = "http://vi:pass@example.com/default.jpg"
    with patch(
        "homeassistant.components.demo.media_player.DemoYoutubePlayer.media_image_url",
        url,
    ):
        await async_setup_component(
            hass, "media_player", {"media_player": {"platform": "demo"}}
        )
        await hass.async_block_till_done()

        state = hass.states.get("media_player.bedroom")
        expect("entity_picture_local" in state.attributes).to_be(False)

        aioclient_mock.get(url, exc=TimeoutError())

        client = await hass_client_no_auth()

        resp = await client.get(state.attributes["entity_picture"])

    expect(resp.status).to_equal(HTTPStatus.INTERNAL_SERVER_ERROR)
    expect(f"Error retrieving proxied image from {url}" in caplog.text).to_be(False)
    expect(
        (
            "Error retrieving proxied image from "
            f"{url.replace('pass', 'xxxxxxxx').replace('vi', 'xxxx')}"
        )
        in caplog.text
    ).to_be(True)


@test
async def get_async_get_browse_image(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test get browse image."""
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    entity_comp = hass.data.get("entity_components", {}).get("media_player")
    expect(entity_comp).to_be_truthy()

    player = entity_comp.get_entity("media_player.bedroom")
    expect(player).to_be_truthy()

    client = await hass_client_no_auth()

    with patch(
        "homeassistant.components.media_player.MediaPlayerEntity."
        "async_get_browse_image",
        return_value=(b"image", "image/jpeg"),
    ):
        url = player.get_browse_image_url("album", "abcd")
        resp = await client.get(url)
        content = await resp.read()

    expect(content).to_equal(b"image")


@test
async def media_browse(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test browsing media."""
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    with patch(
        "homeassistant.components.demo.media_player.DemoBrowsePlayer.async_browse_media",
        return_value=BrowseMedia(
            media_class=MediaClass.DIRECTORY,
            media_content_id="mock-id",
            media_content_type="mock-type",
            title="Mock Title",
            can_play=False,
            can_expand=True,
        ),
    ) as mock_browse_media:
        await client.send_json(
            {
                "id": 5,
                "type": "media_player/browse_media",
                "entity_id": "media_player.browse",
                "media_content_type": "album",
                "media_content_id": "abcd",
            }
        )

        msg = await client.receive_json()

    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    expect(msg["result"]).to_equal(
        {
            "title": "Mock Title",
            "media_class": "directory",
            "media_content_type": "mock-type",
            "media_content_id": "mock-id",
            "can_play": False,
            "can_expand": True,
            "can_search": False,
            "children_media_class": None,
            "thumbnail": None,
            "not_shown": 0,
            "children": [],
        }
    )
    expect(mock_browse_media.mock_calls[0][1]).to_equal(("album", "abcd"))

    with patch(
        "homeassistant.components.demo.media_player.DemoBrowsePlayer.async_browse_media",
        return_value={"bla": "yo"},
    ):
        await client.send_json(
            {
                "id": 6,
                "type": "media_player/browse_media",
                "entity_id": "media_player.browse",
            }
        )

        msg = await client.receive_json()

    expect(msg["id"]).to_equal(6)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    expect(msg["result"]).to_equal({"bla": "yo"})


@test
async def media_browse_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
) -> None:
    """Test browsing media using service call."""
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    with patch(
        "homeassistant.components.demo.media_player.DemoBrowsePlayer.async_browse_media",
        return_value=BrowseMedia(
            media_class=MediaClass.DIRECTORY,
            media_content_id="mock-id",
            media_content_type="mock-type",
            title="Mock Title",
            can_play=False,
            can_expand=True,
            children=[
                BrowseMedia(
                    media_class=MediaClass.ALBUM,
                    media_content_id="album1 content id",
                    media_content_type="album",
                    title="Album 1",
                    can_play=True,
                    can_expand=True,
                ),
                BrowseMedia(
                    media_class=MediaClass.ALBUM,
                    media_content_id="album2 content id",
                    media_content_type="album",
                    title="Album 2",
                    can_play=True,
                    can_expand=True,
                ),
            ],
        ),
    ) as mock_browse_media:
        result = await hass.services.async_call(
            "media_player",
            SERVICE_BROWSE_MEDIA,
            {
                ATTR_ENTITY_ID: "media_player.browse",
                ATTR_MEDIA_CONTENT_TYPE: "album",
                ATTR_MEDIA_CONTENT_ID: "title=Album*",
            },
            blocking=True,
            return_response=True,
        )

        mock_browse_media.assert_called_with(
            media_content_type="album", media_content_id="title=Album*"
        )
        browse_res: BrowseMedia = result["media_player.browse"]
        expect(browse_res.title).to_equal("Mock Title")
        expect(browse_res.media_class).to_equal("directory")
        expect(browse_res.media_content_type).to_equal("mock-type")
        expect(browse_res.media_content_id).to_equal("mock-id")
        expect(browse_res.can_play).to_be(False)
        expect(browse_res.can_expand).to_be(True)
        expect(len(browse_res.children)).to_equal(2)
        expect(browse_res.children[0].title).to_equal("Album 1")
        expect(browse_res.children[0].media_class).to_equal("album")
        expect(browse_res.children[0].media_content_id).to_equal("album1 content id")
        expect(browse_res.children[0].media_content_type).to_equal("album")
        expect(browse_res.children[1].title).to_equal("Album 2")
        expect(browse_res.children[1].media_class).to_equal("album")
        expect(browse_res.children[1].media_content_id).to_equal("album2 content id")
        expect(browse_res.children[1].media_content_type).to_equal("album")


@test
async def media_search(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test browsing media."""
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    with patch(
        "homeassistant.components.demo.media_player.DemoSearchPlayer.async_search_media",
        return_value=SearchMedia(
            result=[
                BrowseMedia(
                    media_class=MediaClass.DIRECTORY,
                    media_content_id="mock-id",
                    media_content_type="mock-type",
                    title="Mock Title",
                    can_play=False,
                    can_expand=True,
                )
            ]
        ),
    ) as mock_search_media:
        await client.send_json(
            {
                "id": 7,
                "type": "media_player/search_media",
                "entity_id": "media_player.search",
                "media_content_type": "album",
                "media_content_id": "abcd",
                "search_query": "query",
                "media_filter_classes": ["album"],
            }
        )

        msg = await client.receive_json()

    expect(msg["id"]).to_equal(7)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    expect(msg["result"]["result"]).to_equal(
        [
            {
                "title": "Mock Title",
                "media_class": "directory",
                "media_content_type": "mock-type",
                "media_content_id": "mock-id",
                "children_media_class": None,
                "can_play": False,
                "can_expand": True,
                "can_search": False,
                "thumbnail": None,
                "not_shown": 0,
                "children": [],
            }
        ]
    )
    expect(mock_search_media.mock_calls[0].kwargs["query"]).to_equal(
        SearchMediaQuery(
            search_query="query",
            media_content_type="album",
            media_content_id="abcd",
            media_filter_classes={MediaClass.ALBUM},
        )
    )


@test
async def media_search_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
) -> None:
    """Test browsing media."""
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()
    expected = [
        BrowseMedia(
            media_class=MediaClass.DIRECTORY,
            media_content_id="mock-id",
            media_content_type="mock-type",
            title="Mock Title",
            can_play=False,
            can_expand=True,
            children=[],
        )
    ]

    with patch(
        "homeassistant.components.demo.media_player.DemoSearchPlayer.async_search_media",
        return_value=SearchMedia(result=expected),
    ) as mock_search_media:
        result = await hass.services.async_call(
            "media_player",
            SERVICE_SEARCH_MEDIA,
            {
                ATTR_ENTITY_ID: "media_player.search",
                ATTR_MEDIA_CONTENT_TYPE: "album",
                ATTR_MEDIA_CONTENT_ID: "title=Album*",
                ATTR_MEDIA_SEARCH_QUERY: "query",
                ATTR_MEDIA_FILTER_CLASSES: ["album"],
            },
            blocking=True,
            return_response=True,
        )

    search_res: SearchMedia = result["media_player.search"]
    expect(search_res.version).to_equal(1)
    expect(search_res.result).to_equal(expected)
    expect(mock_search_media.mock_calls[0].kwargs["query"]).to_equal(
        SearchMediaQuery(
            search_query="query",
            media_content_type="album",
            media_content_id="title=Album*",
            media_filter_classes={MediaClass.ALBUM},
        )
    )


@test
async def group_members_available_when_off(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
) -> None:
    """Test that group_members are still available when media_player is off."""
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        "media_player",
        "turn_off",
        {ATTR_ENTITY_ID: "media_player.group"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("media_player.group")
    expect(state.state).to_equal(STATE_OFF)
    expect("group_members" in state.attributes).to_be(True)


@test.cases(
    test.case("bool_true", input=True, expected=MediaPlayerEnqueue.ADD),
    test.case("bool_false", input=False, expected=MediaPlayerEnqueue.PLAY),
    test.case("play", input="play", expected=MediaPlayerEnqueue.PLAY),
    test.case("next", input="next", expected=MediaPlayerEnqueue.NEXT),
    test.case("add", input="add", expected=MediaPlayerEnqueue.ADD),
    test.case("replace", input="replace", expected=MediaPlayerEnqueue.REPLACE),
)
async def enqueue_rewrite(
    input: Any,
    expected: MediaPlayerEnqueue,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
) -> None:
    """Test that group_members are still available when media_player is off."""
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    with patch(
        "homeassistant.components.demo.media_player.DemoYoutubePlayer.play_media",
    ) as mock_play_media:
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": "media_player.bedroom",
                "media_content_type": "music",
                "media_content_id": "1234",
                "enqueue": input,
            },
            blocking=True,
        )

    expect(len(mock_play_media.mock_calls)).to_equal(1)
    expect(mock_play_media.mock_calls[0][2]["enqueue"]).to_equal(expected)


@test
async def enqueue_alert_exclusive(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
) -> None:
    """Test that alert and enqueue cannot be used together."""
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": "media_player.bedroom",
                "media_content_type": "music",
                "media_content_id": "1234",
                "enqueue": "play",
                "announce": True,
            },
            blocking=True,
        )


@test.cases(
    test.case("braces", media_content_id="a/b c/d+e%2Fg{}"),
    test.case("pct2D", media_content_id="a/b c/d+e%2D"),
    test.case("pct2E", media_content_id="a/b c/d+e%2E"),
    test.case(
        "pool_party",
        media_content_id="2012-06%20Pool%20party%20%2F%20BBQ",
    ),
)
async def get_async_get_browse_image_quoting(
    media_content_id: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test get browse image using media_content_id with special characters.

    async_get_browse_image() should get called with the same string that is
    passed into get_browse_image_url().
    """
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    entity_comp = hass.data.get("entity_components", {}).get("media_player")
    expect(entity_comp).to_be_truthy()

    player = entity_comp.get_entity("media_player.bedroom")
    expect(player).to_be_truthy()

    client = await hass_client_no_auth()

    with patch(
        "homeassistant.components.media_player.MediaPlayerEntity."
        "async_get_browse_image",
    ) as mock_browse_image:
        url = player.get_browse_image_url("album", media_content_id)
        await client.get(url)
        mock_browse_image.assert_called_with("album", media_content_id, None)


@test
async def play_media_via_selector(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_homeassistant),
) -> None:
    """Test that play_media data under 'media' is remapped to top level keys for backward compatibility."""
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    with patch(
        "homeassistant.components.demo.media_player.DemoYoutubePlayer.play_media",
    ) as mock_play_media:
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": "media_player.bedroom",
                "media": {
                    "media_content_type": "music",
                    "media_content_id": "1234",
                },
            },
            blocking=True,
        )
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": "media_player.bedroom",
                "media_content_type": "music",
                "media_content_id": "1234",
            },
            blocking=True,
        )

    expect(len(mock_play_media.mock_calls)).to_equal(2)
    expect(mock_play_media.mock_calls[0].args).to_equal(
        mock_play_media.mock_calls[1].args
    )

    async with expect_raises_async(vol.Invalid, match="Play media cannot contain 'media'"):
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "media_content_id": "1234",
                "entity_id": "media_player.bedroom",
                "media": {
                    "media_content_type": "music",
                    "media_content_id": "1234",
                },
            },
            blocking=True,
        )
