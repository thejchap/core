"""Tryke skip stub for test_services.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def read_file() -> None:
    """Stub for test_read_file."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def read_file_disallowed_path() -> None:
    """Stub for test_read_file_disallowed_path."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def read_file_bad_encoding_option() -> None:
    """Stub for test_read_file_bad_encoding_option."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def read_file_decoding_error() -> None:
    """Stub for test_read_file_decoding_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def read_file_dne() -> None:
    """Stub for test_read_file_dne."""

