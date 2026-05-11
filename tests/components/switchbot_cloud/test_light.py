"""Test for the Switchbot Light Entity. (tryke skip stub)."""

from tryke import expect, fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.switchbot_cloud.light module imports cleanly."""
    from homeassistant.components.switchbot_cloud import light  # noqa: PLC0415
    expect(light).not_.to_be(None)


@test.skip("conftest fixtures need migration to _fixtures.py")
async def coordinator_data_is_none() -> None:
    """Stub for test_coordinator_data_is_none (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def strip_light_turn_off() -> None:
    """Stub for test_strip_light_turn_off (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def rgbww_light_turn_off() -> None:
    """Stub for test_rgbww_light_turn_off (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def strip_light_turn_on() -> None:
    """Stub for test_strip_light_turn_on (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def rgbww_light_turn_on() -> None:
    """Stub for test_rgbww_light_turn_on (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def ceiling_light_turn_on() -> None:
    """Stub for test_ceiling_light_turn_on (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def ceiling_light_turn_off() -> None:
    """Stub for test_ceiling_light_turn_off (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def rgbic_neon_rope_light() -> None:
    """Stub for test_rgbic_neon_rope_light (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def candle_warmer_lamp() -> None:
    """Stub for test_candle_warmer_lamp (port deferred)."""
