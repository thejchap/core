"""Tryke skip-stubs for nest test_events (port deferred)."""
from tryke import test

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def event_zones() -> None:
    """Stub for test_event_zones (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def event() -> None:
    """Stub for test_event (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def camera_multiple_event() -> None:
    """Stub for test_camera_multiple_event (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def media_not_supported() -> None:
    """Stub for test_media_not_supported (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def unknown_event() -> None:
    """Stub for test_unknown_event (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def unknown_device_id() -> None:
    """Stub for test_unknown_device_id (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def event_message_without_device_event() -> None:
    """Stub for test_event_message_without_device_event (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def doorbell_event_thread() -> None:
    """Stub for test_doorbell_event_thread (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def doorbell_event_session_update() -> None:
    """Stub for test_doorbell_event_session_update (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def structure_update_event() -> None:
    """Stub for test_structure_update_event (port deferred)."""


