"""Tryke skip stub for test_subscriber.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_callbacks() -> None:
    """Stub for test_no_callbacks."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def empty_callbacks() -> None:
    """Stub for test_empty_callbacks."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_callbacks() -> None:
    """Stub for test_async_callbacks."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def long_async_callbacks() -> None:
    """Stub for test_long_async_callbacks."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def callbacks() -> None:
    """Stub for test_callbacks."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def subscribe_unsubscribe() -> None:
    """Stub for test_subscribe_unsubscribe."""

