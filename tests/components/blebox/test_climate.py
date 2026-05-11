"""Tryke skip stub for test_climate.py."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.blebox.climate module imports cleanly."""
    from homeassistant.components.blebox import climate  # noqa: PLC0415
    expect(climate).not_.to_be(None)


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def init() -> None:
    """Stub for test_init."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update() -> None:
    """Stub for test_update."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def on_when_below_desired() -> None:
    """Stub for test_on_when_below_desired."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def on_when_above_desired() -> None:
    """Stub for test_on_when_above_desired."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def off() -> None:
    """Stub for test_off."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def set_thermo() -> None:
    """Stub for test_set_thermo."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_failure() -> None:
    """Stub for test_update_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def reding_hvac_actions() -> None:
    """Stub for test_reding_hvac_actions."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def thermo_off() -> None:
    """Stub for test_thermo_off."""

