"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_exceptions() -> None:
    """Stub for test_config_exceptions."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def connect_websocket_error() -> None:
    """Stub for test_connect_websocket_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def connect_request_limit_reached_error() -> None:
    """Stub for test_connect_request_limit_reached_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def start_charging_action() -> None:
    """Stub for test_start_charging_action."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def start_charging_action_without_card() -> None:
    """Stub for test_start_charging_action_without_card."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def start_charging_action_errors() -> None:
    """Stub for test_start_charging_action_errors."""

