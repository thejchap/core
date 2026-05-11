"""Tests for the switchbot button platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("entity_id slugs need translations (button.test_name_light_sensor etc)")
async def art_frame_button_press() -> None:
    """Stub for test_art_frame_button_press (port deferred)."""

@test.skip("entity_id slugs need translations")
async def meter_pro_co2_sync_datetime_button() -> None:
    """Stub for test_meter_pro_co2_sync_datetime_button (port deferred)."""

@test.skip("entity_id slugs need translations")
async def meter_pro_co2_sync_datetime_button_with_timezone() -> None:
    """Stub for test_meter_pro_co2_sync_datetime_button_with_timezone (port deferred)."""

@test.skip("entity_id slugs need translations")
async def air_purifier_buttons() -> None:
    """Stub for test_air_purifier_buttons (port deferred)."""
