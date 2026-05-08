"""Test for Portainer services. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def services() -> None:
    """Stub for test_services (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def service_prune_images() -> None:
    """Stub for test_service_prune_images (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def service_validation_errors() -> None:
    """Stub for test_service_validation_errors (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def service_portainer_exceptions() -> None:
    """Stub for test_service_portainer_exceptions (port deferred)."""
