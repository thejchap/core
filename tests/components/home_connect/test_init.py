"""Tryke skip-stubs for test_init.py - indirect parametrize unsupported."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the home_connect integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.home_connect.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("home_connect")


@test.skip("indirect parametrize unsupported")
async def entry_setup() -> None:
    """Stub for test_entry_setup."""

@test.skip("indirect parametrize unsupported")
async def token_refresh_success() -> None:
    """Stub for test_token_refresh_success."""

@test.skip("indirect parametrize unsupported")
async def setup_implementation_unavailable() -> None:
    """Stub for test_setup_implementation_unavailable."""

@test.skip("indirect parametrize unsupported")
async def token_refresh_error() -> None:
    """Stub for test_token_refresh_error."""

@test.skip("indirect parametrize unsupported")
async def client_error() -> None:
    """Stub for test_client_error."""

@test.skip("indirect parametrize unsupported")
async def client_rate_limit_error() -> None:
    """Stub for test_client_rate_limit_error."""

@test.skip("indirect parametrize unsupported")
async def required_program_or_at_least_an_option() -> None:
    """Stub for test_required_program_or_at_least_an_option."""

@test.skip("indirect parametrize unsupported")
async def entity_migration() -> None:
    """Stub for test_entity_migration."""

@test.skip("indirect parametrize unsupported")
async def bsh_key_transformations() -> None:
    """Stub for test_bsh_key_transformations."""

@test.skip("indirect parametrize unsupported")
async def config_entry_unique_id_migration() -> None:
    """Stub for test_config_entry_unique_id_migration."""
