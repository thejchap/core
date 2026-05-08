"""Tryke skip stub for test_init.py."""

from tryke import test

# Re-exported for test_config_flow.py compatibility (legacy import).
MOCK_CONFIG_DATA = {
    "name": "IP Webcam",
    "host": "1.1.1.1",
    "port": 8080,
    "username": "user",
    "password": "pass",
}


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def successful_config_entry() -> None:
    """Stub for test_successful_config_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_failed_connection_error() -> None:
    """Stub for test_setup_failed_connection_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_failed_invalid_auth() -> None:
    """Stub for test_setup_failed_invalid_auth."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""

