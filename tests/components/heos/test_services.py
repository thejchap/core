"""Tryke skip stub for test_services.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sign_in() -> None:
    """Stub for test_sign_in."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sign_in_failed() -> None:
    """Stub for test_sign_in_failed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sign_in_unknown_error() -> None:
    """Stub for test_sign_in_unknown_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sign_in_not_loaded_raises() -> None:
    """Stub for test_sign_in_not_loaded_raises."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sign_out() -> None:
    """Stub for test_sign_out."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sign_out_not_loaded_raises() -> None:
    """Stub for test_sign_out_not_loaded_raises."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sign_out_unknown_error() -> None:
    """Stub for test_sign_out_unknown_error."""

