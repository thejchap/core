"""Tryke skip-stubs for test_device_trigger.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def triggers() -> None:
    """Stub for test_triggers."""


@test.skip("zha: sibling test pending tryke port")
async def no_triggers() -> None:
    """Stub for test_no_triggers."""


@test.skip("zha: sibling test pending tryke port")
async def if_fires_on_event() -> None:
    """Stub for test_if_fires_on_event."""


@test.skip("zha: sibling test pending tryke port")
async def device_offline_fires() -> None:
    """Stub for test_device_offline_fires."""


@test.skip("zha: sibling test pending tryke port")
async def exception_no_triggers() -> None:
    """Stub for test_exception_no_triggers."""


@test.skip("zha: sibling test pending tryke port")
async def exception_bad_trigger() -> None:
    """Stub for test_exception_bad_trigger."""


@test.skip("zha: sibling test pending tryke port")
async def validate_trigger_config_missing_info() -> None:
    """Stub for test_validate_trigger_config_missing_info."""


@test.skip("zha: sibling test pending tryke port")
async def validate_trigger_config_unloaded_bad_info() -> None:
    """Stub for test_validate_trigger_config_unloaded_bad_info."""
