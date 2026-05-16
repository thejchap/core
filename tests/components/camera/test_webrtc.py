"""Test camera WebRTC."""

from typing import Any
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test
from webrtc_models import RTCIceCandidate, RTCIceCandidateInit, RTCIceServer

from homeassistant.components.camera import (
    Camera,
    CameraWebRTCProvider,
    StreamType,
    WebRTCAnswer,
    WebRTCCandidate,
    WebRTCError,
    WebRTCMessage,
    WebRTCSendMessage,
    async_register_webrtc_provider,
    get_camera_from_entity_id,
)
from homeassistant.components.web_rtc import async_register_ice_servers
from homeassistant.components.websocket_api import TYPE_RESULT
from homeassistant.core import HomeAssistant, callback
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.setup import async_setup_component

from ._fixtures import (
    mock_camera,
    mock_stream_source,
    mock_test_webrtc_cameras,
    register_test_provider,
    setup_homeassistant,
)
from .common import STREAM_SOURCE, WEBRTC_ANSWER, SomeTestProvider

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import WebSocketGenerator

WEBRTC_OFFER = "v=0\r\n"
HLS_STREAM_SOURCE = "http://127.0.0.1/example.m3u"
TEST_INTEGRATION_DOMAIN = "test"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


class Go2RTCProvider(SomeTestProvider):
    """go2rtc provider."""

    @property
    def domain(self) -> str:
        """Return the integration domain of the provider."""
        return "go2rtc"


@test
async def async_register_webrtc_provider_test(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    _mock_stream_source: Mock = Depends(mock_stream_source),
) -> None:
    """Test registering a WebRTC provider."""
    camera = get_camera_from_entity_id(hass, "camera.demo_camera")
    expect(camera.camera_capabilities.frontend_stream_types).to_equal({StreamType.HLS})

    provider = SomeTestProvider()
    unregister = async_register_webrtc_provider(hass, provider)
    await hass.async_block_till_done()

    expect(camera.camera_capabilities.frontend_stream_types).to_equal(
        {StreamType.HLS, StreamType.WEB_RTC}
    )

    provider._is_supported = False
    await camera.async_refresh_providers()

    expect(camera.camera_capabilities.frontend_stream_types).to_equal({StreamType.HLS})

    provider._is_supported = True
    await camera.async_refresh_providers()
    expect(camera.camera_capabilities.frontend_stream_types).to_equal(
        {StreamType.HLS, StreamType.WEB_RTC}
    )

    unregister()
    await hass.async_block_till_done()

    expect(camera.camera_capabilities.frontend_stream_types).to_equal({StreamType.HLS})


@test
async def async_register_webrtc_provider_twice_test(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    _mock_stream_source: Mock = Depends(mock_stream_source),
    register_test_provider: SomeTestProvider = Depends(register_test_provider),
) -> None:
    """Test registering a WebRTC provider twice should raise."""
    async with expect_raises_async(ValueError, match="Provider already registered"):
        async_register_webrtc_provider(hass, register_test_provider)


@test
async def async_register_webrtc_provider_camera_not_loaded_test(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test registering a WebRTC provider when camera is not loaded."""
    async with expect_raises_async(ValueError, match="Unexpected state, camera not loaded"):
        async_register_webrtc_provider(hass, SomeTestProvider())


@test
async def ws_get_client_config(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test get WebRTC client config."""
    await async_setup_component(hass, "camera", {})

    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {"type": "camera/webrtc/get_client_config", "entity_id": "camera.async"}
    )
    msg = await client.receive_json()

    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    expect(msg["result"]).to_equal(
        {
            "configuration": {
                "iceServers": [
                    {
                        "urls": [
                            "stun:stun.home-assistant.io:3478",
                            "stun:stun.home-assistant.io:80",
                        ]
                    },
                ],
            },
        }
    )

    @callback
    def get_ice_server() -> list[RTCIceServer]:
        return [
            RTCIceServer(
                urls=["stun:example2.com", "turn:example2.com"],
                username="user",
                credential="pass",
            )
        ]

    async_register_ice_servers(hass, get_ice_server)

    await client.send_json_auto_id(
        {"type": "camera/webrtc/get_client_config", "entity_id": "camera.async"}
    )
    msg = await client.receive_json()

    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    expect(msg["result"]).to_equal(
        {
            "configuration": {
                "iceServers": [
                    {
                        "urls": [
                            "stun:stun.home-assistant.io:3478",
                            "stun:stun.home-assistant.io:80",
                        ]
                    },
                    {
                        "urls": ["stun:example2.com", "turn:example2.com"],
                        "username": "user",
                        "credential": "pass",
                    },
                ],
            },
        }
    )


@test
async def ws_get_client_config_custom_config(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test get WebRTC client config."""
    await async_process_ha_core_config(
        hass,
        {"webrtc": {"ice_servers": [{"url": "stun:custom_stun_server:3478"}]}},
    )

    await async_setup_component(hass, "camera", {})

    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {"type": "camera/webrtc/get_client_config", "entity_id": "camera.async"}
    )
    msg = await client.receive_json()

    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    expect(msg["result"]).to_equal(
        {
            "configuration": {
                "iceServers": [{"urls": ["stun:custom_stun_server:3478"]}]
            },
        }
    )


@test
async def ws_get_client_config_no_rtc_camera(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test get WebRTC client config."""
    await async_setup_component(hass, "camera", {})

    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {"type": "camera/webrtc/get_client_config", "entity_id": "camera.demo_camera"}
    )
    msg = await client.receive_json()

    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_falsy()
    expect(msg["error"]).to_equal(
        {
            "code": "webrtc_get_client_config_failed",
            "message": "Camera does not support WebRTC, frontend_stream_types={<StreamType.HLS: 'hls'>}",
        }
    )


async def provide_webrtc_answer(stream_source: str, offer: str, stream_id: str) -> str:
    """Simulate an rtsp to webrtc provider."""
    assert stream_source == STREAM_SOURCE
    assert offer == WEBRTC_OFFER
    return WEBRTC_ANSWER


@test
async def websocket_webrtc_offer(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test initiating a WebRTC stream with offer and answer."""
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/offer",
            "entity_id": "camera.async",
            "offer": WEBRTC_OFFER,
        }
    )
    response = await client.receive_json()
    expect(response["type"]).to_equal(TYPE_RESULT)
    expect(response["success"]).to_be_truthy()
    subscription_id = response["id"]

    response = await client.receive_json()
    expect(response["id"]).to_equal(subscription_id)
    expect(response["type"]).to_equal("event")
    expect(response["event"]["type"]).to_equal("session")

    response = await client.receive_json()
    expect(response["id"]).to_equal(subscription_id)
    expect(response["type"]).to_equal("event")
    expect(response["event"]).to_equal(
        {
            "type": "answer",
            "answer": WEBRTC_ANSWER,
        }
    )

    await client.send_json_auto_id(
        {
            "type": "unsubscribe_events",
            "subscription": subscription_id,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()


async def _test_websocket_webrtc_offer_webrtc_provider(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    register_test_provider: SomeTestProvider,
    message: WebRTCMessage,
    expected_frontend_message: dict[str, Any],
) -> None:
    """Test initiating a WebRTC stream with a webrtc provider."""
    client = await hass_ws_client(hass)
    with (
        patch.object(
            register_test_provider, "async_handle_async_webrtc_offer", autospec=True
        ) as mock_async_handle_async_webrtc_offer,
        patch.object(
            register_test_provider, "async_close_session", autospec=True
        ) as mock_async_close_session,
    ):
        await client.send_json_auto_id(
            {
                "type": "camera/webrtc/offer",
                "entity_id": "camera.demo_camera",
                "offer": WEBRTC_OFFER,
            }
        )
        response = await client.receive_json()
        expect(response["type"]).to_equal(TYPE_RESULT)
        expect(response["success"]).to_be_truthy()
        subscription_id = response["id"]
        mock_async_handle_async_webrtc_offer.assert_called_once()
        expect(mock_async_handle_async_webrtc_offer.call_args[0][1]).to_equal(
            WEBRTC_OFFER
        )
        send_message: WebRTCSendMessage = (
            mock_async_handle_async_webrtc_offer.call_args[0][3]
        )

        response = await client.receive_json()
        expect(response["id"]).to_equal(subscription_id)
        expect(response["type"]).to_equal("event")
        expect(response["event"]["type"]).to_equal("session")
        session_id = response["event"]["session_id"]

        send_message(message)

        response = await client.receive_json()
        expect(response["id"]).to_equal(subscription_id)
        expect(response["type"]).to_equal("event")
        expect(response["event"]).to_equal(expected_frontend_message)

        await client.send_json_auto_id(
            {
                "type": "unsubscribe_events",
                "subscription": subscription_id,
            }
        )
        msg = await client.receive_json()
        expect(msg["success"]).to_be_truthy()
        mock_async_close_session.assert_called_once_with(session_id)


@test
async def websocket_webrtc_offer_webrtc_provider_deprecated(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_stream_source: Mock = Depends(mock_stream_source),
    _mock_camera: None = Depends(mock_camera),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    register_test_provider: SomeTestProvider = Depends(register_test_provider),
) -> None:
    """Test initiating a WebRTC stream with a webrtc provider with the deprecated class."""
    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Using RTCIceCandidate is deprecated. Use RTCIceCandidateInit instead",
        )
        await _test_websocket_webrtc_offer_webrtc_provider(
            hass,
            hass_ws_client,
            register_test_provider,
            WebRTCCandidate(RTCIceCandidate("candidate")),
            {"type": "candidate", "candidate": {"candidate": "candidate"}},
        )


@test
async def websocket_webrtc_offer_webrtc_provider_candidate(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_stream_source: Mock = Depends(mock_stream_source),
    _mock_camera: None = Depends(mock_camera),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    register_test_provider: SomeTestProvider = Depends(register_test_provider),
) -> None:
    """Test initiating a WebRTC stream with a webrtc provider — candidate message."""
    await _test_websocket_webrtc_offer_webrtc_provider(
        hass,
        hass_ws_client,
        register_test_provider,
        WebRTCCandidate(RTCIceCandidateInit("candidate")),
        {
            "type": "candidate",
            "candidate": {"candidate": "candidate", "sdpMLineIndex": 0},
        },
    )


@test
async def websocket_webrtc_offer_webrtc_provider_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_stream_source: Mock = Depends(mock_stream_source),
    _mock_camera: None = Depends(mock_camera),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    register_test_provider: SomeTestProvider = Depends(register_test_provider),
) -> None:
    """Test initiating a WebRTC stream with a webrtc provider — error message."""
    await _test_websocket_webrtc_offer_webrtc_provider(
        hass,
        hass_ws_client,
        register_test_provider,
        WebRTCError("webrtc_offer_failed", "error"),
        {"type": "error", "code": "webrtc_offer_failed", "message": "error"},
    )


@test
async def websocket_webrtc_offer_webrtc_provider_answer(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_stream_source: Mock = Depends(mock_stream_source),
    _mock_camera: None = Depends(mock_camera),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    register_test_provider: SomeTestProvider = Depends(register_test_provider),
) -> None:
    """Test initiating a WebRTC stream with a webrtc provider — answer message."""
    await _test_websocket_webrtc_offer_webrtc_provider(
        hass,
        hass_ws_client,
        register_test_provider,
        WebRTCAnswer("answer"),
        {"type": "answer", "answer": "answer"},
    )


@test
async def websocket_webrtc_offer_invalid_entity(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test WebRTC with a camera entity that does not exist."""
    await async_setup_component(hass, "camera", {})
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/offer",
            "entity_id": "camera.does_not_exist",
            "offer": WEBRTC_OFFER,
        }
    )
    response = await client.receive_json()

    expect(response["type"]).to_equal(TYPE_RESULT)
    expect(response["success"]).to_be_falsy()
    expect(response["error"]).to_equal(
        {
            "code": "home_assistant_error",
            "message": "Camera not found",
        }
    )


@test
async def websocket_webrtc_offer_missing_offer(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test WebRTC stream with missing required fields."""
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/offer",
            "entity_id": "camera.demo_camera",
        }
    )
    response = await client.receive_json()

    expect(response["type"]).to_equal(TYPE_RESULT)
    expect(response["success"]).to_be_falsy()
    expect(response["error"]["code"]).to_equal("invalid_format")


@test
async def websocket_webrtc_offer_invalid_stream_type(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test WebRTC initiating for a camera with a different stream_type."""
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/offer",
            "entity_id": "camera.demo_camera",
            "offer": WEBRTC_OFFER,
        }
    )
    response = await client.receive_json()

    expect(response["type"]).to_equal(TYPE_RESULT)
    expect(response["success"]).to_be_falsy()
    expect(response["error"]).to_equal(
        {
            "code": "webrtc_offer_failed",
            "message": "Camera does not support WebRTC, frontend_stream_types={<StreamType.HLS: 'hls'>}",
        }
    )


async def _run_ws_webrtc_candidate(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    frontend_candidate: dict[str, Any],
    expected_candidate: RTCIceCandidateInit,
) -> None:
    client = await hass_ws_client(hass)
    session_id = "session_id"
    with patch.object(
        get_camera_from_entity_id(hass, "camera.async"), "async_on_webrtc_candidate"
    ) as mock_on_webrtc_candidate:
        await client.send_json_auto_id(
            {
                "type": "camera/webrtc/candidate",
                "entity_id": "camera.async",
                "session_id": session_id,
                "candidate": frontend_candidate,
            }
        )
        response = await client.receive_json()
        expect(response["type"]).to_equal(TYPE_RESULT)
        expect(response["success"]).to_be_truthy()
        mock_on_webrtc_candidate.assert_called_once_with(session_id, expected_candidate)


@test
async def ws_webrtc_candidate(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test ws webrtc candidate command."""
    await _run_ws_webrtc_candidate(
        hass,
        hass_ws_client,
        {"candidate": "candidate", "sdpMLineIndex": 0},
        RTCIceCandidateInit("candidate"),
    )


@test
async def ws_webrtc_candidate_mline_index(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test ws webrtc candidate command with sdpMLineIndex."""
    await _run_ws_webrtc_candidate(
        hass,
        hass_ws_client,
        {"candidate": "candidate", "sdpMLineIndex": 1},
        RTCIceCandidateInit("candidate", sdp_m_line_index=1),
    )


@test
async def ws_webrtc_candidate_mid(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test ws webrtc candidate command with sdpMid."""
    await _run_ws_webrtc_candidate(
        hass,
        hass_ws_client,
        {"candidate": "candidate", "sdpMid": "1"},
        RTCIceCandidateInit("candidate", sdp_mid="1"),
    )


async def _run_ws_webrtc_candidate_invalid(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    message: dict,
    expected_error_msg: str,
) -> None:
    client = await hass_ws_client(hass)
    with patch("homeassistant.components.camera.Camera.async_on_webrtc_candidate"):
        await client.send_json_auto_id(
            {
                "type": "camera/webrtc/candidate",
                "entity_id": "camera.async",
                "session_id": "session_id",
                "candidate": message,
            }
        )
        response = await client.receive_json()

    expect(response["type"]).to_equal(TYPE_RESULT)
    expect(response["success"]).to_be_falsy()
    expect(response["error"]).to_equal(
        {
            "code": "invalid_format",
            "message": expected_error_msg,
        }
    )


@test
async def ws_webrtc_candidate_invalid_candidate_missing(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test ws WebRTC candidate invalid — candidate missing."""
    await _run_ws_webrtc_candidate_invalid(
        hass,
        hass_ws_client,
        {"sdpMLineIndex": 0},
        (
            'Field "candidate" of type str is missing in RTCIceCandidateInit instance'
            " for dictionary value @ data['candidate']. Got {'sdpMLineIndex': 0}"
        ),
    )


@test
async def ws_webrtc_candidate_invalid_sdp_mline_negative(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test ws WebRTC candidate invalid — sdpMLineIndex < 0."""
    await _run_ws_webrtc_candidate_invalid(
        hass,
        hass_ws_client,
        {"candidate": "candidate", "sdpMLineIndex": -1},
        (
            "sdpMLineIndex must be greater than or equal to 0 for dictionary value @ "
            "data['candidate']. Got {'candidate': 'candidate', 'sdpMLineIndex': -1}"
        ),
    )


@test
async def ws_webrtc_candidate_not_supported(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test ws webrtc candidate command is raising if not supported."""
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/candidate",
            "entity_id": "camera.async_no_candidate",
            "session_id": "session_id",
            "candidate": {"candidate": "candidate"},
        }
    )
    response = await client.receive_json()
    expect(response["type"]).to_equal(TYPE_RESULT)
    expect(response["success"]).to_be_falsy()
    expect(response["error"]).to_equal(
        {
            "code": "home_assistant_error",
            "message": "Cannot handle WebRTC candidate",
        }
    )


@test
async def ws_webrtc_candidate_webrtc_provider(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    _mock_stream_source: Mock = Depends(mock_stream_source),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    register_test_provider: SomeTestProvider = Depends(register_test_provider),
) -> None:
    """Test ws webrtc candidate command with WebRTC provider."""
    with patch.object(
        register_test_provider, "async_on_webrtc_candidate"
    ) as mock_on_webrtc_candidate:
        client = await hass_ws_client(hass)
        session_id = "session_id"
        candidate = "candidate"
        await client.send_json_auto_id(
            {
                "type": "camera/webrtc/candidate",
                "entity_id": "camera.demo_camera",
                "session_id": session_id,
                "candidate": {"candidate": candidate, "sdpMLineIndex": 1},
            }
        )
        response = await client.receive_json()
        expect(response["type"]).to_equal(TYPE_RESULT)
        expect(response["success"]).to_be_truthy()
        mock_on_webrtc_candidate.assert_called_once_with(
            session_id, RTCIceCandidateInit(candidate, sdp_m_line_index=1)
        )


@test
async def ws_webrtc_candidate_invalid_entity(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test ws WebRTC candidate command with a camera entity that does not exist."""
    await async_setup_component(hass, "camera", {})
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/candidate",
            "entity_id": "camera.does_not_exist",
            "session_id": "session_id",
            "candidate": {"candidate": "candidate"},
        }
    )
    response = await client.receive_json()

    expect(response["type"]).to_equal(TYPE_RESULT)
    expect(response["success"]).to_be_falsy()
    expect(response["error"]).to_equal(
        {
            "code": "home_assistant_error",
            "message": "Camera not found",
        }
    )


@test
async def ws_webrtc_canidate_missing_candidate(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test ws WebRTC candidate command with missing required fields."""
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/candidate",
            "entity_id": "camera.async",
            "session_id": "session_id",
        }
    )
    response = await client.receive_json()

    expect(response["type"]).to_equal(TYPE_RESULT)
    expect(response["success"]).to_be_falsy()
    expect(response["error"]["code"]).to_equal("invalid_format")


@test
async def ws_webrtc_candidate_invalid_stream_type(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test ws WebRTC candidate command for a camera with a different stream_type."""
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/candidate",
            "entity_id": "camera.demo_camera",
            "session_id": "session_id",
            "candidate": {"candidate": "candidate"},
        }
    )
    response = await client.receive_json()

    expect(response["type"]).to_equal(TYPE_RESULT)
    expect(response["success"]).to_be_falsy()
    expect(response["error"]).to_equal(
        {
            "code": "webrtc_candidate_failed",
            "message": "Camera does not support WebRTC, frontend_stream_types={<StreamType.HLS: 'hls'>}",
        }
    )


@test
async def webrtc_provider_optional_interface(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test optional interface for WebRTC provider."""

    class OnlyRequiredInterfaceProvider(CameraWebRTCProvider):
        """Test provider."""

        @property
        def domain(self) -> str:
            """Return the domain of the provider."""
            return "test"

        @callback
        def async_is_supported(self, stream_source: str) -> bool:
            """Determine if the provider supports the stream source."""
            return True

        async def async_handle_async_webrtc_offer(
            self,
            camera: Camera,
            offer_sdp: str,
            session_id: str,
            send_message: WebRTCSendMessage,
        ) -> None:
            """Handle the WebRTC offer and return the answer via the provided callback."""
            send_message(WebRTCAnswer(answer="answer"))

        async def async_on_webrtc_candidate(
            self, session_id: str, candidate: RTCIceCandidateInit
        ) -> None:
            """Handle the WebRTC candidate."""

    provider = OnlyRequiredInterfaceProvider()
    expect(provider.async_is_supported("stream_source")).to_be(True)
    await provider.async_handle_async_webrtc_offer(
        Mock(), "offer_sdp", "session_id", Mock()
    )
    await provider.async_on_webrtc_candidate(
        "session_id", RTCIceCandidateInit("candidate")
    )
    provider.async_close_session("session_id")
