"""Tryke skip stubs for test_sensor - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reading_measures_not_list() -> None:
    """Stub for test_reading_measures_not_list (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reading_no_unit() -> None:
    """Stub for test_reading_no_unit (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def ignore_invalid_latest_reading() -> None:
    """Stub for test_ignore_invalid_latest_reading (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reading_unavailable() -> None:
    """Stub for test_reading_unavailable (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def recover_from_failure() -> None:
    """Stub for test_recover_from_failure (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reading_is_sampled() -> None:
    """Stub for test_reading_is_sampled (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def multiple_readings_are_sampled() -> None:
    """Stub for test_multiple_readings_are_sampled (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def ignore_no_latest_reading() -> None:
    """Stub for test_ignore_no_latest_reading (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_measures() -> None:
    """Stub for test_no_measures (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def mark_existing_as_unavailable_if_no_latest() -> None:
    """Stub for test_mark_existing_as_unavailable_if_no_latest (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""


