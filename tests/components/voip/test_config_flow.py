"""Test VoIP config flow."""

from tryke import test


@test.skip("opuslib not installed; SIP fixtures")
async def form_user() -> None:
    """Skipped pending fixture port."""

@test.skip("opuslib not installed; SIP fixtures")
async def single_instance() -> None:
    """Skipped pending fixture port."""

@test.skip("opuslib not installed; SIP fixtures")
async def options_flow() -> None:
    """Skipped pending fixture port."""
