"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_entities() -> None:
    """Stub for test_sensor_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def newsletter_sensor_added_on_update() -> None:
    """Stub for test_newsletter_sensor_added_on_update."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def revenue_sensors_not_created_without_stripe() -> None:
    """Stub for test_revenue_sensors_not_created_without_stripe."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def newsletter_sensor_removed_when_stale() -> None:
    """Stub for test_newsletter_sensor_removed_when_stale."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def newsletter_sensor_removed_on_reload() -> None:
    """Stub for test_newsletter_sensor_removed_on_reload."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entities_unavailable_on_update_failure() -> None:
    """Stub for test_entities_unavailable_on_update_failure."""

