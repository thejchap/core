"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_registry_cleanup() -> None:
    """Stub for test_device_registry_cleanup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def subscription_setup() -> None:
    """Stub for test_subscription_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def subscription_setup_polling_disabled() -> None:
    """Stub for test_subscription_setup_polling_disabled."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_icons() -> None:
    """Stub for test_sensor_icons."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def minor_v1_v2_migration() -> None:
    """Stub for test_minor_v1_v2_migration."""

