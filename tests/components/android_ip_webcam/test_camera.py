"""Test the Android IP Webcam camera."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.android_ip_webcam.const import DOMAIN
from homeassistant.components.camera import async_get_stream_source
from homeassistant.core import HomeAssistant

from ._fixtures import aioclient_mock_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test.cases(
    test.case(
        "with_auth",
        config={
            "host": "1.1.1.1",
            "port": 8080,
            "username": "user",
            "password": "pass",
        },
        expected_stream_source="rtsp://user:pass@1.1.1.1:8080/h264_aac.sdp",
    ),
    test.case(
        "no_auth",
        config={
            "host": "1.1.1.1",
            "port": 8080,
        },
        expected_stream_source="rtsp://1.1.1.1:8080/h264_aac.sdp",
    ),
)
async def camera_stream_source(
    config: dict[str, Any],
    expected_stream_source: str,
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _aiomock: None = Depends(aioclient_mock_fixture),
) -> None:
    """Test camera stream source."""
    entity_id = "camera.1_1_1_1"
    entry = MockConfigEntry(domain=DOMAIN, data=config)
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)

    stream_source = await async_get_stream_source(hass, entity_id)

    expect(stream_source).to_equal(expected_stream_source)
