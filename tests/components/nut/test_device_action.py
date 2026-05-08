"""Tryke skip-stubs for nut test_device_action (port deferred)."""
from tryke import test

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def get_all_actions_for_specified_user() -> None:
    """Stub for test_get_all_actions_for_specified_user (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def no_actions_for_anonymous_user() -> None:
    """Stub for test_no_actions_for_anonymous_user (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def no_actions_device_not_found() -> None:
    """Stub for test_no_actions_device_not_found (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def no_actions_device_invalid() -> None:
    """Stub for test_no_actions_device_invalid (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def list_commands_exception() -> None:
    """Stub for test_list_commands_exception (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def unsupported_command() -> None:
    """Stub for test_unsupported_command (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def action() -> None:
    """Stub for test_action (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def run_command_exception() -> None:
    """Stub for test_run_command_exception (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def action_exception_device_not_found() -> None:
    """Stub for test_action_exception_device_not_found (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def action_exception_invalid_config() -> None:
    """Stub for test_action_exception_invalid_config (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def action_exception_device_invalid() -> None:
    """Stub for test_action_exception_device_invalid (port deferred)."""


