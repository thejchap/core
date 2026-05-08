"""Tryke skip-stubs for powerwall switch tests.

Original tests use Powerwall API mocks; full port deferred.
"""

from tryke import test

@test.skip("Powerwall API mocks")
async def entity_registry() -> None:
    """Test powerwall off-grid switch device."""

@test.skip("Powerwall API mocks")
async def initial() -> None:
    """Test initial grid status without off grid switch selected."""

@test.skip("Powerwall API mocks")
async def on() -> None:
    """Test state once offgrid switch has been turned on."""

@test.skip("Powerwall API mocks")
async def off() -> None:
    """Test state once offgrid switch has been turned off."""

@test.skip("Powerwall API mocks")
async def exception_on_powerwall_error() -> None:
    """Ensure that an exception in the tesla_powerwall library causes a HomeAssistantError."""
