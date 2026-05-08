"""Test VoIP config flow."""

from tryke import test


@test.skip("system libopus.so not installed; voip_utils import fails")
async def form_user() -> None:
    """Skipped: requires Opus C library at the system level."""


@test.skip("system libopus.so not installed; voip_utils import fails")
async def single_instance() -> None:
    """Skipped: requires Opus C library at the system level."""


@test.skip("system libopus.so not installed; voip_utils import fails")
async def options_flow() -> None:
    """Skipped: requires Opus C library at the system level."""
