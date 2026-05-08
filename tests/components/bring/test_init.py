"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_unload() -> None:
    """Stub for test_load_unload."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def init_failure() -> None:
    """Stub for test_init_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_not_ready_udpdate_failed() -> None:
    """Stub for test_config_entry_not_ready_udpdate_failed."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def activity_coordinator_errors() -> None:
    """Stub for test_activity_coordinator_errors."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_not_ready_auth_error() -> None:
    """Stub for test_config_entry_not_ready_auth_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def coordinator_skips_deactivated() -> None:
    """Stub for test_coordinator_skips_deactivated."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def purge_devices() -> None:
    """Stub for test_purge_devices."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def create_devices() -> None:
    """Stub for test_create_devices."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def coordinator_update_intervals() -> None:
    """Stub for test_coordinator_update_intervals."""

