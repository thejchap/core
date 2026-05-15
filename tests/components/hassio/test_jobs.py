"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def job_manager_setup() -> None:
    """Stub for test_job_manager_setup (port deferred)."""

@test.skip("pending tryke port")
async def disconnect_on_config_entry_reload() -> None:
    """Stub for test_disconnect_on_config_entry_reload (port deferred)."""

@test.skip("pending tryke port")
async def job_manager_ws_updates() -> None:
    """Stub for test_job_manager_ws_updates (port deferred)."""

@test.skip("pending tryke port")
async def job_manager_reload_on_supervisor_restart() -> None:
    """Stub for test_job_manager_reload_on_supervisor_restart (port deferred)."""
