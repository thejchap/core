"""Tryke skip stub for test_weather.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_weather.weather module imports cleanly."""
    from homeassistant.components.google_weather import weather  # noqa: PLC0415
    expect(weather).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def weather() -> None:
    """Stub for test_weather."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def availability() -> None:
    """Stub for test_availability."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def manual_update_entity() -> None:
    """Stub for test_manual_update_entity."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def condition() -> None:
    """Stub for test_condition."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def all_conditions_mapped() -> None:
    """Stub for test_all_conditions_mapped."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def forecast_service() -> None:
    """Stub for test_forecast_service."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def forecast_subscription() -> None:
    """Stub for test_forecast_subscription."""

