"""Go2rtc utility function tests."""

from unittest.mock import Mock

from tryke import expect, test

from homeassistant.components.camera import Camera
from homeassistant.components.go2rtc.util import get_camera_identifier


@test.cases(
    test.case(
        "prefer_unique_id",
        unique_id="unique123",
        entity_id="camera.test",
        expected="test_unique123",
    ),
    test.case(
        "fallback_entity_id",
        unique_id=None,
        entity_id="camera.test",
        expected="camera.test",
    ),
    test.case(
        "safe_chars",
        unique_id="abc-def_ghi.123",
        entity_id="camera.test",
        expected="test_abc-def_ghi.123",
    ),
    test.case(
        "hash",
        unique_id="cam#1",
        entity_id="camera.test",
        expected="test_cam%231",
    ),
    test.case(
        "colon",
        unique_id="cam:1",
        entity_id="camera.test",
        expected="test_cam%3A1",
    ),
    test.case(
        "slash",
        unique_id="cam/1",
        entity_id="camera.test",
        expected="test_cam%2F1",
    ),
    test.case(
        "question",
        unique_id="cam?1",
        entity_id="camera.test",
        expected="test_cam%3F1",
    ),
    test.case(
        "ampersand",
        unique_id="cam&1",
        entity_id="camera.test",
        expected="test_cam%261",
    ),
    test.case(
        "equals",
        unique_id="cam=1",
        entity_id="camera.test",
        expected="test_cam%3D1",
    ),
    test.case(
        "percent",
        unique_id="cam%1",
        entity_id="camera.test",
        expected="test_cam%251",
    ),
    test.case(
        "space",
        unique_id="cam 1",
        entity_id="camera.test",
        expected="test_cam%201",
    ),
    test.case(
        "at",
        unique_id="cam@1",
        entity_id="camera.test",
        expected="test_cam%401",
    ),
    test.case(
        "underscore",
        unique_id="cam_1",
        entity_id="camera.test",
        expected="test_cam_1",
    ),
    test.case(
        "encoded_hash",
        unique_id="cam%231",
        entity_id="camera.test",
        expected="test_cam%25231",
    ),
    test.case(
        "non_ascii",
        unique_id="cam€1",
        entity_id="camera.test",
        expected="test_cam%E2%82%AC1",
    ),
)
def get_camera_identifier_sanitizes(
    *, unique_id: str | None, entity_id: str, expected: str
) -> None:
    """Test get_camera_identifier sanitizes and prefers unique_id."""
    camera = Mock(spec_set=Camera)
    camera.platform.platform_name = "test"
    camera.unique_id = unique_id
    camera.entity_id = entity_id
    expect(get_camera_identifier(camera)).to_equal(expected)
