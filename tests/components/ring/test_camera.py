"""The tests for the Ring switch platform. (tryke skip stub)."""

from tryke import expect, fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.ring.camera module imports cleanly."""
    from homeassistant.components.ring import camera  # noqa: PLC0415
    expect(camera).not_.to_be(None)


@test.skip("syrupy snapshot")
async def states() -> None:
    """Stub for test_states (port deferred)."""

@test.skip("syrupy snapshot")
async def camera_motion_detection_state_reports_correctly() -> None:
    """Stub for test_camera_motion_detection_state_reports_correctly (port deferred)."""

@test.skip("syrupy snapshot")
async def camera_motion_detection_can_be_turned_on_and_off() -> None:
    """Stub for test_camera_motion_detection_can_be_turned_on_and_off (port deferred)."""

@test.skip("syrupy snapshot")
async def camera_motion_detection_not_supported() -> None:
    """Stub for test_camera_motion_detection_not_supported (port deferred)."""

@test.skip("syrupy snapshot")
async def motion_detection_errors_when_turned_on() -> None:
    """Stub for test_motion_detection_errors_when_turned_on (port deferred)."""

@test.skip("syrupy snapshot")
async def camera_handle_mjpeg_stream() -> None:
    """Stub for test_camera_handle_mjpeg_stream (port deferred)."""

@test.skip("syrupy snapshot")
async def camera_image() -> None:
    """Stub for test_camera_image (port deferred)."""

@test.skip("syrupy snapshot")
async def camera_live_view_no_subscription() -> None:
    """Stub for test_camera_live_view_no_subscription (port deferred)."""

@test.skip("syrupy snapshot")
async def camera_stream_attributes() -> None:
    """Stub for test_camera_stream_attributes (port deferred)."""

@test.skip("syrupy snapshot")
async def camera_webrtc() -> None:
    """Stub for test_camera_webrtc (port deferred)."""
