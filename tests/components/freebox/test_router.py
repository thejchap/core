"""Tryke skip stub for test_router.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the freebox.router module imports cleanly."""
    from homeassistant.components.freebox import router  # noqa: PLC0415
    expect(router).not_.to_be(None)


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

