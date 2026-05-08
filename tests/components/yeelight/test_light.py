"""Tryke skip-stubs for test_light.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("yeelight: sibling test pending tryke port")
async def services() -> None:
    """Stub for test_services."""


@test.skip("yeelight: sibling test pending tryke port")
async def update_errors() -> None:
    """Stub for test_update_errors."""


@test.skip("yeelight: sibling test pending tryke port")
async def state_already_set_avoid_ratelimit() -> None:
    """Stub for test_state_already_set_avoid_ratelimit."""


@test.skip("yeelight: sibling test pending tryke port")
async def device_types() -> None:
    """Stub for test_device_types."""


@test.skip("yeelight: sibling test pending tryke port")
async def effects() -> None:
    """Stub for test_effects."""


@test.skip("yeelight: sibling test pending tryke port")
async def ambilight_with_nightlight_disabled() -> None:
    """Stub for test_ambilight_with_nightlight_disabled."""


@test.skip("yeelight: sibling test pending tryke port")
async def state_fails_to_update_triggers_update() -> None:
    """Stub for test_state_fails_to_update_triggers_update."""
