"""Tryke skip-stubs for nest test_device_trigger (port deferred)."""
from tryke import test

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def subscriber_automation() -> None:
    """Stub for test_subscriber_automation (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def get_triggers() -> None:
    """Stub for test_get_triggers (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def multiple_devices() -> None:
    """Stub for test_multiple_devices (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def triggers_for_invalid_device_id() -> None:
    """Stub for test_triggers_for_invalid_device_id (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def no_triggers() -> None:
    """Stub for test_no_triggers (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def fires_on_camera_motion() -> None:
    """Stub for test_fires_on_camera_motion (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def fires_on_camera_person() -> None:
    """Stub for test_fires_on_camera_person (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def fires_on_camera_sound() -> None:
    """Stub for test_fires_on_camera_sound (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def fires_on_doorbell_chime() -> None:
    """Stub for test_fires_on_doorbell_chime (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def trigger_for_wrong_device_id() -> None:
    """Stub for test_trigger_for_wrong_device_id (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def trigger_for_wrong_event_type() -> None:
    """Stub for test_trigger_for_wrong_event_type (port deferred)."""


