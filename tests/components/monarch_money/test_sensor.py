"""Test sensors."""

from tryke import test


@test.skip("snapshot-based test (snapshot_platform) — needs pytest --snapshot-update support in shim")
async def all_entities() -> None:
    """Stub for test_all_entities (port deferred)."""
