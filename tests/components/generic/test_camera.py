"""Tryke skip stub for test_camera.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the generic.camera module imports cleanly."""
    from homeassistant.components.generic import camera  # noqa: PLC0415
    expect(camera).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def fetching_url() -> None:
    """Stub for test_fetching_url."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def image_caching() -> None:
    """Stub for test_image_caching."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def fetching_without_verify_ssl() -> None:
    """Stub for test_fetching_without_verify_ssl."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def fetching_url_with_verify_ssl() -> None:
    """Stub for test_fetching_url_with_verify_ssl."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def limit_refetch() -> None:
    """Stub for test_limit_refetch."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stream_source() -> None:
    """Stub for test_stream_source."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stream_source_error() -> None:
    """Stub for test_stream_source_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_alternative_options() -> None:
    """Stub for test_setup_alternative_options."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_stream_source() -> None:
    """Stub for test_no_stream_source."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def camera_content_type() -> None:
    """Stub for test_camera_content_type."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def timeout_cancelled() -> None:
    """Stub for test_timeout_cancelled."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def frame_interval_property() -> None:
    """Stub for test_frame_interval_property."""

