"""Tryke skip-stubs for octoprint test_button (port deferred)."""
from tryke import test

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def restart_octoprint() -> None:
    """Stub for test_restart_octoprint (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def pause_job() -> None:
    """Stub for test_pause_job (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def resume_job() -> None:
    """Stub for test_resume_job (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def stop_job() -> None:
    """Stub for test_stop_job (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def shutdown_system() -> None:
    """Stub for test_shutdown_system (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def reboot_system() -> None:
    """Stub for test_reboot_system (port deferred)."""


