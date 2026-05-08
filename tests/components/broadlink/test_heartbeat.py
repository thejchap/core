"""Tryke skip stub for test_heartbeat.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def heartbeat_trigger_startup() -> None:
    """Stub for test_heartbeat_trigger_startup."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def heartbeat_ignore_oserror() -> None:
    """Stub for test_heartbeat_ignore_oserror."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def heartbeat_trigger_right_time() -> None:
    """Stub for test_heartbeat_trigger_right_time."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def heartbeat_do_not_trigger_before_time() -> None:
    """Stub for test_heartbeat_do_not_trigger_before_time."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def heartbeat_unload() -> None:
    """Stub for test_heartbeat_unload."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def heartbeat_do_not_unload() -> None:
    """Stub for test_heartbeat_do_not_unload."""

