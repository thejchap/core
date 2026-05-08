"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def file_value_entry_setup() -> None:
    """Stub for test_file_value_entry_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def file_value_template() -> None:
    """Stub for test_file_value_template."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def file_empty() -> None:
    """Stub for test_file_empty."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def file_path_invalid() -> None:
    """Stub for test_file_path_invalid."""

