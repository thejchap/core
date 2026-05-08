"""Tryke skip stub for test_notify.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_message_without_target_logs_error() -> None:
    """Stub for test_send_message_without_target_logs_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def get_file_from_url() -> None:
    """Stub for test_get_file_from_url."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def get_file_from_url_not_on_allowlist() -> None:
    """Stub for test_get_file_from_url_not_on_allowlist."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def get_file_from_url_with_large_attachment() -> None:
    """Stub for test_get_file_from_url_with_large_attachment."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def get_file_from_url_with_large_attachment_no_header() -> None:
    """Stub for test_get_file_from_url_with_large_attachment_no_header."""

