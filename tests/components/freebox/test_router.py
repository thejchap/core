"""Tryke skip stub for test_router.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def is_json() -> None:
    """Stub for test_is_json."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_hosts_list_if_supported() -> None:
    """Stub for test_get_hosts_list_if_supported."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_hosts_list_if_supported_bridge() -> None:
    """Stub for test_get_hosts_list_if_supported_bridge."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_hosts_list_if_supported_bridge_error() -> None:
    """Stub for test_get_hosts_list_if_supported_bridge_error."""

