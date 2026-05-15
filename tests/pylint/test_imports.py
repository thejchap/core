"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def good_import() -> None:
    """Stub for test_good_import (port deferred)."""

@test.skip("pending tryke port")
async def bad_import() -> None:
    """Stub for test_bad_import (port deferred)."""

@test.skip("pending tryke port")
async def good_root_import() -> None:
    """Stub for test_good_root_import (port deferred)."""

@test.skip("pending tryke port")
async def bad_root_import() -> None:
    """Stub for test_bad_root_import (port deferred)."""

@test.skip("pending tryke port")
async def bad_namespace_import() -> None:
    """Stub for test_bad_namespace_import (port deferred)."""

@test.skip("pending tryke port")
async def domain_alias() -> None:
    """Stub for test_domain_alias (port deferred)."""
