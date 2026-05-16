"""Test to check for circular imports in core components."""

from tryke import test


@test.skip("subprocess import-cycle check incompatible with tryke worker model")
async def circular_imports(component: str = "") -> None:
    """Check that components can be imported without circular imports."""
