"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the gardena_bluetooth integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.gardena_bluetooth.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("gardena_bluetooth")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_delayed_product() -> None:
    """Stub for test_setup_delayed_product."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_retry() -> None:
    """Stub for test_setup_retry."""

